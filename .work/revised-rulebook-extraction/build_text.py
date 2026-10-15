"""Reconstruct page-aware English text from native PDF characters, not OCR guesses."""
import bisect
import collections
import gzip
import hashlib
import html as html_lib
import json
import pathlib
import re
import sys

from pdfplumber.utils import chars_to_textmap, extract_text, extract_words
from manual_pages import MANUAL, ART_ONLY

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "ACKSII" / "Source"
OUT = SOURCE / "ACKSII Revised Rulebook (EN working text).md"

ICONS = {
    "\ue900": "acidic", "\ue901": "arcane", "\ue902": "bludgeoning",
    "\ue903": "necrotic", "\ue904": "cold", "\ue905": "electric",
    "\ue906": "fire", "\ue907": "luminous", "\ue908": "slashing",
    "\ue90b": "piercing", "\ue90c": "poisonous", "\ue90d": "seismic",
    "\ue910": "varies by weapon",
}
COUNTS = collections.Counter()
FLAGS = []
TABLES = []
PAGE_CHECKS = []
HYPHENS = []
CURRENT_PAGE = None
FONT_LOOKUPS = json.loads((WORK / "font-encoding.json").read_text(encoding="utf-8"))


def center(c):
    return ((c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2)


def in_body(c,rec):
    # Assess margins in the original portrait coordinate system, including
    # notes and table rows that extend below the usual text frame.
    if rec.get("rotation_normalized")==90:
        x0,x1,y0,y1=c["top"],c["bottom"],rec["width"]-c["x1"],rec["width"]-c["x0"]
        width=rec["height"]
    elif rec.get("rotation_normalized")==-90:
        x0,x1,y0,y1=rec["height"]-c["bottom"],rec["height"]-c["top"],c["x0"],c["x1"]
        width=rec["height"]
    else:
        x0,x1,y0,y1=c["x0"],c["x1"],c["top"],c["bottom"]
        width=rec["width"]
    return y0>=60 and y1<770 and 25<(x0+x1)/2<width-25 and not (c["font"]=="Constantine" and y0>738)


def is_red(color):
    if isinstance(color, list) and len(color) == 4:
        return color[0] < 0.2 and color[1] > 0.8 and color[2] > 0.8 and color[3] < 0.2
    if isinstance(color, list) and len(color) == 3:
        return color[0] > 0.7 and color[1] < 0.35 and color[2] < 0.35
    return False


def prepare(c, number):
    c = dict(c)
    c["fontname"] = c["font"]
    c["doctop"] = c["top"]
    text = c["text"]
    candidates = [] if c.get("code") is not None else FONT_LOOKUPS.get(c["font"], {}).get(text, [])
    if candidates and c["size"] and "Damage-Icons" not in c["font"]:
        width = (c["x1"]-c["x0"]) / c["size"] * 1000
        close = [e for e in candidates if abs(e["width"]-width) < 0.5]
        choices = {e["fixed"] for e in close}
        if len(choices) == 1:
            fixed = choices.pop()
            if fixed != text:
                COUNTS["font_unicode_repairs"] += 1
                text = fixed
        elif len(choices) > 1:
            FLAGS.append({"page":number,"kind":"glyph_case_ambiguity","id":c["id"],"text":text,"choices":sorted(choices),"font":c["font"]})
    if "ACKS2e-Damage-Icons" in c["font"]:
        if text in ICONS:
            kind = "extraordinary" if is_red(c["color"]) else "mundane"
            text = f" [{kind} {ICONS[text]}] "
            COUNTS[f"{kind}_damage_icons"] += 1
        elif text.strip():
            FLAGS.append({"page": number, "kind": "unknown_damage_icon", "char": repr(text), "id": c["id"]})
    if c["font"] == "Wingdings-Regular" and text in ("\x8d","\t"):
        text = "♦"
        COUNTS["list_bullets_recovered"] += 1
    if c["font"] == "Wingdings2" and text == "\x9a":
        text = "◇"
        COUNTS["list_bullets_recovered"] += 1
    if "\ufffd" in text:
        # The affected font supplies dotted TOC leaders; these are not lost letters.
        if number in (5, 6, 7) and ("Trajan" in c["font"] or "MinionPro-Semibold" in c["font"]):
            text = text.replace("\ufffd", ".")
            COUNTS["toc_leader_glyphs_recovered"] += 1
        else:
            FLAGS.append({"page": number, "kind": "replacement_character", "id": c["id"], "font": c["font"]})
    if "TrajanPro3-Bold" in c["font"] or "ImperatorSmallCaps" in c["font"] or "Archeologicaps" in c["font"]:
        text = text.upper()
    for ch in text:
        if (ord(ch) < 32 and ch not in "\t\r\n") or 0x7F <= ord(ch) < 0xA0 or 0xE000 <= ord(ch) <= 0xF8FF:
            FLAGS.append({"page": number, "kind": "unresolved_glyph", "char": repr(ch), "font": c["font"], "id": c["id"]})
    for glyph,letters in {"ﬀ":"ff","ﬁ":"fi","ﬂ":"fl","ﬃ":"ffi","ﬄ":"ffl","ﬅ":"st","ﬆ":"st"}.items():
        if glyph in text:
            text=text.replace(glyph,letters)
            COUNTS["ligatures_expanded"]+=1
    c["text"] = text.replace("\u00a0", " ")
    return c


def clusters(values, tolerance=0.8):
    groups = []
    for value in sorted(set(values)):
        if groups and value - groups[-1][-1] <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(g) / len(g) for g in groups]


