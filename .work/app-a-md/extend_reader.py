"""One-time reader-scope update, with preservation of every previous range."""
from pathlib import Path
import json,re,shutil
from labels import decorate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==344 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 487' in s:
        replacements={
          "TARGET = OUT / 'ACKS II — Начало и главы 1–12.md'":"TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложение A.md'",
          "'12 Осады.md')]":"'12 Осады.md', 'A Сеттинг.md')]",
          'LAST_PAGE = 487':'LAST_PAGE = 507','EXPECTED_NOTES = 654':'EXPECTED_NOTES = 674','EXPECTED_TABLES = 351':'EXPECTED_TABLES = 353',
          "    475: ('Осады', 'SIEGES'),":"    475: ('Осады', 'SIEGES'),\n    489: ('Сеттинг', 'SETTING'),",
          "r'\\n# Глава (?:[1-9]|10|11|12)\\. '":"r'\\n# (?:Глава (?:[1-9]|10|11|12)\\. |Приложение A\\. )'",
          "            ('12. Осады', '12 SIEGES', 'Глава 12. Осады', 'CHAPTER 12: SIEGES'),":"            ('12. Осады', '12 SIEGES', 'Глава 12. Осады', 'CHAPTER 12: SIEGES'),\n            ('A. Сеттинг', 'A SETTING', 'Приложение A. Сеттинг', 'APPENDIX A: SETTING'),",
          '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488)',
          "'12. Осады': 'Глава 12. Осады'":"'12. Осады': 'Глава 12. Осады', 'A. Сеттинг': 'Приложение A. Сеттинг'",
          "('12 SIEGES', 'CHAPTER 12: SIEGES')):":"('12 SIEGES', 'CHAPTER 12: SIEGES'), ('A SETTING', 'APPENDIX A: SETTING')):",
          "    TARGET.write_text(result, 'utf-8')\n":"",
          "'previous_reader_pages_5_473_unchanged': True,":"'previous_reader_pages_5_473_unchanged': True,\n        'previous_reader_pages_5_487_unchanged': True,\n        'appendix_a_language_trees_and_illustrations_preserved': True,",
          '<title>ACKS II — главы 1–12</title>':'<title>ACKS II — главы 1–12 и приложение A</title>'
        }
        for a,b in replacements.items():assert a in s,a;s=s.replace(a,b)
        proof='''    previous12 = result.split('<p align="right" id="pdf-page-0488">', 1)[0]
    previous12 = re.sub(r'\\n---\\s*$', '', previous12).rstrip() + '\\n'
    assert previous12 == (OUT / 'ACKS II — Начало и главы 1–12.md').read_text('utf-8'), 'Previously completed reader pages 5–487 changed'
    assert result.count('class="language-tree"') == 2
    assert result.count('data-depth="') == 116
    for asset in ('appendix-a-map.png', 'appendix-a-siege.png'):
        assert ('assets/' + asset) in result and (OUT / 'assets' / asset).is_file()
    result = result.replace('Начало и главы 1–12', 'Начало, главы 1–12 и приложение A', 1).replace('FRONT MATTER AND CHAPTERS 1–12', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDIX A', 1)
    rendered = rendered.replace('Начало и главы 1–12', 'Начало, главы 1–12 и приложение A', 1).replace('FRONT MATTER AND CHAPTERS 1–12', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDIX A', 1)
    TARGET.write_text(result, 'utf-8')
'''
        at=s.index('    css = ');s=s[:at]+proof+s[at:];p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 507' in s
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    if not backup.exists():
        assert '## Приложение A. Сеттинг' not in target.read_text('utf-8')
        shutil.copyfile(target,backup)
    additions=['','## Приложение A. Сеттинг','','<small>APPENDIX A: SETTING — EDITORIAL NOTES</small>','']
    for uid,note in json.loads((HERE/'notes.json').read_text('utf-8')).items():
        note=re.sub(r'rr\.p\d{4}\.[bt][\w.]+',lambda m:'`'+m[0]+'`',decorate(note))
        additions.extend([f'<!-- unit: {uid} -->',f'`{uid}`: '+note,''])
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader extended: PDF 5–507, 503 page markers, 353 tables, 674 notes')
if __name__=='__main__':main()
