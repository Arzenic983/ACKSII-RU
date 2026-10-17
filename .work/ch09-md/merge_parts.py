"""Merge disjoint contributor ranges in immutable source order; no DB writes."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text('utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')
source=[json.loads(x) for x in (ROOT/'contributions/09/source.jsonl').read_text('utf-8').splitlines()]
texts=read(HERE/'styled.json')
notes=read(HERE/'notes.json')
seen=set()
for part in sorted((HERE/'parts').glob('*/translations.json')):
    incoming=read(part)
    a,b=(list(map(int,re.findall(r'\d+',part.parent.name)))+[None])[:2]
    b=b or a
    assert set(incoming)=={u['id'] for u in source if a<=u['pdf_page']<=b},(part,'incomplete range')
    assert not seen.intersection(incoming),(part,'overlapping contributor ranges')
    seen.update(incoming)
    texts.update(incoming)
    for k,v in read(part.with_name('notes.json')).items():
        assert k in incoming
        notes[k]=re.sub(r'^\*\s*','',v)
ordered={u['id']:texts[u['id']] for u in source if u['id'] in texts}
assert set(ordered)==set(texts)
assert list(ordered)==[u['id'] for u in source[:len(ordered)]],'Untranslated gap: wait for the earlier range'
save(HERE/'styled.json',ordered)
save(HERE/'notes.json',notes)
print('Merged',len(ordered),'of',len(source),'units')
