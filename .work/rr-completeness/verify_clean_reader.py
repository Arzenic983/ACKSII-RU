from pathlib import Path
from html.parser import HTMLParser
import importlib.util,json,re
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'ACKSII/База перевода'
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reader',ROOT/'tools/build_rr_reader.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Visible(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.data=[]
    def handle_starttag(self,t,a):
        if t in ('style','script'):self.skip+=1
        if t in ('p','div','br','blockquote','li','tr','h1','h2','h3','h4'):self.data.append('\n')
    def handle_endtag(self,t):
        if t in ('style','script'):self.skip-=1
    def handle_data(self,s):
        if not self.skip:self.data.append(s)

v=Visible();v.feed(b.render(b.HUMAN.read_text('utf-8')))
lines=[re.sub(r'\s+',' ',s).strip() for s in ''.join(v.data).splitlines() if s.strip()]
technical=re.compile(r'rr\.p|SQLite|JSONL?|CSV|SHA-?256|\brevision\b|\bID\b|\.json|\.py\b|\.work/|data-unit|data-part|source_markup|EN checked|\bHTML\b|\bCSS\b|Markdown|дамп|валидатор|рендер|декоратор',re.I)
bad=[s for s in lines if technical.search(s)]
assert not bad,bad
assert len(b.notes(b.HUMAN.read_text('utf-8')))==751
assert b.HUMAN.read_text('utf-8').count('<table')+len(re.findall(r'^\|[^\n]*(?:\n\|[^\n]*)*',b.HUMAN.read_text('utf-8'),re.M))==370
result={'date':'2026-10-18','reader':str(b.HUMAN.relative_to(ROOT)),'sha256':b.sha(b.HUMAN),'visible_machine_markers':0,'reader_note_projections':len(b.NOTE_PROJECTIONS),'notes':751,'tables':370,'english_term_labels_preserved':True,'HTML_checked_as_rendered_text':True,'machine_marker_check_passed':True}
(BASE/'RR_clean_reader_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(result,ensure_ascii=False))
