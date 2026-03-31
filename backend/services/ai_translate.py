"""
翻译服务：
1) 配置 DeepSeek API Key：优先走 DeepSeek
2) DeepSeek 调用失败：若配置百度翻译 API，则回退到百度翻译（避免 mock 导致“看起来没真正翻译”）
3) 两者都未配置：返回可读的模拟译文（便于开发联调）
"""

import hashlib
import os
import random
import time
from typing import Tuple

import requests


def translate_literary(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary_block: str = "",
    parallel_block: str = "",
) -> tuple[str, str]:
    """
    返回 (译文, 使用的引擎标签 deepseek|baidu|mock)
    """
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    system = (
        "你是一名资深文学译者，负责将中国网络文学译为目标语言，要求自然、符合母语读者习惯，"
        "保留语气与文化内涵。以下为术语与句对参考，请尽量遵守术语译法。"
    )
    user_parts = [
        f"源语言: {source_lang}",
        f"目标语言: {target_lang}",
        "正文:",
        text[:8000],
    ]
    if glossary_block:
        user_parts.insert(3, "术语表:\n" + glossary_block)
    if parallel_block:
        user_parts.insert(3, "平行句参考:\n" + parallel_block)
    user_content = "\n\n".join(user_parts)

    deepseek_err: str | None = None
    baidu_err: str | None = None

    try:
        if deepseek_api_key:
            url = f"{base}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.4,
                "max_tokens": 4096,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=120)
            r.raise_for_status()
            data = r.json()
            out = data["choices"][0]["message"]["content"].strip()
            return out, "deepseek"
    except Exception as e:
        # DeepSeek 没开通/余额不足等场景会抛异常，这里优先回退到百度翻译
        deepseek_err = str(e)
        if _baidu_configured():
            try:
                out = _baidu_translate(text, source_lang, target_lang)
                if out.strip():
                    return out, "baidu"
                baidu_err = "百度翻译返回为空"
            except Exception as be:
                baidu_err = str(be)

        err = "[DeepSeek 调用失败，回退百度失败/未配置后回退 mock]\n"
        if deepseek_err:
            err += f"DeepSeek error: {deepseek_err}\n"
        if baidu_err:
            err += f"Baidu error: {baidu_err}\n"
        err += _mock_translate(
            text, target_lang, glossary_block
        )
        return err, "mock"

    # DeepSeek 没配置：直接走百度（若配置），否则 mock
    if _baidu_configured():
        try:
            out = _baidu_translate(text, source_lang, target_lang)
            if out.strip():
                return out, "baidu"
            baidu_err = "百度翻译返回为空"
        except Exception as be:
            baidu_err = str(be)

    err = "[百度翻译不可用/失败，回退 mock]\n"
    if baidu_err:
        err += f"Baidu error: {baidu_err}\n"
    err += _mock_translate(text, target_lang, glossary_block)
    mock = _mock_translate(text, target_lang, glossary_block)
    # 保持返回长度较短：若 err 已包含 mock 内容，就直接返回 err
    return err if err else mock, "mock"


def _baidu_configured() -> bool:
    app_id = os.getenv("BAIDU_APP_ID", "").strip()
    secret_key = os.getenv("BAIDU_SECRET_KEY", "").strip()
    return bool(app_id and secret_key)


def _map_lang_to_baidu(lang: str) -> str:
    """
    Baidu 翻译 expects from/to language codes，例如：
    zh, en, ja, ko, es, fr, de ...
    我们把系统里的 zh_classical/zh_modern 归一为 zh。
    """
    l = (lang or "").strip().lower()
    if l.startswith("zh"):
        return "zh"
    mapping = {
        "en": "en",
        "ja": "ja",
        "japanese": "ja",
        "ko": "ko",
        "kor": "ko",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "ru": "ru",
        "pt": "pt",
        "it": "it",
        "vi": "vi",
        "ar": "ar",
        "th": "th",
    }
    return mapping.get(l, l or "auto")


def _chunk_text(text: str, max_chars: int) -> list[str]:
    if max_chars <= 0:
        max_chars = 2000
    # 简单按字符分块；句子切断会影响一点质量，但能避免接口长度限制
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _baidu_translate(text: str, source_lang: str, target_lang: str) -> str:
    app_id = os.getenv("BAIDU_APP_ID", "").strip()
    secret_key = os.getenv("BAIDU_SECRET_KEY", "").strip()
    endpoint = os.getenv(
        "BAIDU_API_URL", "https://api.fanyi.baidu.com/api/trans/vip/translate"
    ).strip()
    max_chunk = int(os.getenv("BAIDU_MAX_CHUNK_CHARS", "2000"))

    from_code = _map_lang_to_baidu(source_lang)
    to_code = _map_lang_to_baidu(target_lang)

    out_parts: list[str] = []
    for chunk in _chunk_text(text, max_chars=max_chunk):
        if not chunk.strip():
            continue

        salt = str(random.randint(10000, 99999)) + str(int(time.time()))
        sign_src = app_id + chunk + salt + secret_key
        sign = hashlib.md5(sign_src.encode("utf-8")).hexdigest()

        data = {
            "q": chunk,
            "from": from_code if from_code else "auto",
            "to": to_code,
            "appid": app_id,
            "salt": salt,
            "sign": sign,
        }
        r = requests.post(endpoint, data=data, timeout=120)
        r.raise_for_status()
        payload = r.json()

        # Baidu returns either { trans_result: [{src,dst}] } or { error_code, error_msg }
        if "error_code" in payload:
            raise RuntimeError(
                f"Baidu translate error: {payload.get('error_code')} {payload.get('error_msg')}"
            )
        trans = payload.get("trans_result") or []
        dst = "".join([x.get("dst", "") for x in trans]).strip()
        if dst:
            out_parts.append(dst)

    return "\n".join(out_parts).strip()


def _mock_translate(text: str, target_lang: str, glossary_block: str) -> str:
    hint = ""
    if glossary_block:
        hint = "（已注入术语提示）"
    return f"[模拟译文·{target_lang}]{hint}\n{text[:2000]}"
