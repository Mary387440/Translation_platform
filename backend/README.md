# SailoAI 小语种翻译阅读平台 - 后端

基于 Flask + SQLAlchemy + MySQL 的后端服务。

## 环境准备

1. 创建并激活虚拟环境（可选）

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置数据库连接（可在系统环境变量或 `.env` 中设置）

```bash
set DATABASE_URL=mysql+pymysql://user:password@localhost:3306/translation_platform
set JWT_SECRET_KEY=your-secret
```

4. 同步数据库表结构（推荐 Flask-Migrate）

```bash
set FLASK_APP=app
flask db init
flask db migrate -m "init"
flask db upgrade
```

若库中已有旧表、新增列失败，请自行执行 `ALTER TABLE` 为 `docs`、`glossary_entries` 增加 `dataset_id`，并新建表 `datasets`、`parallel_pairs`（字段与 `models.py` 保持一致）。

5. 启动服务

```bash
python app.py
# 或
flask run
```

## 主要 API

- `GET /api/health` — 健康检查  
- `POST /api/auth/register` / `POST /api/auth/login` / `GET /api/auth/me` — 用户与 JWT  
- `GET|POST /api/datasets` — 数据集元数据  
- `POST /api/datasets/<id>/import/terminology|parallel|documents` — 三种导入  

导入格式详见 **`DATASETS.md`**。上传文件保存在 `backend/uploads/`（已加入 `.gitignore`）。

