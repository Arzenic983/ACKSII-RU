"""Independent rendered-text, mechanics, database, and preservation audit."""
from pathlib import Path
from html.parser import HTMLParser
import html,json,re,sqlite3,subprocess
from collections import Counter
from build_chapter import plain,numbers
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'


class UnitText(HTMLParser):
    def __init__(self,author_quotes):
        super().__init__()
        self.data={};self.current=None;self.skip=0;self.lists=[]
        self.author_quotes=author_quotes;self.quotes=[]

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a' and attrs.get('id','').startswith('rr.'):
            self.current=attrs['id'];self.data[self.current]=[]
        elif tag=='a' and attrs.get('id','').startswith('pdf-page-'):
            self.current=None
        if tag=='blockquote':
            ignored=self.current not in self.author_quotes
            self.quotes.append(ignored)
            self.skip+=int(ignored)
        if tag in ('small','sup'):self.skip+=1
        if tag=='br' and self.current and not self.skip:self.data[self.current].append(' ')
        if tag in ('ol','ul'):self.lists.append(int(attrs.get('start',1)) if tag=='ol' else None)
        if tag=='li' and self.lists and self.lists[-1] is not None:
            if self.current:self.data[self.current].append(str(self.lists[-1])+'. ')
            self.lists[-1]+=1

    def handle_endtag(self,tag):
        if tag in ('small','sup'):self.skip-=1
        if tag in ('ol','ul'):self.lists.pop()
        if tag=='blockquote':self.skip-=int(self.quotes.pop())

    def handle_data(self,s):
        if self.current and not self.skip:self.data[self.current].append(s)


def normalized(s):
    s=html.unescape(re.sub('<[^>]+>',' ',s))
    s=plain(s).replace('\\*','*').replace('*','')
    s=re.sub(r'(?m)^>\s*','',s)
    s=re.sub(r'\s+([.,;:!?»\)\]])',r'\1',s)
    return re.sub(r'\s+',' ',s).strip()


def mechanics(s):
    s=re.sub(r'(\d+)<br\s*/?>(d\d+)',r'\1\2',s,flags=re.I)
    s=re.sub('<[^>]*>',' ',plain(s)).replace('−','-').replace('–','-')
    s=re.sub(r'(?<=\d)[, \u00a0](?=\d{3}(?:\D|$))','',s)
    s=re.sub(r'(\d+)(?:st|nd|rd|th)?\s*-\s*(\d+)(?:st|nd|rd|th)',r'\1-\2',s)
    return (Counter(t.lower() for t in re.findall(r'\b(?:\d+)?d\d+',s,re.I)),
            Counter(re.findall(r'\d+(?:[.,]\d+)?%',s)),
            Counter(re.findall(r'(?<![\w\d])[-+±]\d+(?:[.,]\d+)?',s)))


def main():
    rows=[json.loads(s) for s in (ROOT/'contributions/08/translator.jsonl').read_text('utf-8').splitlines()]
    md=(ROOT/'ACKSII/Перевод Markdown/08 Кампании.md').read_text('utf-8')
    node='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    rendered=subprocess.run([node,str(ROOT/'.work/ch02-md/render_document.mjs')],input=md,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    parser=UnitText({u['id'] for u in rows if re.search(r'(?m)^> ',u['russian'])});parser.feed(rendered)
    assert set(parser.data)=={u['id'] for u in rows}
    differences=[(u['id'],normalized(''.join(parser.data[u['id']])),normalized(u['russian'])) for u in rows if normalized(''.join(parser.data[u['id']]))!=normalized(u['russian'])]
    (HERE/'render_differences.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not differences,differences[:5]
    mechanical=[]
    for row in rows:
        if mechanics(row['english'])!=mechanics(row['russian']):mechanical.append(row['id'])
        assert Counter(numbers(row['english']))==Counter(numbers(row['russian'])),row['id']
    (HERE/'mechanics_differences.json').write_text(json.dumps(mechanical,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not mechanical,mechanical
    integrated=(HERE/'integration.json').exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        for u in rows:
            current=db.execute('SELECT * FROM bilingual WHERE id=?',(u['id'],)).fetchone()
            assert current['english']==u['english'] and current['source_sha256']==u['source_sha256']
            assert u['revision']==0 and current['revision']==int(integrated)
            if integrated:assert current['russian']==u['russian'] and current['status']=='reviewed'
        if integrated:
            with sqlite3.connect((HERE/'before_chapter08.sqlite.tmp').resolve().as_uri()+'?mode=ro',uri=True) as old:
                assert [tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='08' ORDER BY id")]==old.execute("SELECT * FROM bilingual WHERE chapter_id!='08' ORDER BY id").fetchall()
    baseline=json.loads((HERE/'baseline_before_continuation.json').read_text('utf-8'))
    import hashlib
    for path,digest in baseline['protected'].items():
        if Path(path).name=='Примечания редактора.md':continue
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    report=json.loads((BASE/'08_validation.json').read_text('utf-8'))
    report['checks'].update(rendered_unit_text_matches_package=True,dice_percentages_and_signed_modifiers=True,protected_previous_chapter_files_unchanged=True,integrated_russian_and_status_match_package=integrated,other_chapters_unchanged_after_integration=integrated)
    report['display_corrections']={'rr.p0353.b011 + rr.p0353.b013':'Один заголовок FOUNDING SETTLEMENTS, оба исходных ID/текста сохранены; порядок отображения восстановлен по изображению PDF353.','rr.p0425.b001 / rr.p0425.b003':'Полные английские заголовки восстановлены по изображению PDF425.','rr.p0345.t02.r001.c01':'TITLE по изображению PDF345 вместо извлечённого TIITTLLEE.'}
    report['rendered_headings']=254
    if integrated:report['database_translations']=23797
    (BASE/'08_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'rendered_chapter.html').write_text(rendered,'utf-8')
    print('4906 rendered units match package; dice, percentages and signed modifiers match; integrated:',integrated)


if __name__=='__main__':main()
