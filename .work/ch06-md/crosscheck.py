from common import ROOT,HERE
import sqlite3,re,sys
sys.stdout.reconfigure(encoding='utf-8')
db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
us=[dict(r) for r in db.execute("SELECT * FROM units WHERE chapter_id='03' ORDER BY pdf_page,block_order,row_index,column_index,id")]
targets={'BRIBERY','ENDURANCE','CLIMBING','MOUNTAINeERING'.upper(),'PRECISE SHOOTING','RIDING','MOUNTED COMBAT'}
parts=[]
for i,u in enumerate(us):
    if u['kind']=='heading' and u['source_plain'] in targets:
        j=i+1
        while j<len(us) and us[j]['kind']!='heading':j+=1
        parts.extend(x['id']+' | '+x['source_markup'] for x in us[i:j] if not x['table_id'])
for r in db.execute("SELECT * FROM units WHERE chapter_id='04' AND (source_plain LIKE '%Impact%' OR source_plain LIKE '%Long Bow%' OR source_plain LIKE '%Longbow%') ORDER BY pdf_page,block_order"):
    parts.append(r['id']+' | '+r['source_markup'])
    if r['table_id']:
        parts.extend(x['id']+' | '+x['source_markup'] for x in db.execute('SELECT * FROM units WHERE table_id=? AND row_index=? ORDER BY column_index',(r['table_id'],r['row_index'])))
text='\n\n'.join(parts);(HERE/'cross_chapter_sources.md').write_text(text,'utf-8');print(text)
