import collections
import gzip
import json
import math
import pathlib
import sys
import time

from pdfminer.layout import LTChar
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

sys.stdout.reconfigure(encoding="utf-8")
WORK = pathlib.Path(__file__).resolve().parent
ROOT = WORK.parents[1]
PDF = ROOT / "ACKSII" / "Source" / "ACKSII Revised Rulebook.pdf"
MAPS = json.loads((WORK / "font-codes.json").read_text(encoding="utf-8"))
STATS = collections.Counter()
CHECKS = []


class TextOnly(PDFTextDevice):
    def begin_page(self, page, ctm):
        self.width = float(page.mediabox[2] - page.mediabox[0])
        self.height = float(page.mediabox[3] - page.mediabox[1])
        self.chars = []

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        try:
            raw = font.to_unichr(cid)
        except Exception:
            raw = f"(cid:{cid})"
        name = font.fontname
        if isinstance(name, bytes):
            name = name.decode("latin1")
        text = MAPS.get(name, {}).get(str(cid), raw)
        if "Damage-Icons" in name or "Wingdings" in name:
            text = raw
        if text != raw:
            STATS["font_encoding_repairs"] += 1
        char = LTChar(matrix, font, fontsize, scaling, rise, text, font.char_width(cid), font.char_disp(cid), ncs, graphicstate)
        color = graphicstate.ncolor
        if isinstance(color, (list, tuple)):
            color = [round(float(x), 5) for x in color]
        self.chars.append({
            "text":text, "x0":round(char.x0,5), "x1":round(char.x1,5),
            "top":round(self.height-char.y1,5), "bottom":round(self.height-char.y0,5),
            "font":name.split("+",1)[-1], "size":round(char.size,5),
            "upright":char.upright, "color":color,
            "matrix": [round(float(x),5) for x in matrix[:4]],
            "code":cid,
        })
        return char.adv


def dedupe(chars):
    buckets = collections.defaultdict(list)
    result = []
    for c in chars:
        x,y=c["x0"],c["top"]
        ix,iy=math.floor(x),math.floor(y)
        duplicate = False
        for bx in (ix-1,ix,ix+1):
            for by in (iy-1,iy,iy+1):
                for previous in buckets[(c["text"],bx,by)]:
                    if abs(previous["x0"]-x)<=1 and abs(previous["top"]-y)<=1:
                        duplicate=True;break
                if duplicate:break
            if duplicate:break
        if not duplicate:
            c["id"]=len(result)
            result.append(c)
            buckets[(c["text"],ix,iy)].append(c)
    return result


def rotate_box(box, width, height, clockwise):
    x0,y0,x1,y1=box
    return [height-y1,x0,height-y0,x1] if clockwise else [y0,width-x1,y1,width-x0]


def main():
    start=time.time()
    resources=PDFResourceManager()
    device=TextOnly(resources)
    interpreter=PDFPageInterpreter(resources,device)
    geometry=WORK/"geometry.jsonl.gz"
    old_file=gzip.open(geometry,"rt",encoding="utf-8") if geometry.exists() else (WORK/"pages.jsonl").open(encoding="utf-8")
    with PDF.open("rb") as pdf, old_file, (WORK/"pages-corrected.jsonl").open("w",encoding="utf-8") as out:
        for number,page in enumerate(PDFPage.get_pages(pdf),1):
            old=json.loads(next(old_file))
            interpreter.process_page(page)
            chars=dedupe(device.chars)
            if len(device.chars)!=old["raw_chars"]:
                CHECKS.append({"page":number,"kind":"raw_char_count_difference","old":old["raw_chars"],"new":len(device.chars)})
            old.update({"chars":chars,"deduplicated_chars":len(chars),"unicode_corrected":True})
            body=[c for c in chars if 60<=c["top"] and c["bottom"]<770 and 25<(c["x0"]+c["x1"])/2<device.width-25 and not (c["font"]=="Constantine" and c["top"]>738)]
            rotated=[c for c in body if not c["upright"]]
            if len(rotated)>len(body)*0.8 and len(rotated)>100:
                clockwise=sum(c["matrix"][1]>0 for c in rotated)>len(rotated)/2
                footer=sorted([c for c in chars if c["top"]>738 and "Constantine" in c["font"]],key=lambda c:c["x0"])
                old["printed_override"]="".join(c["text"] for c in footer).strip()
                for c in chars:
                    c["in_body"] = c in body
                    box=rotate_box([c["x0"],c["top"],c["x1"],c["bottom"]],device.width,device.height,clockwise)
                    c.update(dict(zip(("x0","top","x1","bottom"),box)))
                    c["upright"]=not c["upright"]
                    if c["upright"]:c["size"]=round(c["bottom"]-c["top"],5)
                for table in old["tables"]:
                    table["bbox"]=rotate_box(table["bbox"],device.width,device.height,clockwise)
                    table["cells"]=[rotate_box(cell,device.width,device.height,clockwise) for cell in table["cells"]]
                for img in old["images"]:
                    box=rotate_box([img["x0"],img["top"],img["x1"],img["bottom"]],device.width,device.height,clockwise)
                    img.update(dict(zip(("x0","top","x1","bottom"),box)))
                old["width"],old["height"]=device.height,device.width
                old["rotation_normalized"]=90 if clockwise else -90
                STATS["rotated_pages"]+=1
            out.write(json.dumps(old,ensure_ascii=False)+"\n");out.flush()
            STATS["pages"]+=1
            STATS["raw_chars"]+=len(device.chars)
            STATS["deduplicated_chars"]+=len(chars)
            if number%50==0:print(f"CORRECTED {number}/550 pages {time.time()-start:.1f}s",flush=True)
    (WORK/"corrected-collection-checks.json").write_text(json.dumps({"counts":dict(STATS),"checks":CHECKS},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"counts":dict(STATS),"checks":CHECKS},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
