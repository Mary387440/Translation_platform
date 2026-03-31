"""控制台汇总（对齐计划书中的运营数据看板占位）。"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from authz import admin_required
from app import db
from models import AIUsageLog, Doc, GlossaryEntry, LiteraryWork

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _uid():
    return int(get_jwt_identity())


@bp.get("/summary")
@admin_required
def summary():
    user_id = _uid()
    since = datetime.utcnow() - timedelta(days=7)
    works = LiteraryWork.query.filter_by(user_id=user_id).count()
    docs = Doc.query.filter_by(user_id=user_id).count()
    terms = GlossaryEntry.query.filter_by(user_id=user_id).count()
    ai_calls = (
        AIUsageLog.query.filter(
            AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since
        ).count()
    )
    return jsonify(
        {
            "literary_works": works,
            "documents": docs,
            "glossary_entries": terms,
            "ai_calls_7d": ai_calls,
            "tagline": "SailoAI · 中国文学多语种出海",
        }
    )
