"""Extend the reviewed reader builder; keep every previous preservation check."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
p=ROOT/'.work/reading-md/format_reading.py'
s=p.read_text('utf-8')
if "LAST_PAGE = 333" in s:
    s=s.replace('1–7','1–8').replace("'07 Плавания.md')]","'07 Плавания.md', '08 Кампании.md')]")
    s=s.replace('LAST_PAGE = 333','LAST_PAGE = 427').replace('EXPECTED_TABLES = 221','EXPECTED_TABLES = 300')
    s=s.replace("    317: ('Плавания', 'VOYAGES'),","    317: ('Плавания', 'VOYAGES'),\n    335: ('Кампании', 'CAMPAIGNS'),")
    s=s.replace('[1234567]','[12345678]')
    s=s.replace("            ('7. Плавания', '7 VOYAGES', 'Глава 7. Плавания', 'CHAPTER 7: VOYAGES'),","            ('7. Плавания', '7 VOYAGES', 'Глава 7. Плавания', 'CHAPTER 7: VOYAGES'),\n            ('8. Кампании', '8 CAMPAIGNS', 'Глава 8. Кампании', 'CHAPTER 8: CAMPAIGNS'),")
    s=s.replace('(8, 14, 24, 102, 124, 180, 264, 316)','(8, 14, 24, 102, 124, 180, 264, 316, 334)')
    s=s.replace("'7. Плавания': 'Глава 7. Плавания'","'7. Плавания': 'Глава 7. Плавания', '8. Кампании': 'Глава 8. Кампании'")
    s=s.replace("('7 VOYAGES', 'CHAPTER 7: VOYAGES')):","('7 VOYAGES', 'CHAPTER 7: VOYAGES'), ('8 CAMPAIGNS', 'CHAPTER 8: CAMPAIGNS')):")
    at=s.index('    css = ')
    proof="""    previous7 = result.split('<p align="right" id="pdf-page-0334">', 1)[0]
    previous7 = re.sub(r'\\n---\\s*$', '', previous7).rstrip() + '\\n'
    previous7 = previous7.replace('Начало и главы 1–8', 'Начало и главы 1–7', 1).replace('FRONT MATTER AND CHAPTERS 1–8', 'FRONT MATTER AND CHAPTERS 1–7', 1)
    assert previous7 == (OUT / 'ACKS II — Начало и главы 1–7.md').read_text('utf-8'), 'Previously completed reader pages 5–333 changed'
"""
    s=s[:at]+proof+s[at:]
    s=s.replace("'previous_reader_pages_5_315_unchanged': True,","'previous_reader_pages_5_315_unchanged': True,\n        'previous_reader_pages_5_333_unchanged': True,")
    s=s.replace("'date': '2026-10-16'","'date': '2026-10-17'")
md=(ROOT/'ACKSII/Перевод Markdown/08 Кампании.md').read_text('utf-8')
count=sum(line.startswith('> ') for line in md.splitlines())
s=re.sub(r'EXPECTED_NOTES = \d+',f'EXPECTED_NOTES = {501+count}',s)
assert "'08 Кампании.md'" in s and 'LAST_PAGE = 427' in s
p.write_text(s,'utf-8')
print('Reader target1–8; total tables300; expected notes',501+count)
