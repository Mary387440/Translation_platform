# SailoAI · 多语种文学翻译阅读平台

对齐项目计划书：**书库（网络文学）**、**DeepSeek + RAG（术语/平行句）**、**人工润色与读者反馈**、**场景 OCR 占位**、**数据集与文档库**。

## 快速启动

### 后端

```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
# 配置 DATABASE_URL、JWT_SECRET_KEY，可选 DEEPSEEK_API_KEY
flask db migrate
flask db upgrade
python app.py
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`：

- **读者**：登录后进入 **书库**，阅读已发布作品（管理员需先在后台发布并上架内容）。
- **管理员**：在数据库中将用户 `role` 设为 `admin` 后，登录会进入 **管理后台**（数据集、术语库、书稿等）。

详见 `backend/README.md`。

## 目录说明

| 目录 | 说明 |
|------|------|
| `backend/` | Flask API、`services/`（AI/RAG）、`uploads/` |
| `frontend/` | Vue3 + Element Plus |

详见 `backend/README.md`、`backend/DATASETS.md`、`backend/.env.example`。
