"""网络文学书库、章节阅读、句段翻译（DeepSeek+RAG）、人工润色与反馈。"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from authz import admin_required
from sqlalchemy import func

from app import db
from models import (
    AIUsageLog,
    Chapter,
    ChapterSegment,
    LiteraryWork,
    ReaderFeedback,
    WorkTranslation,
)
from services.ai_translate import translate_literary
from services import rag_context

bp = Blueprint("works", __name__, url_prefix="/api/works")


def _uid():
    return int(get_jwt_identity())


def _log_ai(user_id, action, engine):
    row = AIUsageLog(
        user_id=user_id,
        action_type=action,
        engine=engine,
    )
    db.session.add(row)


@bp.get("")
@admin_required
def list_works():
    user_id = _uid()
    genre = request.args.get("genre")
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or "all"
    query = LiteraryWork.query.filter_by(user_id=user_id)
    if status != "all":
        query = query.filter_by(status=status)
    if genre:
        query = query.filter_by(genre=genre)
    if q:
        like = f"%{q}%"
        query = query.filter(LiteraryWork.title.like(like))
    rows = query.order_by(LiteraryWork.updated_at.desc()).all()
    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "author_name": r.author_name,
                    "genre": r.genre,
                    "src_lang": r.src_lang,
                    "summary": r.summary,
                    "status": r.status,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            ]
        }
    )


@bp.post("")
@admin_required
def create_work():
    user_id = _uid()
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"message": "标题必填"}), 400
    w = LiteraryWork(
        user_id=user_id,
        title=title,
        author_name=(data.get("author_name") or "").strip() or None,
        genre=(data.get("genre") or "其他").strip()[:32],
        src_lang=(data.get("src_lang") or "zh")[:10],
        summary=(data.get("summary") or "").strip() or None,
        status=(data.get("status") or "draft")[:20],
    )
    db.session.add(w)
    db.session.commit()
    return jsonify({"id": w.id, "message": "已创建"}), 201


@bp.get("/<int:work_id>")
@admin_required
def get_work(work_id):
    user_id = _uid()
    w = LiteraryWork.query.filter_by(id=work_id, user_id=user_id).first()
    if not w:
        return jsonify({"message": "作品不存在"}), 404
    ch_count = Chapter.query.filter_by(work_id=w.id).count()
    return jsonify(
        {
            "id": w.id,
            "title": w.title,
            "author_name": w.author_name,
            "genre": w.genre,
            "src_lang": w.src_lang,
            "summary": w.summary,
            "status": w.status,
            "chapter_count": ch_count,
        }
    )


@bp.get("/<int:work_id>/chapters")
@admin_required
def list_chapters(work_id):
    user_id = _uid()
    w = LiteraryWork.query.filter_by(id=work_id, user_id=user_id).first()
    if not w:
        return jsonify({"message": "作品不存在"}), 404
    rows = Chapter.query.filter_by(work_id=work_id).order_by(Chapter.chapter_index.asc()).all()
    return jsonify(
        {
            "items": [
                {"id": r.id, "title": r.title, "chapter_index": r.chapter_index}
                for r in rows
            ]
        }
    )


@bp.post("/<int:work_id>/chapters")
@admin_required
def add_chapter(work_id):
    user_id = _uid()
    w = LiteraryWork.query.filter_by(id=work_id, user_id=user_id).first()
    if not w:
        return jsonify({"message": "作品不存在"}), 404
    data = request.get_json() or {}
    raw = (data.get("text") or "").strip()
    if not raw:
        return jsonify({"message": "章节正文 text 必填"}), 400
    title = (data.get("title") or "正文").strip()[:255]
    max_idx = (
        db.session.query(func.max(Chapter.chapter_index))
        .filter(Chapter.work_id == work_id)
        .scalar()
    )
    next_idx = (max_idx or 0) + 1
    ch = Chapter(work_id=work_id, title=title, chapter_index=int(data.get("chapter_index") or next_idx))
    db.session.add(ch)
    db.session.flush()
    # 按空行分段
    blocks = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if len(blocks) == 1:
        blocks = [p.strip() for p in raw.split("\n") if p.strip()]
    for i, content in enumerate(blocks):
        db.session.add(
            ChapterSegment(chapter_id=ch.id, index_in_chapter=i, content=content)
        )
    w.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"chapter_id": ch.id, "segments": len(blocks)}), 201


@bp.get("/<int:work_id>/chapters/<int:chapter_id>/segments")
@admin_required
def list_segments(work_id, chapter_id):
    user_id = _uid()
    w = LiteraryWork.query.filter_by(id=work_id, user_id=user_id).first()
    if not w:
        return jsonify({"message": "作品不存在"}), 404
    ch = Chapter.query.filter_by(id=chapter_id, work_id=work_id).first()
    if not ch:
        return jsonify({"message": "章节不存在"}), 404
    tgt = (request.args.get("target_lang") or "").strip()
    segs = (
        ChapterSegment.query.filter_by(chapter_id=chapter_id)
        .order_by(ChapterSegment.index_in_chapter.asc())
        .all()
    )
    out = []
    for s in segs:
        trans = None
        if tgt:
            wt = (
                WorkTranslation.query.filter_by(
                    chapter_segment_id=s.id, user_id=user_id, target_lang=tgt
                )
                .order_by(WorkTranslation.is_selected.desc(), WorkTranslation.id.desc())
                .first()
            )
            if wt:
                trans = {
                    "id": wt.id,
                    "text": wt.translated_text,
                    "status": wt.status,
                    "engine": wt.engine,
                }
        out.append(
            {
                "id": s.id,
                "index_in_chapter": s.index_in_chapter,
                "content": s.content,
                "translation": trans,
            }
        )
    return jsonify({"items": out})


@bp.post("/segments/<int:segment_id>/translate")
@admin_required
def translate_segment(segment_id):
    user_id = _uid()
    data = request.get_json() or {}
    target_lang = (data.get("target_lang") or "").strip()[:10]
    use_rag = data.get("use_rag", True)
    if not target_lang:
        return jsonify({"message": "target_lang 必填"}), 400
    seg = ChapterSegment.query.get(segment_id)
    if not seg:
        return jsonify({"message": "句段不存在"}), 404
    ch = Chapter.query.get(seg.chapter_id)
    w = LiteraryWork.query.get(ch.work_id)
    if w.user_id != user_id:
        return jsonify({"message": "无权操作"}), 403
    src_lang = w.src_lang or "zh"
    g_lines = ""
    p_lines = ""
    if use_rag:
        g_lines = rag_context.glossary_hints(user_id, seg.content, src_lang, target_lang)
        p_lines = rag_context.parallel_examples(user_id, seg.content, src_lang, target_lang)
    out_text, engine = translate_literary(seg.content, src_lang, target_lang, g_lines, p_lines)
    wt = WorkTranslation(
        chapter_segment_id=seg.id,
        user_id=user_id,
        target_lang=target_lang,
        engine=engine,
        translated_text=out_text,
        status="ai_draft",
        is_selected=True,
    )
    db.session.add(wt)
    _log_ai(user_id, "translate_segment", engine)
    db.session.commit()
    # 为前端展示翻译依据：术语命中 + 平行句参考（避免超长，这里做截断）
    return jsonify(
        {
            "translation_id": wt.id,
            "translated_text": out_text,
            "engine": engine,
            "status": wt.status,
            "rag": {
                "glossary_block": (g_lines or "")[:4000],
                "parallel_block": (p_lines or "")[:4000],
            }
            if use_rag
            else {"glossary_block": "", "parallel_block": ""},
        }
    )


@bp.put("/translations/<int:tid>/polish")
@admin_required
def polish_translation(tid):
    user_id = _uid()
    data = request.get_json() or {}
    text = (data.get("translated_text") or "").strip()
    if not text:
        return jsonify({"message": "translated_text 必填"}), 400
    wt = WorkTranslation.query.filter_by(id=tid, user_id=user_id).first()
    if not wt:
        return jsonify({"message": "译文不存在"}), 404
    wt.translated_text = text
    wt.status = "human_polished"
    db.session.commit()
    return jsonify({"message": "已保存润色", "id": wt.id})


@bp.post("/translations/<int:tid>/feedback")
@admin_required
def feedback(tid):
    user_id = _uid()
    data = request.get_json() or {}
    wt = WorkTranslation.query.filter_by(id=tid).first()
    if not wt:
        return jsonify({"message": "译文不存在"}), 404
    r = int(data.get("rating") or 0)
    if r < 1 or r > 5:
        return jsonify({"message": "rating 应为 1-5"}), 400
    fb = ReaderFeedback(
        user_id=user_id,
        work_translation_id=tid,
        rating=r,
        comment=(data.get("comment") or "")[:1024] or None,
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({"message": "感谢反馈"}), 201


@bp.post("/<int:work_id>/seed-demo")
@admin_required
def seed_demo(work_id):
    """为指定作品写入示例章节（若无章节）。"""
    user_id = _uid()
    w = LiteraryWork.query.filter_by(id=work_id, user_id=user_id).first()
    if not w:
        return jsonify({"message": "作品不存在"}), 404
    if Chapter.query.filter_by(work_id=work_id).first():
        return jsonify({"message": "已有章节，跳过"}), 200
    text = (
        "夜色如墨，远处的灯火像散落的星子。\n\n"
        "他想起故乡的桥，想起那句未说出口的话。\n\n"
        "风从海上吹来，带着咸涩与自由的味道。"
    )
    ch = Chapter(work_id=work_id, title="第一章 风起", chapter_index=1)
    db.session.add(ch)
    db.session.flush()
    for i, content in enumerate([p.strip() for p in text.split("\n\n") if p.strip()]):
        db.session.add(ChapterSegment(chapter_id=ch.id, index_in_chapter=i, content=content))
    w.status = "published"
    w.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"chapter_id": ch.id, "message": "已写入示例章节"})


@bp.post("/seed-classics")
@admin_required
def seed_classics():
    """
    为当前管理员账号创建一批“经典文学可阅读示例”（短摘录）。
    返回创建出来的作品列表，用于读者端书架展示。
    """
    user_id = _uid()
    data = request.get_json() or {}
    count = int(data.get("count") or 4)
    if count < 1:
        count = 1
    if count > 6:
        count = 6

    classics = [
        {
            "title": "《论语》·学而篇（节选）",
            "author_name": "孔子及弟子",
            "genre": "历史",
            "summary": "孔子语录短句节选，可直接用于对照阅读与翻译。",
            "chapter_title": "第一章 学而",
            "src_lang": "zh",
            "paras": [
                "子曰：学而时习之，不亦说乎？",
                "有朋自远方来，不亦乐乎？",
                "人不知而不愠，不亦君子乎？",
                "为政以德，譬如北辰，居其所而众星共之。",
            ],
        },
        {
            "title": "《孟子》·梁惠王上（节选）",
            "author_name": "孟子",
            "genre": "历史",
            "summary": "关于仁政与民心的对话节选，适合句段翻译体验。",
            "chapter_title": "第一章 梁惠王上",
            "src_lang": "zh",
            "paras": [
                "梁惠王曰：寡人之于国也，尽心焉耳矣。",
                "河内凶，则移其民于河东；河东凶，亦然。",
                "民之为道也，有恒产者有恒心，无恒产者无恒心。",
            ],
        },
        {
            "title": "《道德经》·第一章（节选）",
            "author_name": "老子",
            "genre": "其他",
            "summary": "道与德的开篇短句，适合作为翻译与 RAG 对照。",
            "chapter_title": "第一章 道可道",
            "src_lang": "zh",
            "paras": [
                "道可道，非常道；名可名，非常名。",
                "无名天地之始；有名万物之母。",
                "故常无欲，以观其妙；常有欲，以观其徼。",
            ],
        },
        {
            "title": "《庄子》·逍遥游（节选）",
            "author_name": "庄子",
            "genre": "其他",
            "summary": "关于逍遥与志趣的寓言节选，供读者进行 AI 翻译体验。",
            "chapter_title": "第一章 逍遥游",
            "src_lang": "zh",
            "paras": [
                "北冥有鱼，其名为鲲；鲲之大，不知其几千里也。",
                "化而为鸟，其名为鹏；鹏之背，不知其几千里也。",
                "怒而飞，其翼若垂天之云。",
            ],
        },
        {
            "title": "《红楼梦》·开篇（节选）",
            "author_name": "曹雪芹",
            "genre": "言情",
            "summary": "小说开篇叙述节选，用于展示完整阅读流程。",
            "chapter_title": "第一章 甫一开卷",
            "src_lang": "zh",
            "paras": [
                "甫一开卷，便知是人间富贵，未必尽如尘世。",
                "假作真时真亦假，无为有处有还无。",
                "好一似食尽鸟投林，落了片白茫茫大地真干净！",
            ],
        },
        {
            "title": "《史记》·太史公自序（节选）",
            "author_name": "司马迁",
            "genre": "历史",
            "summary": "史论与叙述的短句节选，用于对照翻译。",
            "chapter_title": "第一章 自序",
            "src_lang": "zh",
            "paras": [
                "究天人之际，通古今之变，成一家之言。",
                "亦欲论列其世，明其所以然。",
                "发愤著书，述往思来。",
            ],
        },
    ]

    created = []
    for item in classics[:count]:
        w = LiteraryWork(
            user_id=user_id,
            title=item["title"],
            author_name=item.get("author_name"),
            genre=item.get("genre", "其他")[:32],
            src_lang=(item.get("src_lang") or "zh")[:10],
            summary=item.get("summary"),
            status="published",
        )
        db.session.add(w)
        db.session.flush()

        ch = Chapter(
            work_id=w.id,
            title=item.get("chapter_title") or "第一章",
            chapter_index=1,
        )
        db.session.add(ch)
        db.session.flush()

        for idx, content in enumerate([p.strip() for p in item["paras"] if (p or "").strip()]):
            db.session.add(
                ChapterSegment(
                    chapter_id=ch.id,
                    index_in_chapter=idx,
                    content=content,
                )
            )

        created.append({"work_id": w.id, "title": w.title})

    db.session.commit()
    return jsonify({"message": "已创建经典作品", "created": created})
