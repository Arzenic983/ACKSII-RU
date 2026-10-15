from pathlib import Path
import re,sys
p=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
s=dict(pat.findall((p/'source_B.md').read_text(encoding='utf-8-sig')))
t=dict(pat.findall((p/'translated_B.md').read_text(encoding='utf-8-sig')))
a,b=map(int,sys.argv[1:3])
for u,v in s.items():
 if a<=int(u[4:8])<=b and len(v)>100:
  print(u+'\nEN '+v+'\nRU '+t[u]+'\n')
