"""数据集：术语库 / 平行句 / 文档库 的元数据与导入接口。"""
import csv
import io
import json
import os
import zipfile

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app import db
from models import Dataset, Doc, GlossaryEntry, ParallelPair

bp = Blueprint("datasets", __name__, url_prefix="/api/datasets")

ALLOWED_DOC_EXT = {".txt", ".md", ".docx", ".pdf"}


def _uid():
    return int(get_jwt_identity())


def _dataset_or_404(dataset_id, user_id, expected_kind=None):
    ds = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if not ds:
        return None, (jsonify({"message": "数据集不存在"}), 404)
    if expected_kind and ds.kind != expected_kind:
        return None, (jsonify({"message": f"数据集类型应为 {expected_kind}"}), 400)
    return ds, None


def _update_stats(dataset, **kwargs):
    stats = {}
    if dataset.stats_json:
        try:
            stats = json.loads(dataset.stats_json)
        except json.JSONDecodeError:
            stats = {}
    stats.update(kwargs)
    dataset.stats_json = json.dumps(stats, ensure_ascii=False)


def _safe_extract_path(base_dir, member_name):
    """防止 ZIP 路径穿越。"""
    base_dir = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base_dir, member_name))
    if not target.startswith(base_dir + os.sep) and target != base_dir:
        raise ValueError("非法压缩包路径")
    return target


@bp.get("")
@jwt_required()
def list_datasets():
    user_id = _uid()
    rows = (
        Dataset.query.filter_by(user_id=user_id)
        .order_by(Dataset.created_at.desc())
        .all()
    )
    out = []
    for r in rows:
        stats = {}
        if r.stats_json:
            try:
                stats = json.loads(r.stats_json)
            except json.JSONDecodeError:
                pass
        out.append(
            {
                "id": r.id,
                "name": r.name,
                "kind": r.kind,
                "description": r.description,
                "source_note": r.source_note,
                "languages": r.languages,
                "stats": stats,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return jsonify({"items": out})


@bp.post("")
@jwt_required()
def create_dataset():
    user_id = _uid()
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    kind = (data.get("kind") or "").strip().lower()
    if not name:
        return jsonify({"message": "名称必填"}), 400
    if kind not in ("terminology", "parallel", "document"):
        return jsonify(
            {"message": "kind 须为 terminology | parallel | document"}
        ), 400

    ds = Dataset(
        user_id=user_id,
        name=name,
        kind=kind,
        description=(data.get("description") or "").strip() or None,
        source_note=(data.get("source_note") or "").strip() or None,
        languages=(data.get("languages") or "").strip() or None,
        stats_json=json.dumps({}, ensure_ascii=False),
    )
    db.session.add(ds)
    db.session.commit()
    return (
        jsonify(
            {
                "id": ds.id,
                "name": ds.name,
                "kind": ds.kind,
                "description": ds.description,
                "source_note": ds.source_note,
                "languages": ds.languages,
            }
        ),
        201,
    )


@bp.get("/<int:dataset_id>")
@jwt_required()
def get_dataset(dataset_id):
    user_id = _uid()
    ds, err = _dataset_or_404(dataset_id, user_id)
    if err:
        return err
    stats = {}
    if ds.stats_json:
        try:
            stats = json.loads(ds.stats_json)
        except json.JSONDecodeError:
            pass
    extra = {}
    if ds.kind == "parallel":
        extra["pair_count"] = ParallelPair.query.filter_by(dataset_id=ds.id).count()
    if ds.kind == "terminology":
        extra["entry_count"] = GlossaryEntry.query.filter_by(dataset_id=ds.id).count()
    if ds.kind == "document":
        extra["doc_count"] = Doc.query.filter_by(dataset_id=ds.id).count()
    return jsonify(
        {
            "id": ds.id,
            "name": ds.name,
            "kind": ds.kind,
            "description": ds.description,
            "source_note": ds.source_note,
            "languages": ds.languages,
            "stats": {**stats, **extra},
            "created_at": ds.created_at.isoformat() if ds.created_at else None,
        }
    )


def _normalize_term_row(row):
    """将一行 dict 映射到术语字段（支持常见别名）。"""
    lower = {k.lower().strip(): (v or "").strip() for k, v in row.items() if k}
    def g(*keys):
        for k in keys:
            if k in lower and lower[k]:
                return lower[k]
        return ""

    src_lang = g("src_lang", "source_lang", "源语言")
    tgt_lang = g("tgt_lang", "target_lang", "目标语言")
    src = g("src_term", "src_text", "source", "term_src", "源术语", "原文")
    tgt = g("tgt_term", "tgt_text", "target", "term_tgt", "目标术语", "译文")
    note = g("note", "备注", "domain", "领域")
    return src_lang, tgt_lang, src, tgt, note


@bp.post("/<int:dataset_id>/import/terminology")
@jwt_required()
def import_terminology(dataset_id):
    user_id = _uid()
    ds, err = _dataset_or_404(dataset_id, user_id, "terminology")
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"message": "请上传 file 字段（CSV/TSV）"}), 400
    f = request.files["file"]
    raw = f.read()
    if not raw:
        return jsonify({"message": "空文件"}), 400

    text = raw.decode("utf-8-sig")
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(text[:4096])
    except csv.Error:
        dialect = csv.excel_tab if "\t" in text.splitlines()[0] else csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return jsonify({"message": "无法解析表头"}), 400

    inserted = 0
    skipped = 0
    batch = []
    for row in reader:
        src_lang, tgt_lang, src, tgt, note = _normalize_term_row(row)
        if not (src_lang and tgt_lang and src and tgt):
            skipped += 1
            continue
        if len(src) > 512 or len(tgt) > 512:
            skipped += 1
            continue
        batch.append(
            GlossaryEntry(
                user_id=user_id,
                dataset_id=ds.id,
                src_lang=src_lang[:10],
                tgt_lang=tgt_lang[:10],
                src_text=src[:512],
                tgt_text=tgt[:512],
                note=(note[:512] if note else None),
            )
        )
        if len(batch) >= 500:
            db.session.add_all(batch)
            db.session.commit()
            inserted += len(batch)
            batch.clear()

    if batch:
        db.session.add_all(batch)
        db.session.commit()
        inserted += len(batch)

    total = GlossaryEntry.query.filter_by(dataset_id=ds.id).count()
    _update_stats(ds, terminology_imported_rows=inserted, terminology_total_entries=total)
    db.session.commit()

    return jsonify(
        {
            "message": "导入完成",
            "inserted": inserted,
            "skipped": skipped,
            "total_entries_in_dataset": total,
        }
    )


