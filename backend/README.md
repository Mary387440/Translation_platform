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

# 可选：真实大模型翻译（见 .env.example）
set DEEPSEEK_API_KEY=sk-...
```

4. 同步数据库表结构（推荐 Flask-Migrate）

```bash
set FLASK_APP=app
flask db init
flask db migrate -m "init"
flask db upgrade
```

若库中已有旧表、新增列失败，请自行执行迁移或按 `models.py` 新建/更新表，包括但不限于：`datasets`、`parallel_pairs`、`literary_works`、`chapters`、`chapter_segments`、`work_translations`、`reader_feedback` 等。

5. 启动服务

```bash
python app.py
# 或
flask run
```

## 主要 API（对齐 SailoAI 计划书能力）

- `GET /api/health` — 健康检查  
- `POST /api/auth/register` / `POST /api/auth/login` / `GET /api/auth/me` / `PUT /api/auth/profile` — 用户与偏好语种  
- `GET /api/dashboard/summary` — 控制台汇总  
- **书库与翻译**：`GET|POST /api/works`，`GET /api/works/<id>/chapters`，`POST /api/works/<id>/chapters`，`GET .../segments?target_lang=`，`POST /api/works/segments/<id>/translate`（DeepSeek + RAG），`PUT /api/works/translations/<id>/polish`，`POST .../feedback`  
- `POST /api/works/<id>/seed-demo` — 写入示例章节（体验用）  
- `GET|POST /api/datasets` — 数据集；三种导入见 **`DATASETS.md`**  
- `GET /api/glossary/entries` — 术语列表（RAG 用词）  
- `POST /api/ocr/scan` — 场景图 OCR 占位（可接 PaddleOCR）  

导入格式详见 **`DATASETS.md`**。上传文件保存在 `backend/uploads/`（已加入 `.gitignore`）。

