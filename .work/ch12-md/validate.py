"""Independent rendered text, table grid, database and source-file verification."""
from pathlib import Path
from html.parser import HTMLParser
import csv,hashlib,html,json,re,sqlite3,subprocess
from labels import undecorate
from audit import audit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
NODE='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def normalize(s):return re.sub(r'\s+',' ',s).strip()
class Rendered(HTMLParser):
    def __init__(self):
        super().__init__();self.active=None;self.texts={};self.ids=[];self.skip=0;self.table=None;self.tables={};self.row=None;self.cell=None;self.part=None;self.parts={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('small','blockquote','sup'):self.skip+=1
        if tag=='br' and self.active and not self.skip:self.texts[self.active]+=' '
        if tag=='table':self.table=[];self.tables[a['id']]=self.table
        if tag=='tr' and self.table is not None:self.row=[];self.table.append(self.row)
        if tag in ('td','th') and self.row is not None:self.cell={'attrs':a,'id':None};self.row.append(self.cell)
        if tag=='a' and 'id' in a:
            self.ids.append(a['id']);self.active=a['id'] if a['id'].startswith('rr.') else None
            if self.active:
                self.texts[self.active]=''
                if self.cell is not None:self.cell['id']=self.active
        if tag=='span' and 'data-unit' in a:
            self.part=(a['data-unit'],int(a['data-part']))
            assert self.part not in self.parts,'Duplicated fragment'
            self.parts[self.part]=''
    def handle_endtag(self,tag):
        if tag in ('small','blockquote','sup'):self.skip-=1
        if tag in ('td','th'):self.cell=None
        if tag=='tr':self.row=None
        if tag=='table':self.table=None
        if tag=='span' and self.part is not None:self.part=None;self.active=None
    def handle_data(self,data):
        if self.part and not self.skip:self.parts[self.part]+=data
        elif self.active and not self.skip:self.texts[self.active]+=data
def main():
    assert not audit(),'Unresolved mechanical differences'
    source=[json.loads(s) for s in (ROOT/'contributions/12/source.jsonl').read_text('utf-8').splitlines()]
    rows=[json.loads(s) for s in (ROOT/'contributions/12/translator.jsonl').read_text('utf-8').splitlines()]
    package={r['id']:r for r in rows}
    md=(ROOT/'ACKSII/Перевод Markdown/12 Осады.md').read_text('utf-8')
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    rendered=subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=md,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    parser=Rendered();parser.feed(rendered)
    assert set(parser.texts)==set(package)
    expected_order=[r['id'] for r in rows if r['pdf_page']!=480]
    assert [uid for uid in parser.texts if not uid.startswith('rr.p0480.')]==expected_order
    display_order=[f'rr.p0480.b{n:03}' for n in [1,2,3,4,5,6,7,8,9,19,21,22,24,18,27,25,28,29,10,11,12,13,14,15,16,17,20,23,26,30]]
    assert [uid for uid in parser.texts if uid.startswith('rr.p0480.')]==display_order
    parts=json.loads((HERE/'presentation_parts.json').read_text('utf-8'))
    expected_parts={(u['id'],i):text for u in rows if u['pdf_page']==480 for i,text in enumerate(parts.get(u['id'],[u['russian']]))}
    assert set(parser.parts)==set(expected_parts)
    for ref,text in expected_parts.items():assert normalize(undecorate(parser.parts[ref]))==normalize(text.replace('*','')),(ref,text,parser.parts[ref])
    for uid in display_order:
        parser.texts[uid]=' '.join(parser.parts[(uid,i)] for i in range(len(parts.get(uid,[package[uid]['russian']]))))
    assert len(parser.ids)==len(set(parser.ids))==823
    text_mismatches=[]
    for u in rows:
        actual=normalize(undecorate(parser.texts[u['id']]))
        expected=html.unescape(u['russian']).replace(r'\*','\ue000')
        expected=normalize(re.sub(r'<br\s*/?>',' ',expected).replace('*','').replace('\ue000','*'))
        if actual!=expected:text_mismatches.append({'id':u['id'],'expected':expected,'actual':actual})
    (HERE/'render_differences.json').write_text(json.dumps(text_mismatches,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not text_mismatches,'Rendered text mismatch: '+str(text_mismatches[:2])
    integrated=(HERE/'integration.json').exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='12'")}
        tables={r['id']:dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='12'")}
        assert digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='12' ORDER BY id")])==baseline['other_chapters']
        for t,old in baseline['immutable_tables'].items():assert digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')])==old,t
        # The prepared dump is the primary English source. Every complete page
        # body is checked, not just a few words or a fresh OCR extraction.
        checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
        checked_pages={}
        for p in range(474,488):
            segment=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
            body=segment.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip()
            body=re.sub(r'\n---\s*$','',body).strip()
            expected=db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip()
            assert body==expected,('Checked dump differs',p)
            checked_pages[p]=hashlib.sha256(body.encode()).hexdigest()
    assert set(parser.tables)==set(tables)
    for tid,trs in parser.tables.items():
        t=tables[tid];assert len(trs)==t['row_count'];grid=set();actual_ids=[]
        for r,tr in enumerate(trs):
            c=0
            for td in tr:
                while (r,c) in grid:c+=1
                rs=int(td['attrs'].get('rowspan',1));cs=int(td['attrs'].get('colspan',1))
                if td['id']:
                    m=meta[td['id']];actual_ids.append(td['id'])
                    assert (r,c,rs,cs)==(m['row_index'],m['column_index'],m['rowspan'],m['colspan']),td['id']
                for rr in range(r,r+rs):
                    for cc in range(c,c+cs):
                        assert (rr,cc) not in grid
                        grid.add((rr,cc))
                c+=cs
        assert grid=={(r,c) for r in range(t['row_count']) for c in range(t['column_count'])}
        assert actual_ids==[u['id'] for u in source if meta[u['id']]['table_id']==tid]
    for a,b in zip(source,rows):
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','revision','source_sha256'):
            assert a[k]==b[k],(a['id'],k)
        review=HERE/'semantic_review.json'
        expected_status='reviewed' if review.exists() and json.loads(review.read_text('utf-8'))['complete_semantic_review_by_Codex'] else 'draft'
        assert b['russian'].strip() and b['status']==expected_status
        if integrated:
            expected_revision=json.loads((HERE/'integration.json').read_text('utf-8')).get('revisions',{}).get(b['id'],b['revision']+1)
            assert meta[b['id']]['russian']==b['russian'] and meta[b['id']]['revision']==expected_revision
    with (ROOT/'contributions/12/translator.csv').open(encoding='utf-8-sig',newline='') as f:csv_rows=list(csv.DictReader(f,delimiter=';'))
    assert len(csv_rows)==len(rows)==809
    for a,b in zip(csv_rows,rows):assert all(a[k]==('' if v is None else str(v)) for k,v in b.items())
    for path,old in baseline['protected_files'].items():
        backup=HERE/'editor_notes_before.tmp'
        if path.endswith('Примечания редактора.md') and backup.exists():
            assert hashlib.sha256(backup.read_bytes()).hexdigest()==old
            assert (ROOT/path).read_text('utf-8').startswith(backup.read_text('utf-8'))
        else:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==old,path
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    assert sum(s.startswith('> ') for s in md.splitlines())==len(notes)
    assert md.count('<small>')==44+sum(1 for td in re.findall('<th(?: [^>]*)?>.*?</th>',md,re.S))
    result={'date':'2026-10-17','chapter':'12','pdf_pages':[474,487],'units':809,'table_count':9,'editor_notes':len(notes),'checks':{'all_rendered_russian_units_match_package':True,'all_table_grids_and_spans_match_database':True,'csv_jsonl_roundtrip':True,'ids_source_hashes_and_original_revision_preserved':True,'other_chapters_and_immutable_database_tables_unchanged':True,'previous_chapters_and_reader_files_unchanged':True,'editor_notes_previous_prefix_preserved':True,'all_14_checked_dump_page_bodies_equal_database_source':True,'numeric_dice_percent_signed_modifier_math_emphasis_and_break_invariants':True,'no_user_approval_assigned':True},'checked_source_page_sha256':checked_pages,'integrated':integrated}
    visual=HERE/'visual_review.json'
    result['documented_source_display_fixes']=json.loads((HERE/'source_display_fixes.json').read_text('utf-8'))
    en_parts=json.loads((HERE/'source_parts.json').read_text('utf-8'))
    for uid,fragments in en_parts.items():assert ' '.join(fragments)==package[uid]['english'],uid
    result['page480_reconstruction']={'rendered_fragments':len(parser.parts),'every_fragment_rendered_once':True,'all_fragment_texts_match_original_unit_translation':True,'all_english_parts_rejoin_unchanged_source_units':True,'display_order_checked_against_pdf':True,'nested_zones':4,'new_source_tables_created':0}
    if visual.exists():result['visual_review']=json.loads(visual.read_text('utf-8'))
    (BASE/'12_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checked_source_page_sha256','visual_review')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
