from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@localhost:3306/translation_platform",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB，ZIP 导入上限

    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from models import Dataset, LiteraryWork, User  # noqa: F401
    from routes_auth import bp as auth_bp
    from routes_dashboard import bp as dashboard_bp
    from routes_datasets import bp as datasets_bp
    from routes_glossary_api import bp as glossary_api_bp
    from routes_ocr import bp as ocr_bp
    from routes_works import bp as works_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(glossary_api_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(works_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


# 供 `flask --app app run` / `flask db migrate` 使用
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

