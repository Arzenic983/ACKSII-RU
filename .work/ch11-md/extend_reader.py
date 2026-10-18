"""Append chapter 11 while retaining every earlier reader preservation proof."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    result=json.loads((HERE/'build.json').read_text('utf-8'))
    assert result['units']==618 and result['integrated'] and result['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 461' in s:
        s=s.replace('1–10','1–11')
        replacements={
            "'10 Манёвры.md')]":"'10 Манёвры.md', '11 Сражения.md')]",
            'LAST_PAGE = 461':'LAST_PAGE = 473',
            'EXPECTED_NOTES = 616':'EXPECTED_NOTES = 633',
            'EXPECTED_TABLES = 331':'EXPECTED_TABLES = 342',
            "    449: ('Манёвры', 'MANEUVERS'),":"    449: ('Манёвры', 'MANEUVERS'),\n    463: ('Сражения', 'BATTLES'),",
            '(?:[1-9]|10)':'(?:[1-9]|10|11)',
            "            ('10. Манёвры', '10 MANEUVERS', 'Глава 10. Манёвры', 'CHAPTER 10: MANEUVERS'),":"            ('10. Манёвры', '10 MANEUVERS', 'Глава 10. Манёвры', 'CHAPTER 10: MANEUVERS'),\n            ('11. Сражения', '11 BATTLES', 'Глава 11. Сражения', 'CHAPTER 11: BATTLES'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462)',
            "'10. Манёвры': 'Глава 10. Манёвры'":"'10. Манёвры': 'Глава 10. Манёвры', '11. Сражения': 'Глава 11. Сражения'",
            "('10 MANEUVERS', 'CHAPTER 10: MANEUVERS')):":"('10 MANEUVERS', 'CHAPTER 10: MANEUVERS'), ('11 BATTLES', 'CHAPTER 11: BATTLES')):",
        }
        for old,new in replacements.items():
            assert old in s,old
            s=s.replace(old,new)
        proof='''    previous10 = result.split('<p align="right" id="pdf-page-0462">', 1)[0]
    previous10 = re.sub(r'\\n---\\s*$', '', previous10).rstrip() + '\\n'
    previous10 = previous10.replace('Начало и главы 1–11', 'Начало и главы 1–10', 1).replace('FRONT MATTER AND CHAPTERS 1–11', 'FRONT MATTER AND CHAPTERS 1–10', 1)
    assert previous10 == (OUT / 'ACKS II — Начало и главы 1–10.md').read_text('utf-8'), 'Previously completed reader pages 5–461 changed'
'''
        at=s.index('    css = ');s=s[:at]+proof+s[at:]
        s=s.replace("'previous_reader_pages_5_447_unchanged': True,","'previous_reader_pages_5_447_unchanged': True,\n        'previous_reader_pages_5_461_unchanged': True,")
        p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 473' in s
    notes=json.loads((HERE/'styled_notes.json').read_text('utf-8'))
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    if not backup.exists():
        assert '## Глава 11. Сражения' not in target.read_text('utf-8')
        shutil.copyfile(target,backup)
    additions=['','## Глава 11. Сражения','','<small>CHAPTER 11: BATTLES — EDITORIAL NOTES</small>','']
    for uid,note in notes.items():additions += [f'<!-- unit: {uid} -->',f'`{uid}`: '+note,'']
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    terms={en:ru for pat,en,ru in (line.split('\t') for line in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if line)}
    (HERE/'term_map.json').write_text(json.dumps(terms,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Reader target1–11; 342 tables, 633 notes, PDF5–473.')
if __name__=='__main__':main()