def get_lines(chars):
    if not chars:
        return []
    textmap = chars_to_textmap(chars, layout=False, x_tolerance=2, x_tolerance_ratio=0.3, y_tolerance=4)
    lines = textmap.extract_text_lines(strip=True, return_chars=True)
    groups=[]
    current=[]
    for item in textmap.tuples:
        if item[0] == "\n":
            if "".join(x[0] for x in current).strip():groups.append(current)
            current=[]
        else:current.append(item)
    if "".join(x[0] for x in current).strip():groups.append(current)
    for line,group in zip(lines,groups):
        line["tuples"] = group
    return lines


def plain(chars):
    if not chars:
        return ""
    return extract_text(chars, x_tolerance=2, x_tolerance_ratio=0.3, y_tolerance=4, layout=False).strip()


def format_line(line, html=False):
    tuples = line.get("tuples",[])
    raw = "".join(ch for ch,_ in tuples)
    groups = []
    for match in re.finditer(r"\S+",raw):
        chars = [c for _,c in tuples[match.start():match.end()] if c is not None]
        styles = collections.Counter()
        for c in chars:
            font = c["font"].lower()
            bold = "bold" in font
            italic = "-it" in font or "italic" in font or font.endswith("boldit")
            styles[(bold,italic)] += len(c["text"])
        style = styles.most_common(1)[0][0] if styles else (False,False)
        text = tidy(match.group(0))
        text = html_lib.escape(text) if html else text.replace("*", "\\*").replace("_", "\\_")
        if groups and groups[-1][0] == style:
            groups[-1][1] += " " + text
        else:
            groups.append([style,text])
    out=[]
    for (bold,italic),text in groups:
        if html:
            if italic:text="<em>"+text+"</em>"
            if bold:text="<strong>"+text+"</strong>"
            out.append(text)
        else:
            marker = "***" if bold and italic else "**" if bold else "*" if italic else ""
            out.append(marker+text+marker)
    return " ".join(out)


def tidy(text):
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = text.replace("\u00ad", "")
    return text


def join_lines(lines, table=False):
    text = ""
    for line in lines:
        line = tidy(line)
        if not line:
            continue
        ending=re.search(r"([A-Za-z]+)-(\*{0,3})$",text)
        starting=re.match(r"(\*{0,3})([a-z][A-Za-z]*)",line)
        if text and ending and starting and starting.group(2) not in ("or","and"):
            # Keep the visible hyphen. Later corpus-assisted review distinguishes
            # genuine compounds from typographic word division.
            HYPHENS.append({"page":CURRENT_PAGE,"left":ending.group(1),"right":starting.group(2),"styles":[ending.group(2),starting.group(1)]})
            if ending.group(2) and ending.group(2)==starting.group(1):
                text=text[:-len(ending.group(2))]+line[len(starting.group(1)):]
            else:
                text += line
            COUNTS["hyphenated_line_joins"] += 1
        elif text:
            text += ("<br>" if table else " ") + line
        else:
            text = line
    return text


