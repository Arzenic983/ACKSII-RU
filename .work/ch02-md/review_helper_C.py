from pathlib import Path
import re, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
w=Path('.work/ch02-md')
pat=r'<!-- unit: ([^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)'
s=dict(re.findall(pat,(w/'source_D.md').read_text(encoding='utf-8'),re.S))
t=dict(re.findall(pat,(w/'translated_D.md').read_text(encoding='utf-8'),re.S))
if len(sys.argv)>1:
    start,end=map(int,sys.argv[1:3])
    for k,v in s.items():
        page=int(k[4:8])
        if start<=page<=end and (len(sys.argv)<4 or re.search(sys.argv[3],k)): print(k+'\nEN '+v.strip()+'\nRU '+t.get(k,'MISSING').strip()+'\n')
else:
    print('SOURCE',len(s),'TRANS',len(t),'MISSING',sorted(s.keys()-t.keys()),'EXTRA',sorted(t.keys()-s.keys()))
    for k,v in s.items():
        if k not in t: continue
        num=lambda x: Counter(re.findall(r'\d+(?:\.\d+|,\d+)*(?:d\d+)?',x))
        if num(v)!=num(t[k]): print('NUM',k,num(v)-num(t[k]),num(t[k])-num(v))
