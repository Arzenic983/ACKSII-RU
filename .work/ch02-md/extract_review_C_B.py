from pathlib import Path
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
source=pat.findall((root/'source_C.md').read_text(encoding='utf-8'))
target=dict(pat.findall((root/'translated_C.md').read_text(encoding='utf-8')))
first,last=map(int,sys.argv[1:3])
print('TOTAL',len(source),'RANGE',first,last)
for idx,(uid,en) in enumerate(source,1):
 if first<=idx<=last:
  print(f'\n{idx}. {uid}\nEN: {en.strip()}\nRU: {target.get(uid,"[MISSING]").strip()}')