def render_prose(chars, page):
    lines = get_lines(chars)
    out = []
    pending = []
    previous = None
    previous_heading = False
    def flush():
        if pending:
            out.append(join_lines(pending))
            pending.clear()
    for line in lines:
        lc = line["chars"]
        text = tidy(line["text"])
        if not text:
            continue
        heading = sum(len(c["text"]) for c in lc if "Trajan" in c["font"] or "Imperator" in c["font"] or "Archeologicaps" in c["font"]) > sum(len(c["text"]) for c in lc) * 0.7
        gap = line["top"] - previous["bottom"] if previous else 0
        indentation = line["x0"] - previous["x0"] if previous else 0
        bold_lead = bool(lc and "Bold" in lc[0]["font"] and ":" in text[:100])
        if heading:
            flush()
            level = "###" if max(c["size"] for c in lc) >= 18 else "####"
            if previous_heading and gap < 5 and out and out[-1].startswith(level+" "):
                out[-1] += " " + text
            else:
                out.append(f"{level} {text}")
        else:
            if gap > 4.5 or bold_lead:
                flush()
            if re.match(r"^(?:•|♦|◇|[0-9]+\.)\s", text):
                flush()
            pending.append(format_line(line))
        previous = line
        previous_heading = heading
    flush()
    return "\n\n".join(out)


def render_contents(chars, page):
    """Read the three columns in order, joining only wrapped entry titles."""
    title = [c for c in chars if c["size"] >= 20]
    rest = [c for c in chars if c not in title]
    bounds = {5:[25,229,402,587],6:[25,210,378,587],7:[25,237,405,587]}[page]
    rows = []
    pending = []
    for x0,x1 in zip(bounds,bounds[1:]):
        for line in get_lines([c for c in rest if x0 <= center(c)[0] < x1]):
            raw = "".join(ch for ch,_ in line["tuples"])
            ending = re.search(r"(?:\s*\.+\s*|\s+)(\d+)\s*$",raw)
            if ending:
                part = dict(line)
                part["tuples"] = line["tuples"][:ending.start()]
                pending.append(format_line(part))
                rows.append("| "+join_lines(pending).replace("|","\\|")+" | "+ending.group(1)+" |")
                pending=[]
            else:
                pending.append(format_line(line))
        if pending:
            FLAGS.append({"page":page,"kind":"unfinished_contents_entry","text":pending})
    COUNTS["contents_entries"] += len(rows)
    head = render_prose(title,page)+"\n\n" if title else ""
    return head+"| Contents | Printed page |\n| --- | --- |\n"+"\n".join(rows)


def verify_payload(body, rendered, page):
    """Check that formatting does not lose or repeat letters, digits or symbols."""
    rendered = rendered.replace("<br>"," ")
    rendered = re.sub(r"</?(?:table|tr|td|th|strong|em)(?: [^>]+)?>", "", rendered)
    rendered = html_lib.unescape(rendered)
    if page in (5,6,7):
        rendered = rendered.replace("| Contents | Printed page |","")
    payload = lambda text: collections.Counter(ch for ch in text if ch.isalnum() or ch in "♦◇")
    expected = payload("".join(c["text"] for c in body))
    actual = payload(rendered)
    missing,extra = expected-actual,actual-expected
    if missing or extra:
        FLAGS.append({"page":page,"kind":"rendered_payload_difference","missing":dict(missing),"extra":dict(extra)})
    else:
        COUNTS["pages_payload_verified"] += 1


def inside(c, box):
    x, y = center(c)
    return box[0] - 0.1 <= x <= box[2] + 0.1 and box[1] - 0.1 <= y <= box[3] + 0.1


