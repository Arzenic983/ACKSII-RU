import collections
import json
import pathlib
import sys
import time

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = pathlib.Path(__file__).resolve().parent
PDF = ROOT / "ACKSII" / "Source" / "ACKSII Revised Rulebook.pdf"
OUTPUT = WORK / "pages.jsonl"


def clean_color(value):
    if isinstance(value, (list, tuple)):
        return [round(float(x), 5) for x in value]
    if isinstance(value, (int, float)):
        return round(float(value), 5)
    return str(value) if value is not None else None


def slim_char(c, index):
    return {
        "id": index,
        "text": c["text"],
        "x0": round(c["x0"], 5),
        "x1": round(c["x1"], 5),
        "top": round(c["top"], 5),
        "bottom": round(c["bottom"], 5),
        "font": c["fontname"].split("+", 1)[-1],
        "size": round(c["size"], 5),
        "upright": c["upright"],
        "color": clean_color(c.get("non_stroking_color", c.get("nonstroking_color"))),
    }


def main():
    start = time.time()
    stats = collections.Counter()
    unusual = collections.defaultdict(collections.Counter)
    with pdfplumber.open(PDF) as pdf, OUTPUT.open("w", encoding="utf-8") as out:
        for number, raw_page in enumerate(pdf.pages, 1):
            page = raw_page.dedupe_chars(tolerance=1, extra_attrs=())
            chars = [slim_char(c, i) for i, c in enumerate(page.chars)]
            tables = []
            for table in page.find_tables():
                if len(table.rows) < 2:
                    continue
                cells = [[round(v, 5) for v in cell] for cell in table.cells]
                xs = sorted({cell[0] for cell in cells} | {cell[2] for cell in cells})
                if len(xs) < 3:
                    continue
                tables.append({"bbox": list(table.bbox), "cells": cells})
            images = [
                {k: round(float(img[k]), 3) for k in ("x0", "x1", "top", "bottom")}
                for img in page.images
            ]
            for c in chars:
                for ch in c["text"]:
                    if ord(ch) < 32 or ch == "\ufffd" or 0xE000 <= ord(ch) <= 0xF8FF:
                        unusual[c["font"]][f"U+{ord(ch):04X}"] += 1
            record = {
                "page": number,
                "width": page.width,
                "height": page.height,
                "raw_chars": len(raw_page.chars),
                "deduplicated_chars": len(chars),
                "chars": chars,
                "tables": tables,
                "images": images,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            stats["pages"] += 1
            stats["raw_chars"] += len(raw_page.chars)
            stats["deduplicated_chars"] += len(chars)
            stats["duplicate_chars_removed"] += len(raw_page.chars) - len(chars)
            stats["candidate_tables"] += len(tables)
            if len(chars) < 100:
                stats["pages_below_100_chars"] += 1
            raw_page.close()
            if number % 25 == 0 or number == len(pdf.pages):
                print(f"AUDIT {number}/{len(pdf.pages)} pages; {stats['candidate_tables']} tables; {time.time()-start:.1f}s", flush=True)
    summary = {"counts": dict(stats), "unusual_by_font": {k: dict(v) for k, v in unusual.items()}}
    (WORK / "audit-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