@bp.post("/<int:dataset_id>/import/parallel")
@jwt_required()
def import_parallel(dataset_id):
    user_id = _uid()
    ds, err = _dataset_or_404(dataset_id, user_id, "parallel")
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"message": "请上传 file 字段（TSV/CSV 或 .jsonl）"}), 400
    f = request.files["file"]
    raw = f.read()
    if not raw:
        return jsonify({"message": "空文件"}), 400

    filename = (f.filename or "").lower()
    inserted = 0
    skipped = 0
    batch = []

    if filename.endswith(".jsonl"):
        for line in raw.decode("utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            sl = (obj.get("src_lang") or "").strip()
            tl = (obj.get("tgt_lang") or "").strip()
            st = (obj.get("src_text") or "").strip()
            tt = (obj.get("tgt_text") or "").strip()
            if not (sl and tl and st and tt):
                skipped += 1
                continue
            batch.append(
                ParallelPair(
                    dataset_id=ds.id,
                    user_id=user_id,
                    src_lang=sl[:20],
                    tgt_lang=tl[:20],
                    src_text=st,
                    tgt_text=tt,
                )
            )
            if len(batch) >= 500:
                db.session.add_all(batch)
                db.session.commit()
                inserted += len(batch)
                batch.clear()
    else:
        text = raw.decode("utf-8-sig")
        try:
            dialect = csv.Sniffer().sniff(text[:4096])
        except csv.Error:
            dialect = csv.excel_tab if "\t" in text.splitlines()[0] else csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        if not reader.fieldnames:
            return jsonify({"message": "无法解析表头"}), 400
        for row in reader:
            lower = {k.lower().strip(): (v or "").strip() for k, v in row.items() if k}
            src_lang = lower.get("src_lang") or lower.get("source_lang") or ""
            tgt_lang = lower.get("tgt_lang") or lower.get("target_lang") or ""
            src_text = (
                lower.get("src_text")
                or lower.get("source")
                or lower.get("source_text")
                or ""
            )
            tgt_text = (
                lower.get("tgt_text")
                or lower.get("target")
                or lower.get("target_text")
                or ""
            )
            if not (src_lang and tgt_lang and src_text and tgt_text):
                skipped += 1
                continue
            batch.append(
                ParallelPair(
                    dataset_id=ds.id,
                    user_id=user_id,
                    src_lang=src_lang[:20],
                    tgt_lang=tgt_lang[:20],
                    src_text=src_text,
                    tgt_text=tgt_text,
                )
            )
            if len(batch) >= 500:
                db.session.add_all(batch)
                db.session.commit()
                inserted += len(batch)
                batch.clear()

    if batch:
        db.session.add_all(batch)
        db.session.commit()
        inserted += len(batch)

    total = ParallelPair.query.filter_by(dataset_id=ds.id).count()
    _update_stats(
        ds,
        parallel_imported_rows=inserted,
        parallel_total_pairs=total,
    )
    db.session.commit()

    return jsonify(
        {
            "message": "导入完成",
            "inserted": inserted,
            "skipped": skipped,
            "total_pairs_in_dataset": total,
        }
    )


@bp.post("/<int:dataset_id>/import/documents")
@jwt_required()
def import_documents(dataset_id):
    user_id = _uid()
    ds, err = _dataset_or_404(dataset_id, user_id, "document")
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"message": "请上传 file 字段（ZIP）"}), 400
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".zip"):
        return jsonify({"message": "请上传 .zip 压缩包"}), 400

    upload_root = current_app.config["UPLOAD_FOLDER"]
    extract_dir = os.path.join(upload_root, "datasets", str(user_id), str(ds.id))
    os.makedirs(extract_dir, exist_ok=True)

    data = f.read()
    if not data:
        return jsonify({"message": "空文件"}), 400

    created = 0
    skipped = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if name.startswith("__MACOSX/") or "/__MACOSX/" in name:
                skipped += 1
                continue
            base = os.path.basename(name)
            if base.startswith(".") or not base:
                skipped += 1
                continue
            ext = os.path.splitext(base)[1].lower()
            if ext not in ALLOWED_DOC_EXT:
                skipped += 1
                continue
            safe_base = secure_filename(base) or f"file{ext}"
            try:
                target_path = _safe_extract_path(extract_dir, safe_base)
            except ValueError:
                skipped += 1
                continue
            # 若重名则加序号
            if os.path.exists(target_path):
                stem, e = os.path.splitext(safe_base)
                i = 1
                while True:
                    cand = secure_filename(f"{stem}_{i}{e}") or f"file_{i}{e}"
                    target_path = os.path.join(extract_dir, cand)
                    if not os.path.exists(target_path):
                        break
                    i += 1
            with zf.open(info) as src, open(target_path, "wb") as out:
                out.write(src.read())

            rel = os.path.relpath(target_path, upload_root).replace("\\", "/")
            doc = Doc(
                user_id=user_id,
                dataset_id=ds.id,
                title=os.path.splitext(base)[0][:255],
                original_name=base[:255],
                storage_path=rel,
                status="uploaded",
            )
            db.session.add(doc)
            created += 1

    db.session.commit()
    total = Doc.query.filter_by(dataset_id=ds.id).count()
    _update_stats(
        ds,
        document_imported_files=created,
        document_total_docs=total,
    )
    db.session.commit()

    return jsonify(
        {
            "message": "解压并登记完成",
            "created_docs": created,
            "skipped": skipped,
            "total_docs_in_dataset": total,
        }
    )


@bp.get("/<int:dataset_id>/parallel-pairs")
@jwt_required()
def list_parallel_preview(dataset_id):
    """简易预览：前 N 条平行句。"""
    user_id = _uid()
    ds, err = _dataset_or_404(dataset_id, user_id, "parallel")
    if err:
        return err
    limit = min(int(request.args.get("limit", 20)), 100)
    rows = (
        ParallelPair.query.filter_by(dataset_id=ds.id)
        .order_by(ParallelPair.id.asc())
        .limit(limit)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "src_lang": r.src_lang,
                    "tgt_lang": r.tgt_lang,
                    "src_text": r.src_text,
                    "tgt_text": r.tgt_text,
                }
                for r in rows
            ]
        }
    )