def make_table(t, chars, page, table_index):
    xs = clusters([cell[i] for cell in t["cells"] for i in (0, 2)])
    ys = clusters([cell[i] for cell in t["cells"] for i in (1, 3)])
    rows = [[[] for _ in range(len(xs)-1)] for _ in range(len(ys)-1)]
    for c in chars:
        x, y = center(c)
        col = max(0, min(len(xs)-2, bisect.bisect_right(xs, x)-1))
        row = max(0, min(len(ys)-2, bisect.bisect_right(ys, y)-1))
        rows[row][col].append(c)
    spans=[]
    nearest=lambda values,value:min(range(len(values)),key=lambda i:abs(values[i]-value))
    def add_span(span):
        if span[1]-span[0]==1 and span[3]-span[2]==1:return
        overlaps=[s for s in spans if max(span[0],s[0])<min(span[1],s[1]) and max(span[2],s[2])<min(span[3],s[3])]
        for s in overlaps:
            spans.remove(s)
            span=[min(span[0],s[0]),max(span[1],s[1]),min(span[2],s[2]),max(span[3],s[3])]
        if span not in spans:spans.append(span)
    for box in t["cells"]:
        span=[nearest(ys,box[1]),nearest(ys,box[3]),nearest(xs,box[0]),nearest(xs,box[2])]
        if (span[1]-span[0])*(span[3]-span[2])<2:continue
        cc=[c for row in rows[span[0]:span[1]] for cell in row[span[2]:span[3]] for c in cell]
        letters="".join(c["text"] for c in cc if c["text"].strip())
        letters="".join(ch for ch in letters if ch.isalpha())
        if len(letters)<3 or not letters.isupper():continue
        separate=False
        for line in get_lines(cc):
            lc=sorted({c["id"]:c for c in line["chars"] if c["text"].strip()}.values(),key=lambda c:c["x0"])
            if any(right["x0"]-left["x1"]>10 for left,right in zip(lc,lc[1:])):separate=True
        if not separate:add_span(span)
    # Catch long body instructions that span columns, too. Whole words remain
    # in one merged cell even where alternating shading hides the ruled edges.
    for line in get_lines(chars):
        raw="".join(ch for ch,_ in line["tuples"])
        for word in re.finditer(r"\S+",raw):
            wc=[c for _,c in line["tuples"][word.start():word.end()] if c and c["text"].strip()]
            cols={max(0,min(len(xs)-2,bisect.bisect_right(xs,center(c)[0])-1)) for c in wc}
            rns={max(0,min(len(ys)-2,bisect.bisect_right(ys,center(c)[1])-1)) for c in wc}
            if len(cols)>1:
                if not any(s[0]<=min(rns) and s[1]>max(rns) and s[2]<=min(cols) and s[3]>max(cols) for s in spans):
                    add_span([min(rns),max(rns)+1,min(cols),max(cols)+1])
    if spans:
        covered={}
        for r0,r1,c0,c1 in spans:
            for ri in range(r0,r1):
                for ci in range(c0,c1):covered[(ri,ci)]=(r0,r1,c0,c1)
        html_rows=[]
        logical=[]
        for ri,row in enumerate(rows):
            parts=[]
            for ci,cc in enumerate(row):
                span=covered.get((ri,ci))
                attributes=""
                if span:
                    r0,r1,c0,c1=span
                    if (ri,ci)!=(r0,c0):continue
                    cc=[c for sr in rows[r0:r1] for sc in sr[c0:c1] for c in sc]
                    if r1-r0>1:attributes+=f' rowspan="{r1-r0}"'
                    if c1-c0>1:attributes+=f' colspan="{c1-c0}"'
                value=join_lines([format_line(line,html=True) for line in get_lines(cc)],table=True)
                tag="th" if ri==0 else "td"
                parts.append(f"<{tag}{attributes}>{value}</{tag}>")
                logical.append({"row":ri,"col":ci,"span":span,"text":value})
            html_rows.append("<tr>"+"".join(parts)+"</tr>")
        TABLES.append({"page":page,"table":table_index,"bbox":t["bbox"],"xs":xs,"ys":ys,"merged_cells":logical,"char_count":len(chars)})
        COUNTS["tables"]+=1
        COUNTS["table_cells"]+=(len(xs)-1)*(len(ys)-1)
        COUNTS["tables_with_merged_cells"]+=1
        COUNTS["merged_cell_spans"]+=len(spans)
        return "<table>\n"+"\n".join(html_rows)+"\n</table>"
    cells = []
    for row in rows:
        cells.append([join_lines([format_line(line) for line in get_lines(cell)], table=True).replace("|", "\\|") for cell in row])
    if page == 13 and table_index == 1:
        correct = {"Str":"STR", "Int":"INT", "dEX":"DEX", "con":"CON", "cHA":"CHA", "Hd":"HD", "Ac":"AC", "Pc":"PC", "nPc":"NPC", "tt":"TT"}
        for row in cells:
            if row[0] in correct:
                row[0] = correct[row[0]]
                COUNTS["abbreviation_case_recovered"] += 1
    if not cells:
        return ""
    TABLES.append({"page": page, "table": table_index, "bbox": t["bbox"], "xs": xs, "ys": ys, "cells": cells, "char_count": len(chars)})
    COUNTS["tables"] += 1
    COUNTS["table_cells"] += sum(len(row) for row in cells)
    header = "| " + " | ".join(cells[0]) + " |"
    separator = "| " + " | ".join("---" for _ in cells[0]) + " |"
    body = ["| " + " | ".join(row) + " |" for row in cells[1:]]
    return "\n".join([header, separator, *body])


