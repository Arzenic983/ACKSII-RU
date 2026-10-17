"""One-time reader extension through C, with an exact A–B preservation proof."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==827 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 517' in s:
        changes={
            "TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–B.md'":"TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–C.md'",
            "'B Состояния.md')]":"'B Состояния.md', 'C Раны и страдания.md')]",
            'LAST_PAGE = 517':'LAST_PAGE = 531','EXPECTED_NOTES = 694':'EXPECTED_NOTES = 719','EXPECTED_TABLES = 353':'EXPECTED_TABLES = 364',
            "    509: ('Состояния', 'CONDITIONS'),":"    509: ('Состояния', 'CONDITIONS'),\n    519: ('Раны и страдания', 'WOUNDS AND WOE'),",
            'Приложение [AB]\\. )':'Приложение [ABC]\\. )',
            "            ('B. Состояния', 'B CONDITIONS', 'Приложение B. Состояния', 'APPENDIX B: CONDITIONS'),":"            ('B. Состояния', 'B CONDITIONS', 'Приложение B. Состояния', 'APPENDIX B: CONDITIONS'),\n            ('C. Раны', 'C WOUNDS', 'Приложение C. Раны и страдания', 'APPENDIX C: WOUNDS AND WOE'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508, 518)',
            "'B. Состояния': 'Приложение B. Состояния'":"'B. Состояния': 'Приложение B. Состояния', 'C. Раны': 'Приложение C. Раны и страдания'",
            "('B CONDITIONS', 'APPENDIX B: CONDITIONS')):":"('B CONDITIONS', 'APPENDIX B: CONDITIONS'), ('C WOUNDS', 'APPENDIX C: WOUNDS AND WOE')):",
            "'previous_reader_pages_5_507_unchanged': True,":"'previous_reader_pages_5_507_unchanged': True,\n        'previous_reader_pages_5_517_unchanged': True,",
            '<title>ACKS II — главы 1–12 и приложения A–B</title>':'<title>ACKS II — главы 1–12 и приложения A–C</title>'
        }
        for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
        proof='''    previousB = result.split('<p align="right" id="pdf-page-0518">', 1)[0]
    previousB = re.sub(r'\\n---\\s*$', '', previousB).rstrip() + '\\n'
    assert previousB == (OUT / 'ACKS II — Начало, главы 1–12 и приложения A–B.md').read_text('utf-8'), 'Previously completed reader pages 5–517 changed'
    result = result.replace('Начало, главы 1–12 и приложения A–B', 'Начало, главы 1–12 и приложения A–C', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–B', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–C', 1)
    rendered = rendered.replace('Начало, главы 1–12 и приложения A–B', 'Начало, главы 1–12 и приложения A–C', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–B', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–C', 1)
'''
        at=s.index("    TARGET.write_text(result, 'utf-8')");s=s[:at]+proof+s[at:];p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 531' in s
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    old=next(h for name,h in baseline['protected_files'].items() if name.endswith('Примечания редактора.md'))
    if not backup.exists():
        assert hashlib.sha256(target.read_bytes()).hexdigest()==old
        shutil.copyfile(target,backup)
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==old
    additions=['','## Приложение C. Раны и страдания','','<small>APPENDIX C: WOUNDS AND WOE — EDITORIAL NOTES</small>','']
    for uid,note in json.loads((HERE/'styled_notes.json').read_text('utf-8')).items():additions.extend([f'<!-- unit: {uid} -->',f'`{uid}`: '+note,''])
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader target A–C: PDF 5–531, 527 markers, 364 tables, 719 notes')
if __name__=='__main__':main()
