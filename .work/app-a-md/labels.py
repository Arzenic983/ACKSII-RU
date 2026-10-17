"""Display-only labels, reversible without altering the Russian translation."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RULES=[s.split('\t') for s in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if s]
# Full language names precede adjectives. Names in lists are paired separately.
LANG=[]
for s in (HERE/'language_nodes.tsv').read_text('utf-8').splitlines():
    if not s:continue
    _,en,ru,_=s.split('\t')
    ru=ru.replace('*','');en=en.replace('*','')
    if '(и т. п.)' not in ru:
        words=ru.split();pat=' '.join(re.escape(w[:-2])+r'[а-яё]*' if w.endswith(('ий','ый')) else re.escape(w) for w in words)
        LANG.append((pat,en,ru))
names=[]
ru_units=dict(s.split('\t',1) for s in (HERE/'translations.tsv').read_text('utf-8').splitlines() if s)
for line in (ROOT/'contributions/A/source.jsonl').read_text('utf-8').splitlines():
    u=json.loads(line)
    if re.match(r'^\*\*(Male Names|Female Names|Surnames):',u['english']):
        for ru,en in zip(ru_units[u['id']].split('** ',1)[1].split(', '),u['english'].split('** ',1)[1].split(', ')):
            endings={'а':r'(?:а|ы|е|у|ой|ою|ам|ами|ах)','я':r'(?:я|и|е|ю|ей|ею|ям|ями|ях)','й':r'(?:й|я|ю|ем|е|и|ев|ям|ями|ях)','ь':r'(?:ь|я|ю|ем|е|и|ью)'}
            if ru[-1] in endings:pat=re.escape(ru[:-1])+endings[ru[-1]]
            elif ru[-1] in 'иуоэ':pat=re.escape(ru)
            else:pat=re.escape(ru)+r'(?:а|у|ом|е|ы|ов|ам|ами|ах)?'
            names.append(('(?-i:'+pat+')',en,ru))
# Manual multiword terms win over individual names; longest names win over
# shorter names with the same beginning. English insertions are never rescanned.
RULES=[r for r in RULES if ' ' in r[0]]+LANG+[r for r in RULES if ' ' not in r[0]]+sorted(set(names),key=lambda x:-len(x[0]))
PATTERN=re.compile(r'(?<!\w)(?:'+'|'.join(f'(?P<t{i}>{pat})' for i,(pat,en,ru) in enumerate(RULES))+r')(?!\w)',re.I)
def decorate(s):
    shadow=[];positions=[]
    for i,c in enumerate(s):
        if c=='*':continue
        shadow.append(c);positions.append(i)
    additions=[]
    for m in PATTERN.finditer(''.join(shadow)):
        en=RULES[int(m.lastgroup[1:])][1];at=positions[m.end()-1]+1
        if positions[m.start()]>0 and s[positions[m.start()]-1]=='[' and s[at:at+1]==']':at+=1
        additions.append((at,' ['+en+']'))
    for at,label in reversed(additions):s=s[:at]+label+s[at:]
    return s
def undecorate(s):return re.sub(r' \[([A-Za-z][^\]\n]*)\]','',s)
