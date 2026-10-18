"""One-time preparation of appendix-specific checks from inspected chapter checks."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=(ROOT/'.work/ch12-md/audit.py').read_text('utf-8').replace('contributions/12/','contributions/A/')
(HERE/'audit.py').write_text(s,'utf-8')
s=(ROOT/'.work/ch11-md/validate.py').read_text('utf-8')
for a,b in [('contributions/11/','contributions/A/'),('11 Сражения.md','A Сеттинг.md'),("chapter_id='11'","chapter_id='A'"),("chapter_id!='11'","chapter_id!='A'"),('range(462,474)','range(488,508)'),('==630','==364'),('==618','==344'),("==42+sum","==40+sum"),("'chapter':'11'","'chapter':'A'"),("'pdf_pages':[462,473]","'pdf_pages':[488,507]"),("'units':618","'units':344"),("'table_count':11","'table_count':2"),("all_12_checked_dump","all_20_checked_dump"),("BASE/'11_validation.json'","BASE/'A_validation.json'")]:
    assert a in s,a
    s=s.replace(a,b)
s=s.replace("assert b['russian'].strip() and b['status']=='reviewed'","assert b['russian'].strip() and b['status']==('reviewed' if (HERE/'semantic_review.json').exists() else 'draft')")
(HERE/'validate.py').write_text(s,'utf-8')
(HERE/'source_display_fixes.json').write_text('{}\n','utf-8')
p=HERE/'translations.tsv';s=p.read_text('utf-8').replace('Зака́ру','Закару').replace('С Никеею','С Никеей').replace('Таксмаcпада','Таксмаспада').replace('Кародaр','Кародар');p.write_text(s,'utf-8')
p=HERE/'table_rows.json';s=p.read_text('utf-8').replace('зверолюдей','зверолюдов').replace('зверолюдьми','зверолюдами');p.write_text(s,'utf-8')
print('Prepared checks; no database mutation')
