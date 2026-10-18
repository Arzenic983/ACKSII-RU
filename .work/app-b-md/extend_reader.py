"""Extend the reader through appendix B; preserve previous source files."""
from pathlib import Path
import json,re,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==283 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 507' in s:
        changes={
            "TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложение A.md'":"TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–B.md'",
            "'A Сеттинг.md')]":"'A Сеттинг.md', 'B Состояния.md')]",
            'LAST_PAGE = 507':'LAST_PAGE = 517','EXPECTED_NOTES = 674':'EXPECTED_NOTES = 694',
            "    489: ('Сеттинг', 'SETTING'),":"    489: ('Сеттинг', 'SETTING'),\n    509: ('Состояния', 'CONDITIONS'),",
            'Приложение A\\. )':'Приложение [AB]\\. )',
            "            ('A. Сеттинг', 'A SETTING', 'Приложение A. Сеттинг', 'APPENDIX A: SETTING'),":"            ('A. Сеттинг', 'A SETTING', 'Приложение A. Сеттинг', 'APPENDIX A: SETTING'),\n            ('B. Состояния', 'B CONDITIONS', 'Приложение B. Состояния', 'APPENDIX B: CONDITIONS'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508)',
            "'A. Сеттинг': 'Приложение A. Сеттинг'":"'A. Сеттинг': 'Приложение A. Сеттинг', 'B. Состояния': 'Приложение B. Состояния'",
            "('A SETTING', 'APPENDIX A: SETTING')):":"('A SETTING', 'APPENDIX A: SETTING'), ('B CONDITIONS', 'APPENDIX B: CONDITIONS')):",
            "'previous_reader_pages_5_487_unchanged': True,":"'previous_reader_pages_5_487_unchanged': True,\n        'previous_reader_pages_5_507_unchanged': True,",
            '<title>ACKS II — главы 1–12 и приложение A</title>':'<title>ACKS II — главы 1–12 и приложения A–B</title>'
        }
        for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
        proof='''    previousA = result.split('<p align="right" id="pdf-page-0508">', 1)[0]
    previousA = re.sub(r'\\n---\\s*$', '', previousA).rstrip() + '\\n'
    assert previousA == (OUT / 'ACKS II — Начало, главы 1–12 и приложение A.md').read_text('utf-8'), 'Previously completed reader pages 5–507 changed'
    result = result.replace('Начало, главы 1–12 и приложение A', 'Начало, главы 1–12 и приложения A–B', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDIX A', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–B', 1)
    rendered = rendered.replace('Начало, главы 1–12 и приложение A', 'Начало, главы 1–12 и приложения A–B', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDIX A', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–B', 1)
'''
        at=s.index("    TARGET.write_text(result, 'utf-8')");s=s[:at]+proof+s[at:];p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 517' in s
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    if not backup.exists():
        assert '## Приложение B. Состояния' not in target.read_text('utf-8');shutil.copyfile(target,backup)
    additions=['','## Приложение B. Состояния','','<small>APPENDIX B: CONDITIONS — EDITORIAL NOTES</small>','']
    for uid,note in json.loads((HERE/'styled_notes.json').read_text('utf-8')).items():additions.extend([f'<!-- unit: {uid} -->',f'`{uid}`: '+note,''])
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader target A–B: PDF 5–517, 513 markers, 353 tables, 694 notes')
if __name__=='__main__':main()