def wide_ranges(chars, midpoint):
    lines = get_lines(chars)
    candidates = []
    for i, line in enumerate(lines):
        split=midpoint((line["top"]+line["bottom"])/2) if callable(midpoint) else midpoint
        cs = sorted([c for c in line["chars"] if c["text"].strip()], key=lambda c: c["x0"])
        wide = any(c["x0"] < split < c["x1"] for c in cs)
        if not wide:
            for left, right in zip(cs, cs[1:]):
                if left["x1"] <= split <= right["x0"] and right["x0"]-left["x1"] <= 5:
                    wide = True
                    break
        if wide:
            font = collections.Counter(c["font"] for c in cs).most_common(1)[0][0]
            candidates.append([line["top"], line["bottom"], font])
    merged = []
    for top, bottom, font in candidates:
        if merged and top <= merged[-1][1]+6:
            merged[-1][1] = max(merged[-1][1], bottom)
        else:
            merged.append([top, bottom, font])
    # Include short final lines of a full-width paragraph; do not absorb a
    # two-column line, even if it happens to share its typeface.
    for group in merged:
        for line in lines:
            split=midpoint((line["top"]+line["bottom"])/2) if callable(midpoint) else midpoint
            if group[1] <= line["top"] <= group[1]+6 and line["x1"] < split:
                font = collections.Counter(c["font"] for c in line["chars"]).most_common(1)[0][0]
                if font == group[2]:
                    group[1] = line["bottom"]
    ranges=[]
    for top,bottom,_ in merged:
        if ranges and top <= ranges[-1][1]+0.4:
            ranges[-1][1]=max(ranges[-1][1],bottom+0.2)
        else:
            ranges.append([top-0.2,bottom+0.2])
    return ranges


def column_midpoint(chars, default):
    votes = collections.Counter()
    for line in get_lines(chars):
        cs = sorted(line["chars"], key=lambda c: c["x0"])
        for left, right in zip(cs, cs[1:]):
            gap = right["x0"] - left["x1"]
            if gap > 14 and 180 < right["x0"] < 405 and 130 < left["x1"] < 370:
                for x in range(max(240,int(left["x1"]+1)),min(376,int(right["x0"]))):
                    votes[x] += 1
    if votes:
        frequency=max(votes.values())
        if frequency >= 3:
            return min((x for x,count in votes.items() if count==frequency),key=lambda x:abs(x-default))
    return default


