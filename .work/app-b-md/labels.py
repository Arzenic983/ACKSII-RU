"""Appendix-B display labels; shared glossary names use source context."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
RULES=[s.split('\t') for p in ('term_rules.tsv','condition_rules.tsv') for s in (HERE/p).read_text('utf-8').splitlines() if s]
PATTERN=re.compile(r'(?<!\w)(?:'+'|'.join(f'(?P<t{i}>{p})' for i,(p,en) in enumerate(RULES))+r'|(?P<ambiguous>тряс[а-яё]*))(?!\w)',re.I)
def decorate(s,english=''):
    shadow=[];positions=[]
    for i,c in enumerate(s):
        if c=='*':continue
        shadow.append(c);positions.append(i)
    additions=[]
    for m in PATTERN.finditer(''.join(shadow)):
        en=('shaken' if re.search(r'\bshaken\b',english,re.I) else 'cowering') if m.lastgroup=='ambiguous' else RULES[int(m.lastgroup[1:])][1]
        at=positions[m.end()-1]+1
        if re.match(r'\s*\[[A-Za-z]',s[at:]):continue
        if positions[m.start()]>0 and s[positions[m.start()]-1]=='[' and s[at:at+1]==']':at+=1
        additions.append((at,' ['+en+']'))
    for at,label in reversed(additions):s=s[:at]+label+s[at:]
    return s
def undecorate(s):return re.sub(r' \[([A-Za-z][^\]\n]*)\]','',s)
