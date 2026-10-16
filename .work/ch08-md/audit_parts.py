"""Audit all saved ranges before the final contiguous merge."""
import json,re
from pathlib import Path
from collections import Counter
from build_chapter import plain,numbers
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=[json.loads(s) for s in (ROOT/'contributions/08/source.jsonl').read_text('utf-8').splitlines()]
initial=HERE/'initial_fragment.json'
texts=json.loads((initial if initial.exists() else HERE/'styled.json').read_text('utf-8'))
for part in (HERE/'parts').glob('*/translations.json'):
    texts.update(json.loads(part.read_text('utf-8')))
issues=[]
latin={}
for u in source:
    if u['id'] not in texts:continue
    ru=plain(texts[u['id']])
    en=u['english']
    if Counter(numbers(en))!=Counter(numbers(ru)):
        issues.append({'id':u['id'],'kind':'numeric','en':numbers(en),'ru':numbers(ru),'english':en,'russian':ru})
    if en.count('*')!=ru.count('*'):
        issues.append({'id':u['id'],'kind':'emphasis','en':en.count('*'),'ru':ru.count('*'),'english':en,'russian':ru})
    words=re.findall(r'[A-Za-z][A-Za-z\-]{2,}',re.sub('<[^>]*>','',ru))
    if words:latin[u['id']]=words
result={'units':len(texts),'missing':[u['id'] for u in source if u['id'] not in texts],'issues':issues,'latin':latin}
(HERE/'parts_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Units',len(texts),'missing',len(result['missing']),'issues',len(issues))
print(json.dumps(issues,ensure_ascii=False,indent=2))
print('LATIN',json.dumps(latin,ensure_ascii=False))
