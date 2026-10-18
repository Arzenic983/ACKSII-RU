"""Read-only independent checks of the current RR database, chapters and reader."""
from pathlib import Path
from collections import Counter, defaultdict
from html.parser import HTMLParser
from urllib.parse import unquote
import csv, hashlib, html, importlib.util, json, os, re, sqlite3, subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
NODE=os.environ.get('ACKS_NODE') or 'C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
RENDER=ROOT/'.work/ch02-md/render_document.mjs'
SAIL_LEGEND='Подписи схемы: ветер [Wind]; крутой бейдевинд [Close Hauled] ×1/3; галфвинд [Beam Reach] ×1/2; бакштаг [Broad Reach] ×2/3; фордевинд [Run] ×1; лавировка [Tacking] ×2/9. Угол между направлением против ветра и каждым курсом крутого бейдевинда [Close Hauled] — 30°.'

def render(md):
    return subprocess.run([NODE,str(RENDER)],input=md,text=True,encoding='utf-8',capture_output=True,check=True).stdout

class DOM(HTMLParser):
    def __init__(self):
        super().__init__();self.active=None;self.texts={};self.ids=[];self.skip=0
        self.table=None;self.tables=[];self.row=None;self.cell=None;self.part=None;self.parts={}
    def start_unit(self,uid):
        self.active=uid if re.fullmatch(r'rr\.p\d{4}\.(?:b\d{3}|t\d{2}\.r\d{3}\.c\d{2})',uid) else None
        if self.active:self.texts.setdefault(uid,'')
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('small','blockquote','sup','script','style'):self.skip+=1
        if tag in ('br','p','div','li') and self.active and not self.skip:self.texts[self.active]+=' '
        if 'id' in a:
            self.ids.append(a['id'])
            if a['id'].startswith(('rr.','pdf-page-')):self.start_unit(a['id'])
        if tag=='table':self.table=[];self.tables.append(self.table)
        if tag=='tr':self.row=[];self.table.append(self.row)
        if tag in ('td','th'):
            self.cell={'id':a.get('id'),'rowspan':int(a.get('rowspan',1)),'colspan':int(a.get('colspan',1))};self.row.append(self.cell)
        if tag=='a' and self.cell is not None and a.get('id','').startswith('rr.'):self.cell['id']=a['id']
        if tag=='span' and 'data-unit' in a:
            self.part=(a['data-unit'],int(a['data-part']));assert self.part not in self.parts
            self.parts[self.part]=''
    def handle_endtag(self,tag):
        if tag in ('small','blockquote','sup','script','style'):self.skip-=1
        if tag in ('td','th'):self.cell=None;self.active=None
        if tag=='tr':self.row=None
        if tag=='table':self.table=None
        if tag=='span' and self.part is not None:self.part=None;self.active=None
    def handle_data(self,s):
        if self.skip:return
        if self.part:self.parts[self.part]+=s
        elif self.active:self.texts[self.active]+=s

def normalize(s):
    s=html.unescape(s)
    s=re.sub(r'\s*\[(?=[^\[\]]*[A-Za-z])[^\[\]А-Яа-яЁё]*\]','',s)
    s=re.sub(r'(?<=атак)\s*AT\b','',s,flags=re.I)
    s=re.sub(r'(?<=атак)\s*# of Attacks\b','',s,flags=re.I)
    s=re.sub(r'\s+',' ',s).strip()
    # Compare letters and digits without Markdown emphasis and presentation punctuation.
    return ''.join(re.findall(r'[А-Яа-яЁёA-Za-z0-9]',s)).lower()

