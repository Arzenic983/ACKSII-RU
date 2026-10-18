"""Independent rendered-text and whole-repository preservation check."""
import hashlib,json,sqlite3,subprocess,sys,re
from collections import Counter
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.work/ch08-md'))
from validate_final import UnitText,normalized,mechanics
sys.path.insert(0,str(HERE))
from build_fragment import numbers
rows=[json.loads(s) for s in (ROOT/'contributions/09/translator.jsonl').read_text('utf-8').splitlines()]
assert 33<=len(rows)<=3179 and all(u['revision']==0 and u['status'] in ('draft','reviewed') for u in rows)
md=(ROOT/'ACKSII/Перевод Markdown/09 Армии.md').read_text('utf-8')
node='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
rendered=subprocess.run([node,str(ROOT/'.work/ch02-md/render_document.mjs')],input=md,text=True,encoding='utf-8',capture_output=True,check=True).stdout
parsed=UnitText({u['id'] for u in rows if re.search(r'(?m)^> ',u['russian'])});parsed.feed(rendered)
assert set(parsed.data)=={u['id'] for u in rows}
differences=[]
def compared_text(s):
    # Inline labels disappear before HTML parsing; whitespace around operators
    # may therefore move across a <br> without changing visible rule text.
    return re.sub(r'\s*([+/\-])\s*',r'\1',normalized(s))
for u in rows:
    if compared_text(''.join(parsed.data[u['id']]))!=compared_text(u['russian']):differences.append((u['id'],'rendered',normalized(''.join(parsed.data[u['id']])),normalized(u['russian'])))
    if u['id'].startswith('rr.p0441.t01.') and u['id'].endswith('.c08') and re.fullmatch(r'D[01]',u['english']):
        assert u['russian']=='Д'+u['english'][1:],u['id'] # Dwarf class/level, not a zero/one-sided die.
    else:
        # BW means By Weapon; BW+1 is a signed modifier even when adjacent.
        en=re.sub(r'\bBW(?=[+\-])',' ',u['english'])
        ru=re.sub(r'По\s+оружию',' ',u['russian'])
        if mechanics(en)!=mechanics(ru):differences.append((u['id'],'mechanics',u['english'],u['russian']))
    assert Counter(numbers(u['english']))==Counter(numbers(u['russian'])),u['id']
(HERE/'render_differences.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2)+'\n','utf-8')
assert not differences,differences[:3]
baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
integrated=(HERE/'integration.json').exists()
with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    if integrated:
        with sqlite3.connect((HERE/'before_chapter09.sqlite.tmp').resolve().as_uri()+'?mode=ro',uri=True) as old:
            assert db.execute("SELECT * FROM bilingual WHERE chapter_id!='09' ORDER BY id").fetchall()==old.execute("SELECT * FROM bilingual WHERE chapter_id!='09' ORDER BY id").fetchall()
        db.row_factory=sqlite3.Row
        for u in rows:
            current=db.execute('SELECT * FROM bilingual WHERE id=?',(u['id'],)).fetchone()
            assert current['revision']==1 and current['russian']==u['russian'] and current['status']==u['status'],u['id']
        db.row_factory=None
    else:
        assert digest(db.execute('SELECT * FROM bilingual ORDER BY id').fetchall())==baseline['all_bilingual_sha256']
    assert digest(db.execute('SELECT * FROM units ORDER BY id').fetchall())==baseline['source_units_sha256']
    assert digest(db.execute('SELECT * FROM source_tables ORDER BY id').fetchall())==baseline['source_tables_sha256']
    table_rows={}
    for table,r,c,text,uid in db.execute("SELECT table_id,row_index,column_index,english,id FROM bilingual WHERE chapter_id='09' AND kind='table_cell'"):
        table_rows.setdefault(table,{}).setdefault(r,{})[c]=(text,uid)
    field_cost_rows=0
    for table,trs in table_rows.items():
        if table not in ('rr.p0444.t01','rr.p0445.t01','rr.p0446.t01'):continue
        for r,cells in trs.items():
            if r==0 or not all(c in cells for c in (3,4,5,6)):continue
            values={c:Decimal(cells[c][0].replace(',','').replace('gp','')) for c in (3,4,5,6)}
            assert values[3]+4*values[4]+values[5]==values[6],cells[0][1]
            field_cost_rows+=1
    assert field_cost_rows==75
    arithmetic=[]
    for r,cells in table_rows['rr.p0433.t02'].items():
        if r==0:continue
        def gp(c):
            text=cells[c][0].replace(',','')
            return Decimal(re.search(r'[\d.]+',text)[0])/(10 if 'sp' in text else 1)
        value=gp(2)+gp(3)+gp(4)
        if value!=gp(5):arithmetic.append({'id':cells[5][1],'sum_gp':str(value),'listed_gp':str(gp(5))})
    assert {x['id'] for x in arithmetic}=={f'rr.p0433.t02.r{r:03}.c06' for r in (6,18,19,21)}
    assert all(x['id'] in json.loads((HERE/'notes.json').read_text('utf-8')) for x in arithmetic)
for name,sha in baseline['protected'].items():
    if Path(name).name=='Примечания редактора.md':continue # New chapter09 notes are appended explicitly.
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
editorial=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md'
marker='\n\n## Глава 9. Армии — PDF 428–447'.encode('utf-8')
editorial_before=editorial.read_bytes().split(marker,1)[0]
expected_editorial=next(v for k,v in baseline['protected'].items() if Path(k).name==editorial.name)
assert hashlib.sha256(editorial_before).hexdigest()==expected_editorial
p=ROOT/'ACKSII/База перевода/09_validation.json'
report=json.loads(p.read_text('utf-8'))
report['checks'].update(rendered_text_matches_package=True,dice_percentages_signed_modifiers=True,entire_database_unchanged=not integrated,other_chapters_unchanged=True,immutable_sources_and_tables_unchanged=True,previous_full_chapters_and_readers_unchanged=True,integrated_text_and_status_match=integrated)
if integrated:report['database_translations']=26976
report['checks']['previous_editorial_notes_bytes_preserved']=True
report['field_cost_formula_rows_checked']=field_cost_rows
report['source_training_cost_discrepancies_preserved']=arithmetic
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'rendered_fragment.html').write_text(rendered,'utf-8')
print(len(rows),'rendered units match package; mechanics, immutable sources, previous translations and Markdown preserved; integrated:',integrated)
