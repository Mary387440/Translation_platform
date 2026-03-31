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
    if not _get_published_work(work_id):
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
    out = []
    for s in segs:
        trans = None
        if tgt:
            wt = (
                WorkTranslation.query.filter_by(
                    chapter_segment_id=s.id, user_id=reader_id, target_lang=tgt
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
