"""List chapter terminology and candidate invariant cells for manual translation."""
from pathlib import Path
from collections import defaultdict,Counter
import json
import re
import sqlite3
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    tables=json.loads((HERE/'source_tables.json').read_text('utf-8'))
    db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    previous=defaultdict(set)
    for en,ru in db.execute("SELECT english,russian FROM bilingual WHERE russian IS NOT NULL"):
        previous[en].add(ru)
    exact={en:next(iter(values)) for en,values in previous.items() if len(values)==1}
    numeric={}
    words=defaultdict(list)
    for u in units:
        en=u['source_markup']
        if u['table_id']:
            if not re.search('[A-Za-z]',en):numeric[u['id']]=en
            elif en in exact and len(en)<100:numeric[u['id']]=exact[en]
            else:words[en].append(u['id'])
    (HERE/'previous_exact.json').write_text(json.dumps(exact,ensure_ascii=False,indent=2),'utf-8')
    out=[]
    for t in tables:
        chosen=[u for u in units if u['table_id']==t['id'] and u['source_markup'] in words]
        out.append('## '+t['id']+' '+str(t['row_count'])+'×'+str(t['column_count']))
        seen=set()
        for u in chosen:
            en=u['source_markup']
            if en not in seen:out.append(en)
            seen.add(en)
    (HERE/'table_terms.txt').write_text('\n'.join(out),'utf-8')
    descriptions=[u for u in units if not u['table_id'] and u['kind']!='heading']
    (HERE/'body_source.md').write_text('\n\n'.join(f'<!-- unit: {u["id"]} -->\n{u["source_markup"]}' for u in descriptions),'utf-8')
    print('numeric/existing table units',len(numeric),'distinct remaining strings',len(words),'body units',len(descriptions))
    print('\n'.join(out[:130]))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
