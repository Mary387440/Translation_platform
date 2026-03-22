"""场景文字：PaddleOCR 占位接口。若部署 paddleocr 可在此接入真实识别。"""
import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

bp = Blueprint("ocr", __name__, url_prefix="/api/ocr")


def _uid():
    return int(get_jwt_identity())


@bp.post("/scan")
@jwt_required()
def scan_image():
    """
    上传图片，返回识别文本 + 模拟译文。
    生产环境可安装 paddleocr 并在此调用。
    """
    user_id = _uid()
    if "file" not in request.files:
        return jsonify({"message": "请上传 file 图片"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"message": "空文件"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        return jsonify({"message": "仅支持 png/jpg/jpeg/webp/bmp"}), 400

    name = secure_filename(f.filename) or f"img{ext}"
    sub = os.path.join("ocr", str(user_id))
    save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], sub)
    os.makedirs(save_dir, exist_ok=True)
    fn = f"{uuid.uuid4().hex[:12]}_{name}"
    path = os.path.join(save_dir, fn)
    f.save(path)

    target_lang = (request.form.get("target_lang") or "en").strip()[:10]
    # 占位：未接入 PaddleOCR 时返回示例句
    recognized = (
        "[PaddleOCR 占位] 请配置 OCR 后替换为真实识别结果。"
        " 示例：霓虹灯下的招牌写着「故事刚刚开始」。"
    )
    translated = (
        f"[Stub translate → {target_lang}] The story has just begun "
        "(under the neon sign)."
    )
    return jsonify(
        {
            "engine": "paddle_stub",
            "saved_path": f"{sub}/{fn}".replace("\\", "/"),
            "recognized_text": recognized,
            "translated_text": translated,
            "hint": "安装 paddleocr 并在 routes_ocr.scan_image 中接入可实现计划书所述能力",
        }
    )
