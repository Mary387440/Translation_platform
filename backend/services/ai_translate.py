"""DeepSeek 翻译：配置 API Key 则走在线接口，否则返回可读的模拟译文（便于开发联调）。"""
import os
from typing import Optional

import requests


def translate_literary(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary_block: str = "",
    parallel_block: str = "",
) -> tuple[str, str]:
    """
    返回 (译文, 使用的引擎标签 deepseek|mock)
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
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

    if not api_key:
        mock = _mock_translate(text, target_lang, glossary_block)
        return mock, "mock"

    url = f"{base}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.4,
        "max_tokens": 4096,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        out = data["choices"][0]["message"]["content"].strip()
        return out, "deepseek"
    except Exception as e:
        err = f"[DeepSeek 调用失败，已回退模拟] {e}\n" + _mock_translate(
            text, target_lang, glossary_block
        )
        return err, "mock"


def _mock_translate(text: str, target_lang: str, glossary_block: str) -> str:
    hint = ""
    if glossary_block:
        hint = "（已注入术语提示）"
    return f"[模拟译文·{target_lang}]{hint}\n{text[:2000]}"
