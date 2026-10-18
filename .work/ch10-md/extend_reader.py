"""Extend the reader to chapter 10, retaining all earlier preservation checks."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==521 and build['status']=='reviewed_by_Codex' and build['integrated']
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 447' in s:
        s=s.replace('1–9','1–10')
        replacements={
            "'09 Армии.md')]":"'09 Армии.md', '10 Манёвры.md')]",
            'LAST_PAGE = 447':'LAST_PAGE = 461',
            'EXPECTED_NOTES = 595':'EXPECTED_NOTES = 616',
            'EXPECTED_TABLES = 317':'EXPECTED_TABLES = 331',
            "    429: ('Армии', 'ARMIES'),":"    429: ('Армии', 'ARMIES'),\n    449: ('Манёвры', 'MANEUVERS'),",
            '[123456789]':'(?:[1-9]|10)',
            "            ('9. Армии', '9 ARMIES', 'Глава 9. Армии', 'CHAPTER 9: ARMIES'),":"            ('9. Армии', '9 ARMIES', 'Глава 9. Армии', 'CHAPTER 9: ARMIES'),\n            ('10. Манёвры', '10 MANEUVERS', 'Глава 10. Манёвры', 'CHAPTER 10: MANEUVERS'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448)',
            "'9. Армии': 'Глава 9. Армии'":"'9. Армии': 'Глава 9. Армии', '10. Манёвры': 'Глава 10. Манёвры'",
            "('9 ARMIES', 'CHAPTER 9: ARMIES')):":"('9 ARMIES', 'CHAPTER 9: ARMIES'), ('10 MANEUVERS', 'CHAPTER 10: MANEUVERS')):",
        }
        for old,new in replacements.items():
            assert old in s,old
            s=s.replace(old,new)
        at=s.index('    css = ')
        proof="""    previous9 = result.split('<p align="right" id="pdf-page-0448">', 1)[0]
    previous9 = re.sub(r'\\n---\\s*$', '', previous9).rstrip() + '\\n'
    previous9 = previous9.replace('Начало и главы 1–10', 'Начало и главы 1–9', 1).replace('FRONT MATTER AND CHAPTERS 1–10', 'FRONT MATTER AND CHAPTERS 1–9', 1)
    assert previous9 == (OUT / 'ACKS II — Начало и главы 1–9.md').read_text('utf-8'), 'Previously completed reader pages 5–447 changed'
"""
        s=s[:at]+proof+s[at:]
        s=s.replace("'previous_reader_pages_5_427_unchanged': True,","'previous_reader_pages_5_427_unchanged': True,\n        'previous_reader_pages_5_447_unchanged': True,")
        p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 461' in s
    notes=json.loads((HERE/'styled_notes.json').read_text('utf-8'))
    summary=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md'
    marker='## Глава 10. Манёвры'
    old=summary.read_text('utf-8')
    backup=HERE/'editor_notes_before.tmp'
    if marker not in old:
        assert not backup.exists()
        shutil.copyfile(summary,backup)
    assert backup.exists()
    addition=['',marker,'','<small>CHAPTER 10: MANEUVERS — EDITORIAL NOTES</small>','']
    for uid,text in notes.items():addition += [f'<!-- unit: {uid} -->',f'`{uid}`: '+text,'']
    summary.write_text(backup.read_text('utf-8')+'\n'.join(addition),'utf-8')
    terms={en:ru for pat,en,ru in (line.split('\t') for line in (HERE/'term_rules.tsv').read_text('utf-8').splitlines() if line)}
    (HERE/'term_map.json').write_text(json.dumps(terms,ensure_ascii=False,indent=2)+'\n','utf-8')
    export=ROOT/'contributions/_export/ch10'
    subprocess.run([sys.executable,str(BASE/'database_tools.py'),'export','--out',str(export)],check=True)
    for name in ('units.jsonl','progress.json','10_review.csv'):shutil.copyfile(export/name,BASE/name)
    print('Reader extended to PDF461, 331 tables, 616 notes; exports refreshed.')
if __name__=='__main__':main()
