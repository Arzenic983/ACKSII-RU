import sqlite3, json
from pathlib import Path
c=sqlite3.connect('file:ACKSII/База перевода/acksii_translation.sqlite?mode=ro',uri=True)
for row in c.execute("select id, russian from bilingual where pdf_page<=23 and lower(english) like '% xp%' limit 6"):
 print(row)
for x in json.loads(Path('ACKSII/База перевода/glossary.json').read_text(encoding='utf-8-sig')):
 if x.get('term_en','').lower() in ('exp','experience','experience points','lawful','chaotic','hit points','hit dice','sunder','overrun'):
  print(x)
