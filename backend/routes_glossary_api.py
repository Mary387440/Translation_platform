"""术语库列表与检索（阅读/翻译时调用）。"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import GlossaryEntry

bp = Blueprint("glossary_api", __name__, url_prefix="/api/glossary")


def _uid():
    return int(get_jwt_identity())


@bp.get("/entries")
@jwt_required()
def list_entries():
    user_id = _uid()
    q = (request.args.get("q") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per = min(int(request.args.get("per_page", 20)), 100)
    query = GlossaryEntry.query.filter_by(user_id=user_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (GlossaryEntry.src_text.like(like)) | (GlossaryEntry.tgt_text.like(like))
        )
    total = query.count()
    rows = (
        query.order_by(GlossaryEntry.id.desc())
        .offset((page - 1) * per)
        .limit(per)
        .all()
    )
    return jsonify(
        {
            "total": total,
            "page": page,
            "per_page": per,
            "items": [
                {
                    "id": r.id,
                    "src_lang": r.src_lang,
                    "tgt_lang": r.tgt_lang,
                    "src_text": r.src_text,
                    "tgt_text": r.tgt_text,
                    "note": r.note,
                }
                for r in rows
            ],
        }
    )
