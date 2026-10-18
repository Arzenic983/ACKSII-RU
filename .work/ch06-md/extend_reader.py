"""Adapt the inspected reader builder once, keeping its existing preservation gates."""
from common import HERE,ROOT,read
p=ROOT/'.work/reading-md/format_reading.py'
s=p.read_text('utf-8')
assert "LAST_PAGE = 263" in s
s=s.replace('1–5','1–6').replace("'05 Заклинания.md')","'05 Заклинания.md', '06 Приключения.md')")
s=s.replace('LAST_PAGE = 263','LAST_PAGE = 315').replace('EXPECTED_TABLES = 175','EXPECTED_TABLES = 208')
n=sum(map(len,read('notes.json').values()))
s=s.replace('EXPECTED_NOTES = 434',f'EXPECTED_NOTES = {434+n}')
s=s.replace("    181: ('Заклинания', 'SPELLS'),","    181: ('Заклинания', 'SPELLS'),\n    265: ('Приключения', 'ADVENTURES'),")
s=s.replace('[12345]','[123456]')
s=s.replace("            ('5. Заклинания', '5 SPELLS', 'Глава 5. Заклинания', 'CHAPTER 5: SPELLS'),","            ('5. Заклинания', '5 SPELLS', 'Глава 5. Заклинания', 'CHAPTER 5: SPELLS'),\n            ('6. Приключения', '6 ADVENTURES', 'Глава 6. Приключения', 'CHAPTER 6: ADVENTURES'),")
s=s.replace('(8, 14, 24, 102, 124, 180)','(8, 14, 24, 102, 124, 180, 264)')
s=s.replace("'5. Заклинания': 'Глава 5. Заклинания'","'5. Заклинания': 'Глава 5. Заклинания', '6. Приключения': 'Глава 6. Приключения'")
s=s.replace("('5 SPELLS', 'CHAPTER 5: SPELLS')):","('5 SPELLS', 'CHAPTER 5: SPELLS'), ('6 ADVENTURES', 'CHAPTER 6: ADVENTURES')):")
anchor="    css = 'body{font:17px"
addition='''    previous5 = result.split('<p align="right" id="pdf-page-0264">', 1)[0]
    previous5 = re.sub(r'\\n---\\s*$', '', previous5).rstrip() + '\\n'
    previous5 = previous5.replace('Начало и главы 1–6', 'Начало и главы 1–5', 1).replace('FRONT MATTER AND CHAPTERS 1–6', 'FRONT MATTER AND CHAPTERS 1–5', 1)
    old5 = (OUT / 'ACKS II — Начало и главы 1–5.md').read_text('utf-8')
    assert previous5 == old5, 'Previously completed reader pages 5–263 changed'
'''
assert anchor in s;s=s.replace(anchor,addition+anchor)
s=s.replace("        'previous_reader_pages_5_179_unchanged': True,","        'previous_reader_pages_5_179_unchanged': True,\n        'previous_reader_pages_5_263_unchanged': True,\n        'previous_reader_1_5_sha256_normalized_newlines': hashlib.sha256(previous5.encode()).hexdigest(),")
p.write_text(s,'utf-8');print('Reader extended; notes',434+n)