def main():
    db=sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    spec=importlib.util.spec_from_file_location('rr_database_tools',BASE/'database_tools.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result={'date':'2026-10-18','database':module.verify(db)}
    units=[dict(u) for u in db.execute('SELECT * FROM bilingual ORDER BY pdf_page,block_order,row_index,column_index,id')]
    byid={u['id']:u for u in units};chapters=[dict(u) for u in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')]
    assert len(units)==30624 and all(u['russian'] and u['russian'].strip() for u in units)
    assert all(u['status']=='reviewed' for u in units)
    exported=[json.loads(s) for s in (BASE/'units.jsonl').read_text('utf-8').splitlines()]
    assert exported==units,'JSONL differs from database'
    assert json.loads((BASE/'progress.json').read_text('utf-8'))==chapters
    result['chapter_csv_missing']=[];result['chapter_csv_differences']=[]
    for ch in chapters:
        csv_path=BASE/(ch['id']+'_review.csv')
        if not csv_path.exists():result['chapter_csv_missing'].append(ch['id']);continue
        with csv_path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=';'))
        expected=[u for u in units if u['chapter_id']==ch['id']]
        assert [u['id'] for u in rows]==[u['id'] for u in expected]
        for u,e in zip(rows,expected):
            for k in ('english','russian','revision','status','note','source_sha256'):
                if u[k].replace('\r\n','\n')!=('' if e[k] is None else str(e[k])).replace('\r\n','\n'):
                    result['chapter_csv_differences'].append({'id':e['id'],'field':k,'csv':u[k],'database':e[k]})
    result['exports_match_database']=True
    checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
    for p in range(1,551):
        segment=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
        body=segment.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip()
        body=re.sub(r'\n---\s*$','',body).strip()
        assert body==db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip(),p
    result['EN_checked_pages_equal_database']=550
    # Render all base Russian texts through the same Markdown parser, without annotations.
    def isolated_ru(u):
        text=u['russian']
        if text.startswith('>'):text='&gt;'+text[1:]
        return f'<a id="{u["id"]}"></a>\n\n'+text
    expected_parser=DOM();expected_parser.feed(render('\n\n'.join(isolated_ru(u) for u in units)))
    result['chapters']=[];differences=[];all_notes=[];documented=[]
    for ch in chapters:
        file=OUT/('00 Начало.md' if ch['id']=='front_matter' else ch['id']+' '+ch['title_ru']+'.md')
        md=file.read_text('utf-8');actual=DOM();actual.feed(render(md))
        us=[u for u in units if u['chapter_id']==ch['id']];ids=[u['id'] for u in us]
        assert set(actual.texts)==set(ids),(ch['id'],set(ids)-set(actual.texts))
        assert len(actual.ids)==len(set(actual.ids)),('duplicate',ch['id'])
        assert [int(s) for s in re.findall(r'<a id="pdf-page-(\d+)"></a>',md)]==list(range(ch['first_pdf_page'],ch['last_pdf_page']+1))
        for uid in {ref[0] for ref in actual.parts}:
            actual.texts[uid]=' '.join(value for ref,value in sorted(actual.parts.items()) if ref[0]==uid)
        for u in us:
            a=normalize(actual.texts[u['id']]);e=normalize(expected_parser.texts[u['id']])
            # Ordered-list markers can be HTML counter labels or escaped literal text.
            prefix=re.match(r'^(\d+)\.',u['russian'])
            if prefix and a==prefix[1]+e:a=e
            if u['kind']=='heading' and re.fullmatch(r'\d+'+re.escape(e),a):a=e
            if u['id']=='rr.p0320.b013' and a==e+normalize(SAIL_LEGEND):
                documented.append({'id':u['id'],'source_sha256':u['source_sha256'],'extra_visible_text':SAIL_LEGEND,'reason':'Русская легенда исходного изображения схемы; все 5 множителей и угол сверены с изображением PDF 320. Текст базовой единицы сохранён полностью.'});a=e
            if a!=e:differences.append({'id':u['id'],'actual':actual.texts[u['id']],'expected':expected_parser.texts[u['id']]})
        tables=[dict(t) for t in db.execute('SELECT * FROM source_tables WHERE chapter_id=? ORDER BY pdf_page,block_order,id',(ch['id'],))]
        assert len(actual.tables)==len(tables)
        empty=0
        for rows,t in zip(actual.tables,tables):
            assert len(rows)==t['row_count'],t['id'];grid=set();starts={}
            for r,row in enumerate(rows):
                c=0
                for cell in row:
                    while (r,c) in grid:c+=1
                    starts[r,c]=cell
                    for ri in range(r,r+cell['rowspan']):
                        for ci in range(c,c+cell['colspan']):
                            assert (ri,ci) not in grid,t['id'];grid.add((ri,ci))
                    c+=cell['colspan']
            assert grid=={(r,c) for r in range(t['row_count']) for c in range(t['column_count'])},t['id']
            expected={(u['row_index'],u['column_index']):u for u in us if u['table_id']==t['id']}
            for pos,cell in starts.items():
                if pos not in expected:assert cell['id'] is None;empty+=1
                else:
                    u=expected[pos]
                    assert (cell['id'],cell['rowspan'],cell['colspan'])==(u['id'],u['rowspan'] or 1,u['colspan'] or 1),u['id']
        all_notes.extend(line for line in md.splitlines() if line.startswith('> '))
        result['chapters'].append({'id':ch['id'],'file':str(file.relative_to(ROOT)),'pdf_pages':[ch['first_pdf_page'],ch['last_pdf_page']],
            'unit_range':[ids[0],ids[-1]],'units':len(us),'tables':len(tables),'empty_cells_without_id':empty,'notes':sum(s.startswith('> ') for s in md.splitlines())})
    (HERE/'render_differences.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2)+'\n','utf-8')
    result['render_comparison_candidates']=len(differences)
    result['documented_render_additions']=documented
    result['tables_geometry_verified']=sum(ch['tables'] for ch in result['chapters'])
    result['notes_in_full_chapters']=len(all_notes)
    result['limits']='Структурная проверка и нормализованное сопоставление отображаемого текста не являются новой полной смысловой или визуальной вычиткой.'
    (HERE/'structural_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not differences,'Unexplained rendered text differences'
    assert not result['chapter_csv_missing'] and not result['chapter_csv_differences'],'Chapter exports differ'
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
