from pathlib import Path
import re
p=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
s=dict(pat.findall((p/'source_B.md').read_text(encoding='utf-8-sig')))
t=dict(pat.findall((p/'translated_B.md').read_text(encoding='utf-8-sig')))
for u,v in s.items():
 if len(v)<=100:
  print(u+' EN '+v.strip()+' | RU '+t[u].strip())
