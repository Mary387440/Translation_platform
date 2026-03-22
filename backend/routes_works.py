"""网络文学书库、章节阅读、句段翻译（DeepSeek+RAG）、人工润色与反馈。"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
    return jsonify(
        {
            "translation_id": wt.id,
            "translated_text": out_text,
            "engine": engine,
            "status": wt.status,
        }
    )


@bp.put("/translations/<int:tid>/polish")
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
