"""Independently verify rendered E, references, sources and protected chapters."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter,defaultdict
from urllib.parse import unquote
import csv,hashlib,html,json,re,sqlite3,subprocess
from audit import audit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
NODE='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def normalize(s):
    s=re.sub(r'\\([_*])',r'\1',s).replace('*','')
    return re.sub(r'\s+',' ',s).strip()
class Rendered(HTMLParser):
    def __init__(self):super().__init__();self.active=None;self.skip=0;self.texts={};self.ids=[];self.index_links=[];self.index_entries=0;self.tables=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('small','blockquote','sup'):self.skip+=1
        if tag in ('br','p','div') and self.active and not self.skip:self.texts[self.active]+=' '
        if tag=='table':self.tables+=1
        if tag=='a' and 'id' in a:
            self.ids.append(a['id']);self.active=a['id'] if a['id'].startswith('rr.') else None
            if self.active:self.texts[self.active]=''
        if tag=='a' and '#pdf-page-' in a.get('href',''):self.index_links.append((a['href'],a.get('title')))
    def handle_endtag(self,tag):
        if tag in ('small','blockquote','sup'):self.skip-=1
    def handle_data(self,data):
        if self.active and not self.skip:self.texts[self.active]+=data
def main():
    assert not audit()
    source=[json.loads(s) for s in (ROOT/'contributions/E/source.jsonl').read_text('utf-8').splitlines()]
    rows=[json.loads(s) for s in (ROOT/'contributions/E/translator.jsonl').read_text('utf-8').splitlines()]
    package={u['id']:u for u in rows};assert len(rows)==len(package)==83
    md=(ROOT/'ACKSII/Перевод Markdown/E Предметный указатель.md').read_text('utf-8')
    rendered=subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=md,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    parser=Rendered();parser.feed(rendered)
    assert set(parser.texts)==set(package) and len(parser.ids)==len(set(parser.ids))==96
    assert parser.tables==0 and md.count('<small>')==30
    mismatches=[]
    for uid,actual in parser.texts.items():
        if int(uid[4:8])>=545:actual=re.sub(r' \[[A-Za-z][^]\n]*\]','',actual)
        elif uid=='rr.p0539.b002':actual=actual.replace(' [Adventurer Conqueror King System Imperial Imprint]','').replace(' [Auran Empire]','')
        if normalize(actual)!=normalize(package[uid]['russian']):mismatches.append({'id':uid,'expected':normalize(package[uid]['russian']),'actual':normalize(actual)})
    (HERE/'render_differences.json').write_text(json.dumps(mismatches,ensure_ascii=False,indent=2)+'\n','utf-8');assert not mismatches,str(mismatches[:1])
    integrated=(HERE/'integration.json').exists();baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='E'")}
        assert digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='E' ORDER BY id")])==baseline['other_chapters']
        for t,h in baseline['immutable_tables'].items():assert digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')])==h,t
        checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
        for p in range(538,551):
            segment=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
            body=segment.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip();body=re.sub(r'\n---\s*$','',body).strip()
            assert body==db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip(),p
        pages={r['printed_page']:r['pdf_page'] for r in db.execute('SELECT printed_page,pdf_page FROM pages WHERE printed_page IS NOT NULL')}
    for a,b in zip(source,rows):
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256','revision'):assert a[k]==b[k]
        assert hashlib.sha256(a['english'].encode()).hexdigest()==a['source_sha256']
        assert b['status']==('reviewed' if (HERE/'semantic_review.json').exists() else 'draft')
        if integrated:assert meta[b['id']]['russian']==b['russian'] and meta[b['id']]['revision']==b['revision']+1
        if 539<=a['pdf_page']<=544 and a['kind']=='paragraph' and a['id']!='rr.p0539.b002':assert a['english']==b['russian'],a['id']
    with (ROOT/'contributions/E/translator.csv').open(encoding='utf-8-sig',newline='') as f: csvrows=list(csv.DictReader(f,delimiter=';'))
    assert len(csvrows)==83
    for a,b in zip(csvrows,rows):assert all(a[k]==('' if v is None else str(v)) for k,v in b.items())
    entries=json.loads((HERE/'index_entries.json').read_text('utf-8'));assert len(entries)==862
    for e in entries:assert '['+html.escape(e['english'])+'] — ' in md,e['english']
    assert sum(len(re.findall(r'\d+',e['pages'])) for e in entries)==len(parser.index_links)==975
    for href,title in parser.index_links:
        n,physical=map(int,re.findall(r'\d+',title));assert pages[n]==physical
        assert href.endswith(f'#pdf-page-{physical:04}')
        assert unquote(href.split('#',1)[0])=='ACKS II — Начало, главы 1–12 и приложения A–E.md'
    assert md.count('class="index-block"')==24
    for u in source:
        if u['kind']=='heading' and u['id'] not in ('rr.p0548.b002','rr.p0548.b005'):assert '<small>'+html.escape(u['english'])+'</small>' in md,u['id']
    assert '<small>REVERSED SPELL INDEX</small>' in md
    page548=md.split('<a id="pdf-page-0548"></a>',1)[1].split('<a id="pdf-page-0549"></a>',1)[0]
    assert [m for m in re.findall(r'<!-- unit: (rr\.[^ ]+) -->',page548)]==['rr.p0548.b001','rr.p0548.b004','rr.p0548.b005','rr.p0548.b002','rr.p0548.b003','rr.p0548.b006']
    for name,h in baseline['protected_files'].items():
        if name.endswith('Примечания редактора.md') and integrated:
            backup=HERE/'editor_notes_before.tmp'
            if backup.exists():
                old=backup.read_bytes();assert hashlib.sha256(old).hexdigest()==h
                assert (ROOT/name).read_text('utf-8').startswith(old.decode('utf-8').replace('\r\n','\n'))
            else:
                current=(ROOT/name).read_bytes();heading='## Приложение E. Предметный указатель'.encode()
                sep=(b'\r\n' if b'\r\n'+heading in current else b'\n')+heading
                assert current.count(sep)==1 and hashlib.sha256(current.split(sep,1)[0]).hexdigest()==h
        else:assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    notes=json.loads((HERE/'notes.json').read_text('utf-8'));assert len(notes)==sum(s.startswith('> ') for s in md.splitlines())==10
    report={'date':'2026-10-18','chapter':'E','pdf_pages':[538,550],'units':83,'source_headings':30,'rendered_source_heading_blocks':29,'index_entries':862,'index_page_links':975,'tables':0,'editorial_notes':10,'integrated':integrated,'checks':{'all_rendered_russian_units_match_package':True,'all_original_index_references_preserved':True,'all_printed_to_pdf_page_links_verified':True,'backer_names_and_signatures_preserved_exactly':True,'csv_jsonl_roundtrip':True,'ids_source_hashes_and_original_revision_preserved':True,'all_13_EN_checked_page_bodies_equal_database':True,'other_chapters_and_immutable_tables_unchanged':True,'previous_full_chapters_and_readers_unchanged':True,'no_user_approval_assigned':True,'reversed_spell_heading_and_block_order_restored_in_presentation':True},'documented_source_display_fixes':json.loads((HERE/'source_display_fixes.json').read_text('utf-8'))}
    if (HERE/'visual_review.json').exists():report['visual_review']=json.loads((HERE/'visual_review.json').read_text('utf-8'))
    (BASE/'E_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('documented_source_display_fixes','visual_review')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
