import sys

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from urllib.parse import urlparse

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# 兼容直接 `python app.py` 启动时的导入路径：
# 让 `from app import ...` 指向当前模块，避免二次导入触发循环依赖。
if __name__ == "__main__":
    sys.modules["app"] = sys.modules[__name__]


def create_app():
    app = Flask(__name__)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@localhost:3306/translation_platform",
    )
    # 启动时打印当前实际连接的数据库（不输出密码）
    try:
        u = urlparse(app.config["SQLALCHEMY_DATABASE_URI"])
        safe_netloc = (u.hostname or "") + (f":{u.port}" if u.port else "")
        print(f"[boot] DB={u.scheme}://{safe_netloc}{u.path}")
    except Exception:
        print("[boot] DB=<unparseable DATABASE_URL>")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB，ZIP 导入上限

    # 开发期：明确放行前端 dev server Origin，解决浏览器预检（OPTIONS）拦截
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        max_age=86400,
    )

    @app.after_request
    def _cors_fallback(resp):
        # 极少数环境下 Flask-CORS 可能未覆盖到预检/错误响应，这里兜底补齐关键头
        try:
            origin = os.getenv("CORS_ORIGIN_OVERRIDE") or (  # 允许你临时覆盖
                (resp.headers.get("Access-Control-Allow-Origin") or "")
            )
            # 如果 Flask-CORS 已处理，这里不重复覆盖
            if not resp.headers.get("Access-Control-Allow-Origin"):
                req_origin = (getattr(__import__("flask"), "request").headers.get("Origin") or "")
                if req_origin in allowed_origins:
                    resp.headers["Access-Control-Allow-Origin"] = req_origin
                    resp.headers["Vary"] = "Origin"
                    resp.headers["Access-Control-Allow-Credentials"] = "true"
                    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        except Exception:
            pass
        return resp
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from models import (
        Dataset,
        DiscussionComment,
        DiscussionPost,
        EvaluationTask,
        LiteraryWork,
        User,
    )  # noqa: F401
    from routes_auth import bp as auth_bp
    from routes_catalog import bp as catalog_bp
    from routes_dashboard import bp as dashboard_bp
    from routes_datasets import bp as datasets_bp
    from routes_eval import bp as eval_bp
    from routes_glossary_api import bp as glossary_api_bp
    from routes_ocr import bp as ocr_bp
    from routes_works import bp as works_bp
    from routes_discussion import bp as discussion_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(eval_bp)
    app.register_blueprint(glossary_api_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(works_bp)
    app.register_blueprint(discussion_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


# 供 `flask --app app run` / `flask db migrate` 使用
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

