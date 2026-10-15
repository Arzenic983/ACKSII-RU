"""Recover Unicode from PDF glyph names and widths where ToUnicode is defective."""
import collections
import json
import pathlib
import re
import sys

from pdfminer.encodingdb import EncodingDB, name2unicode
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")
WORK = pathlib.Path(__file__).resolve().parent
ROOT = WORK.parents[1]
PDF = ROOT / "ACKSII" / "Source" / "ACKSII Revised Rulebook.pdf"


def glyph_text(name):
    name = str(name).lstrip("/")
    try:
        text = name2unicode(name)
    except (KeyError, ValueError):
        return None
    if name.endswith(".sc"):
        text = text.upper()
    return text


def main():
    reader = PdfReader(PDF)
    seen = set()
    lookups = collections.defaultdict(lambda: collections.defaultdict(list))
    code_maps = {}
    def visit(res):
        for ref in (res.get("/Font") or {}).values():
            font = ref.get_object()
            base = str(font.get("/BaseFont", "")).lstrip("/")
            if base in seen or "/Widths" not in font:
                continue
            seen.add(base)
            fname = base.split("+", 1)[-1]
            encoding = font.get("/Encoding")
            if isinstance(encoding, str):
                base_encoding = str(encoding).lstrip("/")
                differences = []
            elif encoding:
                base_encoding = str(encoding.get("/BaseEncoding", "/StandardEncoding")).lstrip("/")
                differences = encoding.get("/Differences", [])
            else:
                base_encoding = "StandardEncoding"
                differences = []
            encoded = dict(EncodingDB.get_encoding(base_encoding))
            code = 0
            for item in differences:
                if isinstance(item, int):
                    code = item
                else:
                    text = glyph_text(item)
                    if text is not None:
                        encoded[code] = text
                    code += 1
            rawmap = {}
            if "/ToUnicode" in font:
                cmap = font["/ToUnicode"].get_data().decode("latin1")
                for block in re.findall(r"beginbfchar(.*?)endbfchar", cmap, re.S):
                    for source, target in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
                        try:
                            rawmap[int(source, 16)] = bytes.fromhex(target).decode("utf-16-be")
                        except (ValueError, UnicodeDecodeError):
                            pass
            code_maps[base] = {str(k):v for k,v in encoded.items()}
            first = int(font.get("/FirstChar", 0))
            widths = font["/Widths"]
            for code, fixed in encoded.items():
                pos = code-first
                if not 0 <= pos < len(widths):
                    continue
                raw = rawmap.get(code)
                # Unmapped WinAnsi C1 codes may be exposed literally by pdfminer.
                if raw is None and 0x80 <= code <= 0x9F:
                    raw = chr(code)
                if raw is None:
                    continue
                entry = {"width":float(widths[pos]), "fixed":fixed, "code":code, "changed":raw != fixed}
                if entry not in lookups[fname][raw]:
                    lookups[fname][raw].append(entry)
        for ref in (res.get("/XObject") or {}).values():
            obj = ref.get_object()
            if "/Resources" in obj:
                visit(obj["/Resources"])
    for page in reader.pages:
        visit(page["/Resources"])
    path = WORK / "font-encoding.json"
    path.write_text(json.dumps(lookups, ensure_ascii=False), encoding="utf-8")
    (WORK / "font-codes.json").write_text(json.dumps(code_maps, ensure_ascii=False), encoding="utf-8")
    print("FONTS", len(lookups), "GLYPH_ENTRIES",sum(len(entries) for font in lookups.values() for entries in font.values()))
    print("DEFECTIVE_MAPPINGS", sum(e["changed"] for font in lookups.values() for entries in font.values() for e in entries))


if __name__ == "__main__":
    main()