def page_text(rec):
    global CURRENT_PAGE
    number = rec["page"]
    CURRENT_PAGE = number
    all_chars = [prepare(c, number) for c in rec["chars"]]
    low_text = len(all_chars) < 100
    footer = [c for c in all_chars if c["top"] > 738 and "Constantine" in c["font"]]
    printed = rec.get("printed_override",tidy(plain(footer)).replace(" ", ""))
    body = [c for c in all_chars if c["text"] and (low_text or in_body(c,rec))]
    if low_text:
        body = [c for c in body if c not in footer]
    if number in MANUAL or number in ART_ONLY:
        PAGE_CHECKS.append({"page":number,"body_chars":len(body),"used_chars":len(body),"printed":printed,"manual_review":True})
        COUNTS["visually_reviewed_image_pages"] += 1
        return printed, MANUAL.get(number,"<!-- Full-page illustration; decorative running headers omitted. -->")
    if not body:
        FLAGS.append({"page": number, "kind": "image_only_page", "images": len(rec["images"])})
        PAGE_CHECKS.append({"page": number, "body_chars": 0, "used_chars": 0, "printed": printed})
        return printed, "<!-- Image-only page. Visible lettering, if any, is reviewed separately. -->"
    if low_text:
        PAGE_CHECKS.append({"page": number, "body_chars": len(body), "used_chars": len(body), "printed": printed})
        return printed, render_prose(body, number)
    midpoint = rec["width"]/2 if rec.get("rotation_normalized") else 319.5 if number % 2 else 292.5
    used = set()
    table_events = []
    for table_index, t in enumerate(rec["tables"], 1):
        tc = [c for c in body if c["id"] not in used and inside(c, t["bbox"])]
        if len(tc) < 4:
            continue
        if t["bbox"][2]-t["bbox"][0] < 35 or len(clusters([cell[i] for cell in t["cells"] for i in (0, 2)])) > 32:
            FLAGS.append({"page": number, "kind": "table_geometry_review", "table": table_index, "bbox": t["bbox"]})
        content = make_table(t, tc, number, table_index)
        used.update(c["id"] for c in tc)
        caption_chars = [c for c in body if c["id"] not in used and "Trajan" in c["font"] and t["bbox"][1]-35 <= center(c)[1] < t["bbox"][1] and t["bbox"][0]-5 <= center(c)[0] <= t["bbox"][2]+5]
        caption_lines = get_lines(caption_chars)
        selected=[]
        for line in reversed(caption_lines):
            if not selected:
                if -1 <= t["bbox"][1]-line["bottom"] <= 6:selected.append(line)
            elif selected[-1]["top"]-line["bottom"] <= 5:
                selected.append(line)
            else:break
        box=list(t["bbox"])
        if selected:
            selected.reverse()
            caption=" ".join(line["text"] for line in selected)
            used.update(c["id"] for line in selected for c in line["chars"])
            content="#### "+caption+"\n\n"+content
            box[1]=selected[0]["top"]
            TABLES[-1]["caption"]=caption
            COUNTS["table_captions_attached"]+=1
        table_events.append({"box": box, "text": content,"table_index":table_index})
    remaining = [c for c in body if c["id"] not in used]
    if number in (5,6,7):
        text=render_contents(remaining,number)
        used.update(c["id"] for c in remaining)
        verify_payload(body,text,number)
        PAGE_CHECKS.append({"page":number,"body_chars":len(body),"used_chars":len(used),"printed":printed,"columns":3})
        return printed,text
    midpoint = column_midpoint(remaining, midpoint)
    full_tables = [t for t in table_events if t["box"][2]-t["box"][0] > 400]
    partial_tables = [t for t in table_events if t not in full_tables]
    def local_midpoint(y):
        for table in partial_tables:
            box=table["box"]
            if box[1]-2<=y<=box[3]+18:
                if (box[0]+box[2])/2>midpoint and box[0]<midpoint:
                    return box[0]-6
                if (box[0]+box[2])/2<midpoint and box[2]>midpoint:
                    return box[2]+6
        return midpoint
    wides = wide_ranges(remaining, local_midpoint)
    # Avoid a band intersecting a full-width table.
    wide_events = []
    for y0, y1 in wides:
        wc = [c for c in remaining if y0 <= center(c)[1] <= y1]
        if wc:
            wide_events.append({"box": [0, y0, rec["width"], y1], "chars": wc})
    global_events = sorted([*full_tables, *wide_events], key=lambda e: e["box"][1])
    out = []
    emitted_tables=set()
    cursor = 0
    def emit_band(y0, y1):
        for left in (True, False):
            local_tables = sorted([t for t in partial_tables if y0 <= (t["box"][1]+t["box"][3])/2 < y1 and ((t["box"][0]+t["box"][2])/2 < midpoint) == left], key=lambda t:t["box"][1])
            colchars = [c for c in remaining if c["id"] not in used and y0 <= center(c)[1] < y1 and (center(c)[0] < local_midpoint(center(c)[1])) == left]
            local_cursor = y0
            for table in local_tables:
                part = [c for c in colchars if local_cursor <= center(c)[1] < table["box"][3]]
                if part:
                    out.append(render_prose(part, number)); used.update(c["id"] for c in part)
                out.append(table["text"])
                emitted_tables.add(table["table_index"])
                local_cursor = table["box"][3]
            part = [c for c in colchars if c["id"] not in used and center(c)[1] >= local_cursor]
            if part:
                out.append(render_prose(part, number)); used.update(c["id"] for c in part)
    for event in global_events:
        if event["box"][1] < cursor-0.2:
            FLAGS.append({"page": number, "kind": "overlapping_layout_events", "bbox": event["box"]})
            continue
        emit_band(cursor, event["box"][1])
        if "text" in event:
            out.append(event["text"])
            emitted_tables.add(event["table_index"])
        else:
            ec = [c for c in event["chars"] if c["id"] not in used]
            if ec:
                out.append(render_prose(ec, number)); used.update(c["id"] for c in ec)
        cursor = max(cursor, event["box"][3])
    emit_band(cursor, rec["height"])
    for table in table_events:
        if table["table_index"] not in emitted_tables:
            FLAGS.append({"page":number,"kind":"unrendered_table","table":table["table_index"]})
    used.update(c["id"] for c in body if not c["text"].strip())
    unused = [c for c in body if c["id"] not in used]
    if unused:
        FLAGS.append({"page": number, "kind": "unplaced_text", "count": len(unused), "text": plain(unused), "ids": [c["id"] for c in unused]})
        out.append("<!-- Positioned source fragment requiring reading-order review -->\n\n"+render_prose(unused, number))
        used.update(c["id"] for c in unused)
    PAGE_CHECKS.append({"page": number, "body_chars": len(body), "used_chars": len(used), "printed": printed, "tables":len(table_events), "column_midpoint":midpoint})
    text="\n\n".join(s for s in out if s.strip())
    verify_payload(body,text,number)
    return printed,text


