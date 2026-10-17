"""Reversible display labels, including terms split by original table breaks."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
RULES=[s.split('\t') for s in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if s]
PATTERN=re.compile(r'(?<!\w)(?:'+'|'.join(f'(?P<t{i}>{p})' for i,(p,en) in enumerate(RULES))+r')(?!\w)',re.I)
def decorate(s,english=''):
    shadow=[];positions=[]
    for token in re.finditer(r'<[^>]*>|\*|.',s,re.S):
        v=token[0]
        if v=='*':continue
        if v.startswith('<'):
            if v.lower()=='<br>':shadow.append(' ');positions.append(token.end()-1)
            continue
        shadow.append(v);positions.append(token.start())
    additions=[]
    for m in PATTERN.finditer(''.join(shadow)):
        en=RULES[int(m.lastgroup[1:])][1]
        if en=='notable scarring' and 'noticeable scarring' in english:en='noticeable scarring'
        at=positions[m.end()-1]+1
        if re.match(r'\s*\[[A-Za-z]',s[at:]):continue
        if positions[m.start()]>0 and s[positions[m.start()]-1]=='[' and s[at:at+1]==']':at+=1
        additions.append((at,' ['+en+']'))
    for at,label in reversed(additions):s=s[:at]+label+s[at:]
    return s
def undecorate(s):return re.sub(r' \[([A-Za-z][^\]\n]*)\]','',s)
