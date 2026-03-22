from datetime import timedelta

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

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
        nickname=nickname,
    )
    db.session.add(user)
    db.session.commit()

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
            "preferred_src_lang": user.preferred_src_lang,
            "preferred_tgt_lang": user.preferred_tgt_lang,
        }
    )

