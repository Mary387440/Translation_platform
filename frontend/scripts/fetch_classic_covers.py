import re
from pathlib import Path

import requests


OUT_DIR = Path(r"D:\Translation_platform\frontend\public\covers\classics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# key -> (title, douban subject id)
TARGETS = {
    "hongloumeng": ("红楼梦", "5916840"),
    "sanguoyanyi": ("三国演义", "1315153"),
    "shuihuzhuan": ("水浒传", "30151680"),
    "xiyouji": ("西游记", "1638729"),
    "liaozhaizhiyi": ("聊斋志异", "1209632"),
    "rulinwaishi": ("儒林外史", "35002408"),
    "fengshenyanyi": ("封神演义", "1203365"),
    "nahan": ("呐喊", "27077696"),
    "panghuang": ("彷徨", "26710671"),
    "luotuoxiangzi": ("骆驼祥子", "35751135"),
    "weicheng": ("围城", "26392639"),
    "biancheng": ("边城", "1013980"),
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_cover_url_by_subject(subject_id: str) -> str | None:
    page_url = f"https://book.douban.com/subject/{subject_id}/"
    headers = {**UA, "Referer": "https://book.douban.com/"}
    r = requests.get(page_url, headers=headers, timeout=25)
    r.raise_for_status()
    html = r.text
    # 常见封面地址：img*.doubanio.com/view/subject/s|l/public/sxxxx.jpg
    m = re.search(
        r"https://img\d+\.doubanio\.com/view/subject/(?:s|l)/public/s\d+\.jpg",
        html,
    )
    if not m:
        return None
    url = m.group(0)
    return url.replace("/subject/s/public/", "/subject/l/public/")


def download(url: str, out_path: Path, referer: str) -> bool:
    headers = {**UA, "Referer": referer}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200 or not r.content:
        return False
    out_path.write_bytes(r.content)
    return True


def main():
    ok = []
    failed = []
    for key, (title, sid) in TARGETS.items():
        out = OUT_DIR / f"{key}.jpg"
        try:
            url = fetch_cover_url_by_subject(sid)
            if not url:
                failed.append((key, title, "cover url not found"))
                continue
            if download(url, out, referer=f"https://book.douban.com/subject/{sid}/"):
                ok.append((key, title, url))
            else:
                failed.append((key, title, "download failed"))
        except Exception as e:
            failed.append((key, title, str(e)))

    print("SUCCESS:")
    for key, title, _ in ok:
        print(f"- {key}.jpg <- {title}")
    print("\nFAILED:")
    for key, title, reason in failed:
        print(f"- {key} ({title}): {reason}")


if __name__ == "__main__":
    main()

