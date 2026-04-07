from __future__ import annotations

import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CATALOG = Path(r"D:\Translation_platform\frontend\src\data\classic_catalog.js")
OUT_DIR = Path(r"D:\Translation_platform\frontend\public\covers\classics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
]


def load_items() -> list[tuple[str, str, str]]:
    text = CATALOG.read_text(encoding="utf-8")
    # Keep order aligned by object blocks.
    blocks = re.findall(r"\{([^{}]+)\}", text, flags=re.S)
    items: list[tuple[str, str, str]] = []
    for b in blocks:
        km = re.search(r"key:\s*'([^']+)'", b)
        tm = re.search(r"title:\s*'《([^》]+)》'", b)
        am = re.search(r"author_name:\s*'([^']+)'", b)
        if km and tm:
            items.append((km.group(1), tm.group(1), am.group(1) if am else ""))
    return items


def pick_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for fp in FONT_CANDIDATES:
        if fp.exists():
            return ImageFont.truetype(str(fp), size=size)
    return ImageFont.load_default()


def gradient_background(w: int, h: int, seed: int) -> Image.Image:
    random.seed(seed)
    c1 = (random.randint(45, 90), random.randint(20, 70), random.randint(90, 170))
    c2 = (random.randint(140, 220), random.randint(70, 140), random.randint(120, 220))
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def render_cover(key: str, title: str, author: str, out_path: Path) -> None:
    w, h = 600, 840
    img = gradient_background(w, h, seed=abs(hash(key)) % (10**8))
    draw = ImageDraw.Draw(img)

    # Decorative frame
    frame = (242, 224, 190)
    draw.rectangle([24, 24, w - 24, h - 24], outline=frame, width=4)
    draw.rectangle([42, 42, w - 42, h - 42], outline=(255, 255, 255), width=1)

    title_font = pick_font(58)
    author_font = pick_font(34)
    brand_font = pick_font(26)

    # Title vertical chunks for Chinese-style layout
    t = title.strip()
    chunks = [t[i : i + 2] for i in range(0, len(t), 2)]
    x = w // 2 - 36
    y0 = 160
    for i, ch in enumerate(chunks[:8]):
        draw.text((x, y0 + i * 72), ch, fill=(255, 245, 225), font=title_font)

    if author:
        aw = draw.textlength(author, font=author_font)
        draw.text(((w - aw) / 2, h - 170), author, fill=(255, 240, 210), font=author_font)

    brand = "SailoAI 经典文学"
    bw = draw.textlength(brand, font=brand_font)
    draw.text(((w - bw) / 2, h - 110), brand, fill=(240, 230, 210), font=brand_font)

    img.save(out_path, format="JPEG", quality=92)


def main() -> None:
    created = []
    skipped = []
    for key, title, author in load_items():
        out = OUT_DIR / f"{key}.jpg"
        if out.exists() and out.stat().st_size > 1024:
            skipped.append(key)
            continue
        render_cover(key, title, author, out)
        created.append(key)

    print("CREATED:", len(created))
    for k in created:
        print("-", k)
    print("SKIPPED_EXISTING:", len(skipped))


if __name__ == "__main__":
    main()

