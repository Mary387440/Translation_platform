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

浏览器访问 `http://localhost:5173`，登录后使用 **书库 → 一键体验示例 → AI 翻译**。

## 目录说明

| 目录 | 说明 |
|------|------|
| `backend/` | Flask API、`services/`（AI/RAG）、`uploads/` |
| `frontend/` | Vue3 + Element Plus |

详见 `backend/README.md`、`backend/DATASETS.md`、`backend/.env.example`。
