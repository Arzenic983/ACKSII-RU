"""Extend reviewed reader builder to chapter09 without weakening earlier checks."""
from pathlib import Path
import re,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=ROOT/'.work/reading-md/format_reading.py'
s=p.read_text('utf-8')
if 'LAST_PAGE = 427' in s:
    s=s.replace('1–8','1–9').replace("'08 Кампании.md')]","'08 Кампании.md', '09 Армии.md')]")
    s=s.replace('LAST_PAGE = 427','LAST_PAGE = 447')
    s=s.replace("    335: ('Кампании', 'CAMPAIGNS'),", "    335: ('Кампании', 'CAMPAIGNS'),\n    429: ('Армии', 'ARMIES'),")
    s=s.replace('[12345678]','[123456789]')
    s=s.replace("            ('8. Кампании', '8 CAMPAIGNS', 'Глава 8. Кампании', 'CHAPTER 8: CAMPAIGNS'),","            ('8. Кампании', '8 CAMPAIGNS', 'Глава 8. Кампании', 'CHAPTER 8: CAMPAIGNS'),\n            ('9. Армии', '9 ARMIES', 'Глава 9. Армии', 'CHAPTER 9: ARMIES'),")
    s=s.replace('(8, 14, 24, 102, 124, 180, 264, 316, 334)','(8, 14, 24, 102, 124, 180, 264, 316, 334, 428)')
    s=s.replace("'8. Кампании': 'Глава 8. Кампании'","'8. Кампании': 'Глава 8. Кампании', '9. Армии': 'Глава 9. Армии'")
    s=s.replace("('8 CAMPAIGNS', 'CHAPTER 8: CAMPAIGNS')):","('8 CAMPAIGNS', 'CHAPTER 8: CAMPAIGNS'), ('9 ARMIES', 'CHAPTER 9: ARMIES')):")
    at=s.index('    css = ')
    proof="""    previous8 = result.split('<p align="right" id="pdf-page-0428">', 1)[0]
    previous8 = re.sub(r'\\n---\\s*$', '', previous8).rstrip() + '\\n'
    previous8 = previous8.replace('Начало и главы 1–9', 'Начало и главы 1–8', 1).replace('FRONT MATTER AND CHAPTERS 1–9', 'FRONT MATTER AND CHAPTERS 1–8', 1)
    assert previous8 == (OUT / 'ACKS II — Начало и главы 1–8.md').read_text('utf-8'), 'Previously completed reader pages 5–427 changed'
"""
    s=s[:at]+proof+s[at:]
    s=s.replace("'previous_reader_pages_5_333_unchanged': True,","'previous_reader_pages_5_333_unchanged': True,\n        'previous_reader_pages_5_427_unchanged': True,")
md=(ROOT/'ACKSII/Перевод Markdown/09 Армии.md').read_text('utf-8')
validation=json.loads((ROOT/'ACKSII/База перевода/09_validation.json').read_text('utf-8'))
assert validation['chapter_complete'] and validation['translated_units']==3179
count=sum(line.startswith('> ') for line in md.splitlines())
tables=md.count('<table ')
assert tables==validation['tables_in_fragment']
s=re.sub(r'EXPECTED_NOTES = \d+',f'EXPECTED_NOTES = {578+count}',s)
s=re.sub(r'EXPECTED_TABLES = \d+',f'EXPECTED_TABLES = {300+tables}',s)
assert "'09 Армии.md'" in s and 'LAST_PAGE = 447' in s
p.write_text(s,'utf-8')
print('Reader target1–9; tables',300+tables,'notes',578+count)