def main():
    input_path = WORK / "pages-corrected.jsonl"
    if not input_path.exists():input_path = WORK / "pages.jsonl"
    opener = open
    if not input_path.exists():
        input_path=WORK/"pages-corrected.jsonl.gz"
        opener=gzip.open
    if not input_path.exists():
        input_path = WORK / "pages.jsonl.gz"
        opener = gzip.open
    with opener(input_path, "rt", encoding="utf-8") as source, OUT.open("w", encoding="utf-8") as target:
        target.write("# ACKS II Revised Rulebook\n\n")
        target.write("<!-- English working transcription. Page headings and bracketed damage labels are editorial navigation/transcription aids, not additions to the rules. -->\n\n")
        for line in source:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                break
            printed, text = page_text(rec)
            number = rec["page"]
            label = f"PDF page {number}" + (f" printed page {printed}" if printed else "")
            target.write(f'<a id="pdf-page-{number:04d}"></a>\n\n## {label}\n\n')
            target.write(f"[Original PDF page {number}](ACKSII%20Revised%20Rulebook.pdf#page={number})\n\n")
            target.write(text+"\n\n")
            COUNTS["pages"] += 1
            if number % 50 == 0:
                print(f"BUILD {number} pages", flush=True)
    (WORK / "build-checks.json").write_text(json.dumps({"counts": dict(COUNTS), "pages": PAGE_CHECKS, "flags": FLAGS}, ensure_ascii=False, indent=2), encoding="utf-8")
    (WORK / "tables.json").write_text(json.dumps(TABLES, ensure_ascii=False), encoding="utf-8")
    (WORK / "hyphen-joins.json").write_text(json.dumps(HYPHENS,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"counts":dict(COUNTS),"flags":collections.Counter(f["kind"] for f in FLAGS),"output":str(OUT)},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
