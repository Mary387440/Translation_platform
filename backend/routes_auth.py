from datetime import timedelta

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    nickname = data.get("nickname") or ""

    if not email or not password:
        return jsonify({"message": "邮箱和密码必填"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "邮箱已注册"}), 400

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        nickname=nickname or None,
        role="reader",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "邮箱已注册"}), 400
    except OperationalError as e:
        db.session.rollback()
        err = str(e.orig) if getattr(e, "orig", None) else str(e)
        if "role" in err.lower() or "unknown column" in err.lower():
            return jsonify(
                {
                    "message": "数据库表 users 缺少 role 字段。请在 backend 目录执行：flask db upgrade；"
                    "或手动执行：ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'reader';",
                }
            ), 500
        return jsonify({"message": f"数据库错误，请检查 MySQL 是否启动、连接配置是否正确。详情：{err}"}), 500

    return jsonify({"message": "注册成功"}), 201


@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "邮箱或密码错误"}), 401

    access_token = create_access_token(
        identity=str(user.id), expires_delta=timedelta(days=7)
    )
    return jsonify(
        {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "role": getattr(user, "role", None) or "reader",
            },
        }
    )


@bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "role": getattr(user, "role", None) or "reader",
            "preferred_src_lang": user.preferred_src_lang,
            "preferred_tgt_lang": user.preferred_tgt_lang,
        }
    )


@bp.put("/profile")
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    data = request.get_json() or {}
    if "nickname" in data:
        user.nickname = (data.get("nickname") or "").strip() or user.nickname
    if "preferred_src_lang" in data:
        user.preferred_src_lang = (data.get("preferred_src_lang") or "").strip()[:10] or None
    if "preferred_tgt_lang" in data:
        user.preferred_tgt_lang = (data.get("preferred_tgt_lang") or "").strip()[:10] or None
    db.session.commit()
    return jsonify({"message": "已更新"})

