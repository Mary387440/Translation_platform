"""管理员评测任务：选择平行句数据集+指标，计算并返回分数。"""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from authz import admin_required
from app import db
from models import Dataset, EvaluationTask, ParallelPair
from services.ai_translate import translate_literary
from services.eval_metrics import evaluate_batch

bp = Blueprint("eval", __name__, url_prefix="/api/evals")

ALLOWED_METRICS = {"BLEU", "ROUGE", "METEOR"}


def _uid():
    return int(get_jwt_identity())


@bp.get("/metrics")
@admin_required
def metrics_options():
    return jsonify({"items": sorted(list(ALLOWED_METRICS))})


@bp.get("")
@admin_required
def list_tasks():
    uid = _uid()
    rows = EvaluationTask.query.filter_by(user_id=uid).order_by(EvaluationTask.id.desc()).all()
    items = []
    for r in rows:
        result = {}
        if r.result_json:
            try:
                result = json.loads(r.result_json)
            except Exception:
                result = {}
        items.append(
            {
                "id": r.id,
                "name": r.name,
                "dataset_id": r.dataset_id,
                "src_lang": r.src_lang,
                "tgt_lang": r.tgt_lang,
                "engine": r.engine,
                "metrics": r.metrics,
                "sample_size": r.sample_size,
                "status": r.status,
                "result": result,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return jsonify({"items": items})


@bp.post("")
@admin_required
def create_task():
    uid = _uid()
    data = request.get_json() or {}
    dataset_id = int(data.get("dataset_id") or 0)
    name = (data.get("name") or "评测任务").strip()
    src_lang = (data.get("src_lang") or "zh").strip()[:20]
    tgt_lang = (data.get("tgt_lang") or "en").strip()[:20]
    engine = (data.get("engine") or "mock").strip()[:50]
    sample_size = max(1, min(int(data.get("sample_size") or 30), 100))

    metrics = data.get("metrics") or ["BLEU", "ROUGE", "METEOR"]
    metrics = [str(m).upper() for m in metrics if str(m).upper() in ALLOWED_METRICS]
    if not metrics:
        return jsonify({"message": "请至少选择一个有效指标"}), 400

    ds = Dataset.query.filter_by(id=dataset_id, user_id=uid, kind="parallel").first()
    if not ds:
        return jsonify({"message": "仅支持你自己的平行句数据集"}), 400

    rows = (
        ParallelPair.query.filter_by(dataset_id=dataset_id, src_lang=src_lang, tgt_lang=tgt_lang)
        .order_by(ParallelPair.id.asc())
        .limit(sample_size)
        .all()
    )
    if not rows:
        return jsonify({"message": "该语种对没有平行句样本"}), 400

    preds = []
    refs = []
    used_engine = "mock"
    for row in rows:
        pred, e = translate_literary(row.src_text, src_lang, tgt_lang)
        used_engine = e
        preds.append(pred)
        refs.append(row.tgt_text)

    scores = evaluate_batch(preds, refs, metrics)
    result = {
        "scores": scores,
        "n_samples": len(rows),
        "engine": used_engine if engine == "deepseek" else "mock",
        "note": "当前 BLEU/ROUGE/METEOR 为轻量实现，便于平台内快速评测。",
    }

    task = EvaluationTask(
        user_id=uid,
        dataset_id=dataset_id,
        name=name,
        src_lang=src_lang,
        tgt_lang=tgt_lang,
        engine=result["engine"],
        metrics=",".join(metrics),
        sample_size=len(rows),
        status="done",
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({"id": task.id, "result": result}), 201

