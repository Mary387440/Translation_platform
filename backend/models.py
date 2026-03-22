from datetime import datetime

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100))
    preferred_src_lang = db.Column(db.String(10))
    preferred_tgt_lang = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Dataset(db.Model):
    """数据集元数据：术语库 / 平行句语料 / 文档包。"""

    __tablename__ = "datasets"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # terminology | parallel | document
    kind = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    source_note = db.Column(db.String(512))
    # 可存 JSON 数组字符串或逗号分隔，如 ["ja","zh"] 或 ja,zh
    languages = db.Column(db.String(512))
    stats_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Doc(db.Model):
    __tablename__ = "docs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    dataset_id = db.Column(db.BigInteger, db.ForeignKey("datasets.id"), nullable=True)
    title = db.Column(db.String(255))
    original_name = db.Column(db.String(255))
    storage_path = db.Column(db.String(512))
    src_lang = db.Column(db.String(10))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class DocSegment(db.Model):
    __tablename__ = "doc_segments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    doc_id = db.Column(db.BigInteger, db.ForeignKey("docs.id"), nullable=False)
    index_in_doc = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    paragraph_no = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Translation(db.Model):
    __tablename__ = "translations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    doc_id = db.Column(db.BigInteger, db.ForeignKey("docs.id"), nullable=False)
    segment_id = db.Column(db.BigInteger, db.ForeignKey("doc_segments.id"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    target_lang = db.Column(db.String(10), nullable=False)
    engine = db.Column(db.String(50))
    translated_text = db.Column(db.Text, nullable=False)
    quality_score = db.Column(db.Numeric(3, 2))
    is_selected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class GlossaryEntry(db.Model):
    __tablename__ = "glossary_entries"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    dataset_id = db.Column(db.BigInteger, db.ForeignKey("datasets.id"), nullable=True)
    src_lang = db.Column(db.String(10), nullable=False)
    tgt_lang = db.Column(db.String(10), nullable=False)
    src_text = db.Column(db.String(512), nullable=False)
    tgt_text = db.Column(db.String(512), nullable=False)
    note = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ParallelPair(db.Model):
    """平行句对（导入的句级语料）。"""

    __tablename__ = "parallel_pairs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.BigInteger, db.ForeignKey("datasets.id"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    src_lang = db.Column(db.String(20), nullable=False)
    tgt_lang = db.Column(db.String(20), nullable=False)
    src_text = db.Column(db.Text, nullable=False)
    tgt_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    doc_id = db.Column(db.BigInteger, db.ForeignKey("docs.id"))
    segment_id = db.Column(db.BigInteger, db.ForeignKey("doc_segments.id"))
    translation_id = db.Column(db.BigInteger, db.ForeignKey("translations.id"))
    note = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AIUsageLog(db.Model):
    __tablename__ = "ai_usage_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    doc_id = db.Column(db.BigInteger, db.ForeignKey("docs.id"))
    segment_id = db.Column(db.BigInteger, db.ForeignKey("doc_segments.id"))
    action_type = db.Column(db.String(50))
    engine = db.Column(db.String(50))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

