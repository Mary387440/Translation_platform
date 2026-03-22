# 数据集导入格式说明

所有接口均需登录：`Authorization: Bearer <token>`。

## 1. 术语库（`kind: terminology`）

- 上传：`POST /api/datasets/{id}/import/terminology`，表单字段名 `file`。
- 文件：**CSV 或 TSV**，UTF-8（建议带 BOM），首行为表头。
- 推荐列名：`src_lang`, `tgt_lang`, `src_term`, `tgt_term`, `note`（可选）。  
  也支持别名：`src_text`/`tgt_text`、`源语言`/`目标语言` 等（见后端 `_normalize_term_row`）。

## 2. 平行句（`kind: parallel`）

- 上传：`POST /api/datasets/{id}/import/parallel`，字段名 `file`。
- **CSV/TSV**：表头含 `src_lang`, `tgt_lang`, `src_text`, `tgt_text`（或 `source`/`target` 等别名）。
- **JSONL**：每行一个 JSON：`{"src_lang":"ja","tgt_lang":"zh","src_text":"...","tgt_text":"..."}`

## 3. 文档库（`kind: document`）

- 上传：`POST /api/datasets/{id}/import/documents`，字段名 `file`，**仅支持 .zip**。
- ZIP 内为扁平或单层目录均可；仅处理扩展名为 **`.txt` `.md` `.docx` `.pdf`** 的文件。
- 文件解压至 `backend/uploads/datasets/{user_id}/{dataset_id}/`，并在 `docs` 表中登记，`storage_path` 为相对 `uploads/` 的路径。

## 数据集元数据 API

- `GET /api/datasets` — 列表  
- `POST /api/datasets` — 创建，`{"name","kind","description?","source_note?","languages?"}`  
- `GET /api/datasets/{id}` — 详情（含统计）  
- `GET /api/datasets/{id}/parallel-pairs?limit=20` — 平行句预览  

`description` / `source_note` / `languages` 可用于前端展示类似论文中的「数据集介绍」卡片。
