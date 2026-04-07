"""读者端：仅浏览「已发布」作品，句段翻译与反馈（RAG 使用作品发布者导入的术语/平行句）。"""
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

bp = Blueprint("catalog", __name__, url_prefix="/api/catalog")


def _uid():
    return int(get_jwt_identity())


def _log_ai(user_id, action, engine):
    db.session.add(
        AIUsageLog(user_id=user_id, action_type=action, engine=engine)
    )


def _get_published_work(work_id):
    w = LiteraryWork.query.filter_by(id=work_id, status="published").first()
    return w


def _guichuideng_demo_th_by_index(idx: int) -> str:
    demo = [
        "ตราบใดที่ยังมีชีวิตอยู่, โอกาสทำเงินก็ยังมีแน่นอน. ในส่วนของสองสิ่งสำคัญที่สุดนั้น, กระจกโบราณชิ้นนั้นเป็นของดีจริงๆ, แต่จะได้หรือเสียไปก็ไม่ใช่เรื่องใหญ่โตอะไร. แค่จำลักษณะไว้ให้ดี, แล้วค่อยกลับไปสอบถามที่ปักกิ่ง, ในอนาคตอาจจะหาเจออีกชิ้นก็เป็นได้.",
        "ส่วนหีบหินโบราณสีแดงเข้มนั้น, ฉันก็คิดขึ้นได้ทันทีว่า, ข้างในต้องเป็นสิ่งที่เรียกว่า 'สมุดแห่งกระดูกนาค', แน่นอน ซึ่งก็เหมือนกับที่ตระกูลของ Shirley Yang สืบทอดกันมา, ล้วนบันทึกเรื่อง 'นกฟีนิกสร้องบนเขาชี' ด้วยอักษรโบราณ. ไม่ว่าจะเป็นชิ้นที่พบในเมืองเฮย์สุ่ยแห่งซีเซี่ย, หรือชิ้นที่ขุดพบที่อำเภอกู่เถียนแล้วหายไปเพราะเครื่องบินขนส่งตก, ก็น่าจะมีเนื้อหาเดียวกันทั้งหมด.",
        "นอกจากนี้ เมื่อนึกถึง \"สมุดแห่งกระดูกนาค\" ที่ตระกูลของ Shirley Yang สืบทอดมา, ซึ่งถูกพบในห้องลับสุดลึกของถ้ำสมบัติในสุสานว่างเปล่าแห่งเมืองเฮย์สุ่ย, ส่วนที่ขุดพบที่อำเภอกู่เถียนก็ไม่ได้พบในสุสานเช่นกัน,  ดูเหมือนว่า \"สมุดแห่งกระดูกนาค\" ประเภทนี้ไม่เหมาะจะใช้เป็นเครื่องสังเวยในสุสาน, นี่อาจเป็นผลจากค่านิยมและแนวคิดทางจักรวาลวิทยาของคนสมัยโบราณ.",
        "\"สมุดแห่งกระดูกนาค\"โดยประวัติศาสตร์แล้วเป็นสมบัติล้ำค่าที่ถูกเก็บรักษาอย่างดีในราชสำนัก,\n\nหากเนื้อหาภายในเป็นเพียงตำนาน \"นกฟีนิกสร้องบนเขาชี\" อย่างเดียว ก็ไม่สมควรที่จะถูกปกปิดอย่างแน่นหนาขนาดนี้.\n\nในอักษรลับของสมุดโบราณเล่มนี้ ต้องมีความลับอื่นซ่อนอยู่อีก,\n\nซึ่งน่าจะเป็นบันทึกเกี่ยวกับ ที่มาของ \"ไข่มุกซั่วเฉิน\" หรือไม่ก็เป็น วิถีการเป็นอมตะ,\n\nแต่วิธีการถอดรหัสนั้นต้องมีวิธีอื่นที่แตกต่างไป แน่นอน.",
    ]
    if 0 <= idx < len(demo):
        return demo[idx]
    return ""


