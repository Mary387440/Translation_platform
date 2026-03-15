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

4. 初始化数据库（之后接入 Flask-Migrate）

```bash
python app.py
```

当前仅提供基础健康检查接口：

- `GET /api/health` -> `{"status": "ok"}`

