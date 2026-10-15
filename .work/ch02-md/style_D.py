from pathlib import Path
import sqlite3,json
c=sqlite3.connect('file:ACKSII/База перевода/acksii_translation.sqlite?mode=ro',uri=True)
for row in c.execute("select id, english, russian from bilingual where pdf_page<=23 and length(russian)>200 order by random() limit 8"):
 print(row)
g=json.loads(Path('ACKSII/База перевода/glossary.json').read_text(encoding='utf-8-sig'))
print(str(g)[:1800])
