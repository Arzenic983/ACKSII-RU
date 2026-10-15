from pathlib import Path
import re,sys
p=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
s=dict(pat.findall((p/'pending_A.md').read_text(encoding='utf-8-sig')))
t=dict(pat.findall((p/'translated_A_42_45.md').read_text(encoding='utf-8-sig')))
a,b=map(int,sys.argv[1:3])
for u,v in t.items():
 if a<=int(u[4:8])<=b:
  print(u+'\nEN '+s[u]+'\nRU '+v+'\n')
print('MATCHING TARGET COUNT',len(t))