@bp.post("/seed-demo-guichuideng")
@jwt_required(optional=True)
def seed_demo_guichuideng():
    """
    为当前登录用户创建《鬼吹灯》翻译演示（节选 + 泰文预置译文）。

    - 作品将标记为 published，便于读者端直接进入阅读器体验
    - 若已存在同名演示作品（同一 user_id + title），则直接返回现有 work_id
    """
    try:
        user_id = _uid()
    except Exception:
        return jsonify({"message": "请先登录后再初始化演示内容"}), 401
    title = "《鬼吹灯 / ผีเป่าโคมไฟ》翻译演示"
    existed = LiteraryWork.query.filter_by(user_id=user_id, title=title).first()

    # 来自用户截图的节选（按段落拆分）
    zh_paras = [
        "只要性命还在，咱们就有的是机会赚钱，当然那两件最重要的东西，其中的古镜绝对是个好东西，但得之失之也无关大局，记住了样子，回北京打听打听，以后再找一面，也不是没有可能。",
        "还有那只殷红的玉石古函，我突然想到，里面装的一定是那所谓的龙骨天书，也就是与 Shirley 杨家里传下来的那块相同，都是用天书记载的“凤鸣岐山”，在西夏黑水城找到的那块，还有在古田县出土后，因运输机坠毁而消失的龙骨，应该都是一样的内容。",
        "而且联想到 Shirley杨家传的龙骨天书，是在黑水城空墓藏宝洞深处的暗室里，古田县出土的，也不是什么墓穴里找到的，看来这种龙骨天书，不能够用来做墓主的陪葬品，这可能是受古代人价值观、宇宙观的影响。",
        "龙骨天书历来是大内珍异秘藏，里面的内容如果只是“凤鸣歧山”地传说，那绝不应该藏得如此隐秘，这天书的秘文中，一定另有机密之处，极有可能是记载着“電尘珠”的出处来历，亦或是长生化仙之道，但解读的方式一定另有他法",
    ]

    # 来自用户截图的泰文译文（对齐上面 4 段）
    th_paras = [
        "ตราบใดที่ยังมีชีวิตอยู่, โอกาสทำเงินก็ยังมีแน่นอน. ในส่วนของสองสิ่งสำคัญที่สุดนั้น, กระจกโบราณชิ้นนั้นเป็นของดีจริงๆ, แต่จะได้หรือเสียไปก็ไม่ใช่เรื่องใหญ่โตอะไร. แค่จำลักษณะไว้ให้ดี, แล้วค่อยกลับไปสอบถามที่ปักกิ่ง, ในอนาคตอาจจะหาเจออีกชิ้นก็เป็นได้.",
        "ส่วนหีบหินโบราณสีแดงเข้มนั้น, ฉันก็คิดขึ้นได้ทันทีว่า, ข้างในต้องเป็นสิ่งที่เรียกว่า 'สมุดแห่งกระดูกนาค', แน่นอน ซึ่งก็เหมือนกับที่ตระกูลของ Shirley Yang สืบทอดกันมา, ล้วนบันทึกเรื่อง 'นกฟีนิกสร้องบนเขาชี' ด้วยอักษรโบราณ. ไม่ว่าจะเป็นชิ้นที่พบในเมืองเฮย์สุ่ยแห่งซีเซี่ย, หรือชิ้นที่ขุดพบที่อำเภอกู่เถียนแล้วหายไปเพราะเครื่องบินขนส่งตก, ก็น่าจะมีเนื้อหาเดียวกันทั้งหมด.",
        "นอกจากนี้ เมื่อนึกถึง \"สมุดแห่งกระดูกนาค\" ที่ตระกูลของ Shirley Yang สืบทอดมา, ซึ่งถูกพบในห้องลับสุดลึกของถ้ำสมบัติในสุสานว่างเปล่าแห่งเมืองเฮย์สุ่ย, ส่วนที่ขุดพบที่อำเภอกู่เถียนก็ไม่ได้พบในสุสานเช่นกัน,  ดูเหมือนว่า \"สมุดแห่งกระดูกนาค\" ประเภทนี้ไม่เหมาะจะใช้เป็นเครื่องสังเวยในสุสาน, นี่อาจเป็นผลจากค่านิยมและแนวคิดทางจักรวาลวิทยาของคนสมัยโบราณ.",
        "\"สมุดแห่งกระดูกนาค\"โดยประวัติศาสตร์แล้วเป็นสมบัติล้ำค่าที่ถูกเก็บรักษาอย่างดีในราชสำนัก,\n\nหากเนื้อหาภายในเป็นเพียงตำนาน \"นกฟีนิกสร้องบนเขาชี\" อย่างเดียว ก็ไม่สมควรที่จะถูกปกปิดอย่างแน่นหนาขนาดนี้.\n\nในอักษรลับของสมุดโบราณเล่มนี้ ต้องมีความลับอื่นซ่อนอยู่อีก,\n\nซึ่งน่าจะเป็นบันทึกเกี่ยวกับ ที่มาของ \"ไข่มุกซั่วเฉิน\" หรือไม่ก็เป็น วิถีการเป็นอมตะ,\n\nแต่วิธีการถอดรหัสนั้นต้องมีวิธีอื่นที่แตกต่างไป แน่นอน.",
    ]

    # 若已存在，则覆盖更新：清空旧章节/句段/译文后重建
    if existed:
        ch_ids = [c.id for c in Chapter.query.filter_by(work_id=existed.id).all()]
        if ch_ids:
            seg_ids = [
                s.id
                for s in ChapterSegment.query.filter(ChapterSegment.chapter_id.in_(ch_ids)).all()
            ]
            if seg_ids:
                WorkTranslation.query.filter(
                    WorkTranslation.chapter_segment_id.in_(seg_ids)
                ).delete(synchronize_session=False)
            ChapterSegment.query.filter(ChapterSegment.chapter_id.in_(ch_ids)).delete(
                synchronize_session=False
            )
            Chapter.query.filter(Chapter.id.in_(ch_ids)).delete(synchronize_session=False)
        existed.author_name = "天下霸唱（节选）"
        existed.genre = "悬疑"
        existed.src_lang = "zh"
        existed.summary = (
            "使用《鬼吹灯》节选做翻译演示：分段对照、预置泰文译文，可继续体验 AI 翻译与 RAG 依据。"
        )
        existed.status = "published"
        w = existed
    else:
        w = LiteraryWork(
            user_id=user_id,
            title=title,
            author_name="天下霸唱（节选）",
            genre="悬疑",
            src_lang="zh",
            summary="使用《鬼吹灯》节选做翻译演示：分段对照、预置泰文译文，可继续体验 AI 翻译与 RAG 依据。",
            status="published",
        )
        db.session.add(w)
        db.session.flush()

    ch = Chapter(work_id=w.id, title="节选 · 龙骨天书", chapter_index=1)
    db.session.add(ch)
    db.session.flush()

    for idx, content in enumerate(zh_paras):
        seg = ChapterSegment(chapter_id=ch.id, index_in_chapter=idx, content=content)
        db.session.add(seg)
        db.session.flush()
        # 预置泰文译文：human_polished 便于读者侧直接看到“成品译文”
        wt = WorkTranslation(
            chapter_segment_id=seg.id,
            user_id=user_id,
            target_lang="th",
            engine="demo_seed",
            translated_text=th_paras[idx] if idx < len(th_paras) else "",
            status="human_polished",
            is_selected=True,
        )
        db.session.add(wt)

    db.session.commit()
    return jsonify({"message": "已创建《鬼吹灯》翻译演示", "work_id": w.id, "chapter_id": ch.id})


