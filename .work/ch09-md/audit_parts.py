"""Read-only contributor audit; list mechanical and untranslated-text candidates."""
import json,re
from pathlib import Path
from collections import Counter
from build_fragment import plain,numbers
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source={u['id']:u for u in (json.loads(s) for s in (ROOT/'contributions/09/source.jsonl').read_text('utf-8').splitlines())}
results={}
for p in (HERE/'parts').glob('*/translations.json'):
    texts=json.loads(p.read_text('utf-8'));issues=[];latin=Counter()
    for uid,styled in texts.items():
        u=source[uid];ru=plain(styled)
        if Counter(numbers(u['english']))!=Counter(numbers(ru)):issues.append((uid,'numbers',u['english'],ru))
        if u['english'].count('*')!=ru.count('*'):issues.append((uid,'emphasis',u['english'],ru))
        stripped=re.sub(r'\b(?:\d+)?d\d+\b','',re.sub('<[^>]*>',' ',ru))
        for word in re.findall('[A-Za-z]+',stripped):latin[word]+=1
    results[p.parent.name]={'units':len(texts),'issues':issues,'remaining_latin':dict(latin)}
(HERE/'parts_audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
