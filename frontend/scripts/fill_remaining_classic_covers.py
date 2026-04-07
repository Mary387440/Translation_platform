from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

import requests


CATALOG = Path(r"D:\Translation_platform\frontend\src\data\classic_catalog.js")
OUT_DIR = Path(r"D:\Translation_platform\frontend\public\covers\classics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def load_items() -> list[tuple[str, str]]:
    text = CATALOG.read_text(encoding="utf-8")
    keys = re.findall(r"key:\s*'([^']+)'", text)
    titles = re.findall(r"title:\s*'《([^》]+)》'", text)
    n = min(len(keys), len(titles))
    return [(keys[i], titles[i]) for i in range(n)]


def wiki_thumb(title: str) -> str | None:
    api = (
        "https://zh.wikipedia.org/w/api.php"
        "?action=query&format=json&prop=pageimages&piprop=thumbnail"
        "&pithumbsize=700&titles="
        + quote(title)
    )
    r = requests.get(api, headers=UA, timeout=25)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    for page in pages.values():
        src = page.get("thumbnail", {}).get("source")
        if src:
            return src
    return None


def download(url: str, out: Path) -> bool:
    r = requests.get(url, headers=UA, timeout=30)
    if r.status_code != 200 or not r.content:
        return False
    out.write_bytes(r.content)
    return True


def openlibrary_cover(title: str) -> str | None:
    api = f"https://openlibrary.org/search.json?title={quote(title)}&limit=8"
    r = requests.get(api, headers=UA, timeout=20)
    r.raise_for_status()
    docs = r.json().get("docs", [])
    for d in docs:
        cid = d.get("cover_i")
        if cid:
            return f"https://covers.openlibrary.org/b/id/{cid}-L.jpg"
    return None


def main() -> None:
    ok: list[tuple[str, str, str]] = []
    fail: list[tuple[str, str, str]] = []

    for key, title in load_items():
        out = OUT_DIR / f"{key}.jpg"
        if out.exists() and out.stat().st_size > 1024:
            continue
        try:
            url = wiki_thumb(title)
            if url and download(url, out):
                ok.append((key, title, url))
                continue
            ol = openlibrary_cover(title)
            if ol and download(ol, out):
                ok.append((key, title, ol))
                continue
            fail.append((key, title, "all_sources_failed"))
        except Exception as e:  # noqa: BLE001
            fail.append((key, title, str(e)))

    print("SUCCESS:")
    for key, title, url in ok:
        print(f"- {key} ({title}) <- {url}")
    print("\nFAILED:")
    for key, title, reason in fail:
        print(f"- {key} ({title}): {reason}")


if __name__ == "__main__":
    main()