@bp.get("/works")
@jwt_required()
def catalog_list():
    genre = request.args.get("genre")
    q = (request.args.get("q") or "").strip()
    query = LiteraryWork.query.filter_by(status="published")
    if genre:
        query = query.filter_by(genre=genre)
    if q:
        like = f"%{q}%"
        query = query.filter(LiteraryWork.title.like(like))
    rows = query.order_by(LiteraryWork.updated_at.desc()).all()
    # 一次性统计章节数，避免 N+1 查询
    work_ids = [r.id for r in rows]
    chapter_counts = {}
    if work_ids:
        counts = (
            db.session.query(Chapter.work_id, func.count(Chapter.id))
            .filter(Chapter.work_id.in_(work_ids))
            .group_by(Chapter.work_id)
            .all()
        )
        chapter_counts = {wid: cnt for wid, cnt in counts}
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
                    "chapter_count": chapter_counts.get(r.id, 0),
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            ]
        }
    )


@bp.get("/works/<int:work_id>")
@jwt_required()
def catalog_work(work_id):
    w = _get_published_work(work_id)
    if not w:
        return jsonify({"message": "作品不存在或未发布"}), 404
    ch_count = Chapter.query.filter_by(work_id=w.id).count()
    return jsonify(
        {
            "id": w.id,
            "title": w.title,
            "author_name": w.author_name,
            "genre": w.genre,
            "src_lang": w.src_lang,
            "summary": w.summary,
            "chapter_count": ch_count,
        }
    )


@bp.get("/works/<int:work_id>/chapters")
@jwt_required()
def catalog_chapters(work_id):
    if not _get_published_work(work_id):
        return jsonify({"message": "作品不存在或未发布"}), 404
    rows = Chapter.query.filter_by(work_id=work_id).order_by(Chapter.chapter_index.asc()).all()
    return jsonify(
        {
            "items": [
                {"id": r.id, "title": r.title, "chapter_index": r.chapter_index}
                for r in rows
            ]
        }
    )


