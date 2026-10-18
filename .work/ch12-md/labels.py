"""English display labels; never used to rewrite SQLite source or Russian text."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
RULES=[line.split('\t') for line in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if line]
# All alternatives run once, so inserted labels cannot be relabeled. Long phrase
# rules precede their component words. Index mapping handles split emphasis runs.
PATTERN=re.compile(r'(?<![\w])(?:'+'|'.join(f'(?P<t{i}>{pat})' for i,(pat,en,ru) in enumerate(RULES))+r')(?![\w])',re.I)
def decorate(s):
    shadow=[];positions=[]
    for i,c in enumerate(s):
        if c=='*':continue
        shadow.append(c);positions.append(i)
    additions=[]
    for m in PATTERN.finditer(''.join(shadow)):
        en=RULES[int(m.lastgroup[1:])][1]
        at=positions[m.end()-1]+1
        if positions[m.start()]>0 and s[positions[m.start()]-1]=='[' and s[at:at+1]==']':at+=1
        additions.append((at,' ['+en+']'))
    for at,label in reversed(additions):s=s[:at]+label+s[at:]
    return s
def undecorate(s):
    return re.sub(r" \[([A-Za-z][A-Za-z0-9 ,;:/().'’\-]+)\]",'',s)
