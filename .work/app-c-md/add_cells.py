"""Append manually translated ID<TAB>Russian pairs from stdin by exact English."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
source={u['id']:u for u in map(json.loads,(HERE.parents[1]/'contributions/C/source.jsonl').read_text('utf-8').splitlines())}
p=HERE/'cell_terms.tsv'
existing=dict(s.split('\t',1) for s in p.read_text('utf-8').splitlines() if s)
incoming=Path(sys.argv[1]).read_text('utf-8') if len(sys.argv)>1 else sys.stdin.read()
(HERE/'incoming_cells.tsv.tmp').write_text(incoming,'utf-8')
added=[];issues=[]
for line in incoming.splitlines():
    if not line:continue
    uid,ru=line.split('\t',1);u=source[uid];en=u['english']
    assert u['kind']=='table_cell',uid
    if en.count('<br>')!=ru.count('<br>'):
        issues.append((uid,en.count('<br>'),ru.count('<br>')))
    if en in existing:
        if existing[en]!=ru:issues.append((uid,'existing translation differs'))
        continue
    existing[en]=ru;added.append(en+'\t'+ru)
assert not issues,issues
with p.open('a',encoding='utf-8',newline='\n') as f:
    f.write('\n'.join(added)+'\n' if added else '')
print('Added',len(added),'exact English entries')