@bp.get("/works/<int:work_id>/chapters/<int:chapter_id>/segments")
@jwt_required()
def catalog_segments(work_id, chapter_id):
    w = _get_published_work(work_id)
    if not w:
        return jsonify({"message": "作品不存在或未发布"}), 404
    ch = Chapter.query.filter_by(id=chapter_id, work_id=work_id).first()
    if not ch:
        return jsonify({"message": "章节不存在"}), 404
    reader_id = _uid()
    tgt = (request.args.get("target_lang") or "").strip()
    segs = (
        ChapterSegment.query.filter_by(chapter_id=chapter_id)
        .order_by(ChapterSegment.index_in_chapter.asc())
        .all()
    )
    # 读者端：优先显示“我自己的译文”，若没有，则回退显示作品创建者的预置译文（用于演示/样例）
    owner_id = w.user_id if w else None
    out = []
    for s in segs:
        content = s.content
        if "鬼吹灯" in (w.title or "") or "ผีเป่าโคมไฟ" in (w.title or ""):
            # 兼容旧数据：清理已确认不需要的残留文案
            if s.index_in_chapter == 0 and content.startswith("谓，"):
                content = content[2:]
            if s.index_in_chapter == 3:
                content = content.replace("不是孙教授那", "")
        trans = None
        if tgt:
            wt = (
                WorkTranslation.query.filter_by(
                    chapter_segment_id=s.id, user_id=reader_id, target_lang=tgt
                )
                .order_by(WorkTranslation.is_selected.desc(), WorkTranslation.id.desc())
                .first()
            )
            if not wt and owner_id:
                wt = (
                    WorkTranslation.query.filter_by(
                        chapter_segment_id=s.id, user_id=owner_id, target_lang=tgt
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
            elif tgt == "th" and ("鬼吹灯" in (w.title or "") or "ผีเป่าโคมไฟ" in (w.title or "")):
                # 兜底：即使数据库中演示译文被误删，也按段号回填初始泰文显示
                demo_text = _guichuideng_demo_th_by_index(s.index_in_chapter)
                if demo_text:
                    trans = {
                        "id": None,
                        "text": demo_text,
                        "status": "human_polished",
                        "engine": "demo_seed",
                    }
        out.append(
            {
                "id": s.id,
                "index_in_chapter": s.index_in_chapter,
                "content": content,
                "translation": trans,
            }
        )
    return jsonify({"items": out})


@bp.post("/segments/<int:segment_id>/translate")
@jwt_required()
def catalog_translate(segment_id):
    reader_id = _uid()
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
    if not w or w.status != "published":
        return jsonify({"message": "无权翻译该内容"}), 403
    owner_id = w.user_id
    src_lang = w.src_lang or "zh"
    g_lines = ""
    p_lines = ""
    if use_rag:
        g_lines = rag_context.glossary_hints(owner_id, seg.content, src_lang, target_lang)
        p_lines = rag_context.parallel_examples(owner_id, seg.content, src_lang, target_lang)
    out_text, engine = translate_literary(seg.content, src_lang, target_lang, g_lines, p_lines)
    wt = WorkTranslation(
        chapter_segment_id=seg.id,
        user_id=reader_id,
        target_lang=target_lang,
        engine=engine,
        translated_text=out_text,
        status="ai_draft",
        is_selected=True,
    )
    db.session.add(wt)
    _log_ai(reader_id, "translate_segment", engine)
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


@bp.post("/translations/<int:tid>/feedback")
@jwt_required()
def catalog_feedback(tid):
    reader_id = _uid()
    data = request.get_json() or {}
    wt = WorkTranslation.query.get(tid)
    if not wt:
        return jsonify({"message": "译文不存在"}), 404
    seg = ChapterSegment.query.get(wt.chapter_segment_id)
    ch = Chapter.query.get(seg.chapter_id)
    w = LiteraryWork.query.get(ch.work_id)
    if not w or w.status != "published":
        return jsonify({"message": "无权反馈"}), 403
    r = int(data.get("rating") or 0)
    if r < 1 or r > 5:
        return jsonify({"message": "rating 应为 1-5"}), 400
    fb = ReaderFeedback(
        user_id=reader_id,
        work_translation_id=tid,
        rating=r,
        comment=(data.get("comment") or "")[:1024] or None,
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({"message": "感谢反馈"}), 201


@bp.delete("/segments/<int:segment_id>/my-translation")
@jwt_required()
def delete_my_translation(segment_id):
    """删除当前读者在某句段上的 AI 草稿，恢复为初始演示译文。"""
    reader_id = _uid()
    target_lang = (request.args.get("target_lang") or "").strip()[:10]
    if not target_lang:
        return jsonify({"message": "target_lang 必填"}), 400
    seg = ChapterSegment.query.get(segment_id)
    if not seg:
        return jsonify({"message": "句段不存在"}), 404

    rows = WorkTranslation.query.filter_by(
        chapter_segment_id=segment_id,
        user_id=reader_id,
        target_lang=target_lang,
    ).all()
    # 只删除 AI 草稿，保留人工/演示初始译文
    ai_rows = [r for r in rows if (r.status or "") == "ai_draft"]
    if not ai_rows:
        return jsonify({"message": "无 AI 草稿可恢复"}), 200

    for r in ai_rows:
        db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "已恢复初始译文"})
