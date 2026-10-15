from pathlib import Path
import re, sqlite3, json, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd()
work=root/'.work/ch02-md'
pattern=r'<!-- unit: ([^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)'
src=dict(re.findall(pattern,(work/'source_C.md').read_text(encoding='utf-8'),re.S))
dst=dict(re.findall(pattern,(work/'translated_C.md').read_text(encoding='utf-8'),re.S))
print('source',len(src),'translated',len(dst),'missing', sorted(src.keys()-dst.keys()),'extra',sorted(dst.keys()-src.keys()))
print('duplicate count',len(re.findall(r'<!-- unit:',(work/'translated_C.md').read_text(encoding='utf-8')))-len(dst))
for key, val in src.items():
    if key not in dst: continue
    n1=re.findall(r'\d+(?:\.\d+|,\d+)*(?:d\d+)?',val)
    n2=re.findall(r'\d+(?:\.\d+|,\d+)*(?:d\d+)?',dst[key])
    if Counter(n1)!=Counter(n2): print('NUM',key,n1,n2)
db=root/'ACKSII/База перевода/acksii_translation.sqlite'
c=sqlite3.connect(db.as_uri()+'?mode=ro', uri=True)
print('style sample', c.execute('select id, russian from bilingual where pdf_page between 16 and 23 and length(russian)>250 limit 5').fetchall())
c.close()
