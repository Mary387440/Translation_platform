from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app import db
from authz import admin_required
from models import DiscussionComment, DiscussionPost, User

bp = Blueprint("discussion", __name__, url_prefix="/api/discussions")

ALLOWED_CATEGORIES = {"翻译交流", "作品讨论", "技术问题", "公告"}


def _uid() -> int:
    return int(get_jwt_identity())


def _user_map(user_ids: list[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    rows = User.query.filter(User.id.in_(list(set(user_ids)))).all()
    return {u.id: (u.nickname or u.email or f"用户{u.id}") for u in rows}


@bp.get("")
@jwt_required()
def list_posts():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    include_hidden = request.args.get("include_hidden") == "1"
    query = DiscussionPost.query
    if not include_hidden:
        query = query.filter_by(status="published")
    if category:
        query = query.filter_by(category=category)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (DiscussionPost.title.like(like)) | (DiscussionPost.content.like(like))
        )
    rows = (
        query.order_by(DiscussionPost.is_pinned.desc(), DiscussionPost.updated_at.desc())
        .limit(300)
        .all()
    )
    post_ids = [r.id for r in rows]
    comment_counts = {}
    if post_ids:
        cc = (
            db.session.query(DiscussionComment.post_id, func.count(DiscussionComment.id))
            .filter(DiscussionComment.post_id.in_(post_ids))
            .group_by(DiscussionComment.post_id)
            .all()
        )
        comment_counts = {pid: cnt for pid, cnt in cc}
    names = _user_map([r.user_id for r in rows])
    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "summary": r.summary or (r.content[:120] + ("..." if len(r.content) > 120 else "")),
                    "category": r.category,
                    "author_name": names.get(r.user_id, f"用户{r.user_id}"),
                    "likes": r.likes,
                    "comment_count": comment_counts.get(r.id, 0),
                    "is_pinned": bool(r.is_pinned),
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        }
    )


@bp.post("")
@jwt_required()
def create_post():
    user_id = _uid()
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    category = (data.get("category") or "翻译交流").strip()
    if not title or not content:
        return jsonify({"message": "标题和内容必填"}), 400
    if category not in ALLOWED_CATEGORIES:
        return jsonify({"message": "不支持的分类"}), 400
    post = DiscussionPost(
        user_id=user_id,
        title=title[:255],
        content=content[:20000],
        summary=(data.get("summary") or "").strip()[:512] or None,
        category=category,
        status="published",
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"id": post.id, "message": "发布成功"}), 201


@bp.get("/<int:post_id>")
@jwt_required()
def get_post(post_id):
    post = DiscussionPost.query.get(post_id)
    if not post or post.status != "published":
        return jsonify({"message": "帖子不存在"}), 404
    name = _user_map([post.user_id]).get(post.user_id, f"用户{post.user_id}")
    comments = (
        DiscussionComment.query.filter_by(post_id=post_id)
        .order_by(DiscussionComment.created_at.asc())
        .all()
    )
    names = _user_map([c.user_id for c in comments] + [post.user_id])
    return jsonify(
        {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "author_name": name,
            "likes": post.likes,
            "is_pinned": bool(post.is_pinned),
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "author_name": names.get(c.user_id, f"用户{c.user_id}"),
                    "parent_id": c.parent_id,
                    "likes": c.likes,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in comments
            ],
        }
    )


@bp.post("/<int:post_id>/comments")
@jwt_required()
def add_comment(post_id):
    user_id = _uid()
    post = DiscussionPost.query.get(post_id)
    if not post or post.status != "published":
        return jsonify({"message": "帖子不存在"}), 404
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"message": "评论内容必填"}), 400
    parent_id = data.get("parent_id")
    comment = DiscussionComment(
        post_id=post_id,
        user_id=user_id,
        parent_id=int(parent_id) if parent_id else None,
        content=content[:2000],
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({"id": comment.id, "message": "评论成功"}), 201


@bp.post("/<int:post_id>/like")
@jwt_required()
def like_post(post_id):
    post = DiscussionPost.query.get(post_id)
    if not post:
        return jsonify({"message": "帖子不存在"}), 404
    post.likes = int(post.likes or 0) + 1
    db.session.commit()
    return jsonify({"likes": post.likes})


@bp.get("/admin/posts")
@admin_required
def admin_list_posts():
    rows = (
        DiscussionPost.query.order_by(DiscussionPost.is_pinned.desc(), DiscussionPost.updated_at.desc())
        .limit(400)
        .all()
    )
    names = _user_map([r.user_id for r in rows])
    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "author_name": names.get(r.user_id, f"用户{r.user_id}"),
                    "status": r.status,
                    "is_pinned": bool(r.is_pinned),
                    "likes": r.likes,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        }
    )


@bp.put("/admin/posts/<int:post_id>")
@admin_required
def admin_update_post(post_id):
    post = DiscussionPost.query.get(post_id)
    if not post:
        return jsonify({"message": "帖子不存在"}), 404
    data = request.get_json() or {}
    if "status" in data:
        status = (data.get("status") or "").strip()
        if status in {"published", "hidden"}:
            post.status = status
    if "is_pinned" in data:
        post.is_pinned = bool(data.get("is_pinned"))
    if "category" in data:
        cat = (data.get("category") or "").strip()
        if cat in ALLOWED_CATEGORIES:
            post.category = cat
    db.session.commit()
    return jsonify({"message": "更新成功"})


@bp.delete("/admin/posts/<int:post_id>")
@admin_required
def admin_delete_post(post_id):
    post = DiscussionPost.query.get(post_id)
    if not post:
        return jsonify({"message": "帖子不存在"}), 404
    DiscussionComment.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "已删除"})
