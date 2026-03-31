import argparse
import csv
import os
from typing import Iterable


DATASET_ROOT_DEFAULT = r"D:\Translation_platform\datasets\sources\Classical-Modern-main"
EXPORT_DIR_DEFAULT = r"D:\Translation_platform\datasets\exports"


def _try_decode(raw: bytes, encodings: list[str]) -> str | None:
    for enc in encodings:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def _read_lines_safely(path: str) -> list[str]:
    # 语料一般是 utf-8；这里做多编码兜底，避免因个别文件编码差异导致脚本中断。
    with open(path, "rb") as f:
        raw = f.read()
    text = _try_decode(raw, ["utf-8-sig", "utf-8", "gb18030", "gbk", "latin1"])
    if text is None:
        # latin1 永远能解码，但为了类型一致这里兜底。
        text = raw.decode("latin1", errors="replace")
    return text.splitlines()


def _iter_parallel_dirs(root: str) -> Iterable[str]:
    for cur_dir, _subdirs, files in os.walk(root):
        # 路径名可能包含非英文字符，但我们只根据文件名筛选。
        if "source.txt" in files and "target.txt" in files:
            yield cur_dir


def convert(
    input_root: str,
    output_tsv_path: str,
    src_lang: str,
    tgt_lang: str,
    max_rows: int,
    encoding_hint: str | None = None,
) -> None:
    os.makedirs(os.path.dirname(output_tsv_path), exist_ok=True)

    written = 0
    processed_dirs = 0
    skipped_dirs = 0

    # 用 TSV 让后端 csv.Sniffer 更容易识别；并确保包含表头。
    with open(output_tsv_path, "w", encoding="utf-8", newline="") as out_f:
        writer = csv.writer(out_f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["src_lang", "tgt_lang", "src_text", "tgt_text"])

        for d in _iter_parallel_dirs(input_root):
            processed_dirs += 1
            src_path = os.path.join(d, "source.txt")
            tgt_path = os.path.join(d, "target.txt")
            try:
                src_lines = _read_lines_safely(src_path)
                tgt_lines = _read_lines_safely(tgt_path)
            except Exception:
                skipped_dirs += 1
                continue

            n = min(len(src_lines), len(tgt_lines))
            if n <= 0:
                skipped_dirs += 1
                continue

            for i in range(n):
                s = (src_lines[i] or "").strip()
                t = (tgt_lines[i] or "").strip()
                if not s or not t:
                    continue

                writer.writerow([src_lang, tgt_lang, s, t])
                written += 1
                if written >= max_rows:
                    break
            if written >= max_rows:
                break

    print(f"[done] written_rows={written}")
    print(f"[stats] processed_dirs={processed_dirs} skipped_dirs={skipped_dirs}")
    print(f"[output] {output_tsv_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", default=DATASET_ROOT_DEFAULT)
    p.add_argument("--output", default=os.path.join(EXPORT_DIR_DEFAULT, "classical_modern_parallel_sample.tsv"))
    p.add_argument("--src-lang", default="zh_classical")
    p.add_argument("--tgt-lang", default="zh_modern")
    p.add_argument("--max-rows", type=int, default=5000)
    args = p.parse_args()

    convert(
        input_root=args.input_root,
        output_tsv_path=args.output,
        src_lang=args.src_lang,
        tgt_lang=args.tgt_lang,
        max_rows=args.max_rows,
    )


if __name__ == "__main__":
    main()

