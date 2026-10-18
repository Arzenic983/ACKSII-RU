"""Check all numeric, dice, percent, emphasis and line-break invariants."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def numeric(s,russian=False):
    s=re.sub('<[^>]*>','',s)
    s=re.sub(r'(?<=\d)'+(r'[ \u00a0]' if russian else r'[,\u00a0]')+r'(?=\d{3}(?:\D|$))','',s)
    return [n.replace(',','.') for n in re.findall(r'\d+(?:[.,]\d+)?',s)]
def audit():
    rows=[json.loads(s) for s in (ROOT/'contributions/C/source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'))
    fixes=json.loads((HERE/'source_display_fixes.json').read_text('utf-8'))
    differences=[]
    for u in rows:
        en=u['english'];ru=pure[u['id']];issues={}
        numeric_en=en
        if u['id'] in fixes and 'numeric_source' in fixes[u['id']]:
            assert en==fixes[u['id']]['original']
            numeric_en=fixes[u['id']]['numeric_source']
        if numeric(numeric_en)!=numeric(ru,True):issues['numbers']=[numeric(numeric_en),numeric(ru,True)]
        if en.count('*')!=ru.count('*'):issues['emphasis_counts']=[en.count('*'),ru.count('*')]
        if len(re.findall(r'<br\s*/?>',en))!=len(re.findall(r'<br\s*/?>',ru)):issues['line_breaks']=[en,ru]
        for name,pat in [('dice',r'\d+[dD]\d+(?:[+-]\d+)?'),('percentages',r'\d+%'),('explicit_signed_modifiers',r'(?<![\w\d])[+-]\d+'),('threshold_suffixes',r'\d+[+-](?!\w)'),('multiplication_and_division',r'(?<=[\d)])\s*[×/=](?=\s*[\d(])')]:
            a=re.findall(pat,en);b=re.findall(pat,ru)
            a=[v.strip() for v in a];b=[v.strip() for v in b]
            if a!=b:issues[name]=[a,b]
        if issues:differences.append({'id':u['id'],'differences':issues})
    (HERE/'mechanics_differences.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(differences,ensure_ascii=False,indent=2))
    return differences
if __name__=='__main__':audit()
