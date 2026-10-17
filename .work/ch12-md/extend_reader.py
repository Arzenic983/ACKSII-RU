"""Extend the reader through chapter 12 and append the editor-note summary."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==809 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 473' in s:
        s=s.replace('1–11','1–12')
        replacements={
            "'11 Сражения.md')]":"'11 Сражения.md', '12 Осады.md')]",
            'LAST_PAGE = 473':'LAST_PAGE = 487','EXPECTED_NOTES = 633':'EXPECTED_NOTES = 654','EXPECTED_TABLES = 342':'EXPECTED_TABLES = 351',
            "    463: ('Сражения', 'BATTLES'),":"    463: ('Сражения', 'BATTLES'),\n    475: ('Осады', 'SIEGES'),",
            '(?:[1-9]|10|11)':'(?:[1-9]|10|11|12)',
            "            ('11. Сражения', '11 BATTLES', 'Глава 11. Сражения', 'CHAPTER 11: BATTLES'),":"            ('11. Сражения', '11 BATTLES', 'Глава 11. Сражения', 'CHAPTER 11: BATTLES'),\n            ('12. Осады', '12 SIEGES', 'Глава 12. Осады', 'CHAPTER 12: SIEGES'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474)',
            "'11. Сражения': 'Глава 11. Сражения'":"'11. Сражения': 'Глава 11. Сражения', '12. Осады': 'Глава 12. Осады'",
            "('11 BATTLES', 'CHAPTER 11: BATTLES')):":"('11 BATTLES', 'CHAPTER 11: BATTLES'), ('12 SIEGES', 'CHAPTER 12: SIEGES')):",
            "    text = re.sub(r' id=\"rr\\.[^\"]+\"', '', text)":"    text = re.sub(r' id=\"rr\\.[^\"]+\"', '', text)\n    text = re.sub(r' data-(?:unit|part)=\"[^\"]*\"', '', text)",
        }
        for old,new in replacements.items():assert old in s,old;s=s.replace(old,new)
        proof='''    previous11 = result.split('<p align="right" id="pdf-page-0474">', 1)[0]
    previous11 = re.sub(r'\\n---\\s*$', '', previous11).rstrip() + '\\n'
    previous11 = previous11.replace('Начало и главы 1–12', 'Начало и главы 1–11', 1).replace('FRONT MATTER AND CHAPTERS 1–12', 'FRONT MATTER AND CHAPTERS 1–11', 1)
    assert previous11 == (OUT / 'ACKS II — Начало и главы 1–11.md').read_text('utf-8'), 'Previously completed reader pages 5–473 changed'
'''
        at=s.index('    css = ');s=s[:at]+proof+s[at:]
        s=s.replace("'previous_reader_pages_5_461_unchanged': True,","'previous_reader_pages_5_461_unchanged': True,\n        'previous_reader_pages_5_473_unchanged': True,")
        p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 487' in s
    notes=json.loads((HERE/'styled_notes.json').read_text('utf-8'))
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    if not backup.exists():
        assert '## Глава 12. Осады' not in target.read_text('utf-8')
        shutil.copyfile(target,backup)
    additions=['','## Глава 12. Осады','','<small>CHAPTER 12: SIEGES — EDITORIAL NOTES</small>','']
    for uid,note in notes.items():additions += [f'<!-- unit: {uid} -->',f'`{uid}`: '+note,'']
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader target 1–12; 351 tables, 654 notes, PDF 5–487.')
if __name__=='__main__':main()
