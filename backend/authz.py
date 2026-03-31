"""权限：管理员 / 读者。"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import User


def admin_required(fn):
    """仅管理员：JWT 已登录且 user.role == admin。"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        role = getattr(user, "role", None) or "reader"
        if not user or role != "admin":
            return jsonify({"message": "需要管理员权限"}), 403
        return fn(*args, **kwargs)

    return wrapper
