"""Display-only terms and bilingual placeholders; preserve Russian brackets."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
RULES=[s.split('\t') for s in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if s]
PATTERN=re.compile(r'(?<!\w)(?:'+'|'.join(f'(?P<t{i}>{p})' for i,(p,en) in enumerate(RULES))+r')(?!\w)',re.I)
def plain(s):
    def repl(m):
        if re.match(r'\s*\[[A-Za-z#]',s[m.end():]):return m[0]
        return m[0]+' ['+RULES[int(m.lastgroup[1:])][1]+']'
    return PATTERN.sub(repl,s)
def decorate(s,english=''):
    placeholders=iter(re.findall(r'\[[A-Za-z][^]\n]*\]',english))
    result=[]
    for part in re.split(r'(\[[^]\n]+\])',s):
        if part.startswith('['):
            result.append(part)
            if re.match(r'\[[А-Яа-яЁё]',part):
                label=next(placeholders,None)
                if label:result.append(' '+label)
        else:result.append(plain(part))
    return ''.join(result)
def undecorate(s):return re.sub(r' \[([A-Za-z#][^]\n]*)\]','',s)
