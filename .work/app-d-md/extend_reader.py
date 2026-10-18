"""Extend the reader through D and preserve the completed PDF 5–531 exactly."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==163 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 531' in s:
        changes={
            "TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–C.md'":"TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–D.md'",
            "'C Раны и страдания.md')]":"'C Раны и страдания.md', 'D Материалы.md')]",
            'LAST_PAGE = 531':'LAST_PAGE = 537','EXPECTED_NOTES = 719':'EXPECTED_NOTES = 731','EXPECTED_TABLES = 364':'EXPECTED_TABLES = 370',
            'Приложение [ABC]\\. )':'Приложение [ABCD]\\. )',
            "            ('C. Раны', 'C WOUNDS', 'Приложение C. Раны и страдания', 'APPENDIX C: WOUNDS AND WOE'),":"            ('C. Раны', 'C WOUNDS', 'Приложение C. Раны и страдания', 'APPENDIX C: WOUNDS AND WOE'),\n            ('D. Материалы', 'D RESOURCES', 'Приложение D. Материалы', 'APPENDIX D: RESOURCES'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508, 518)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508, 518, 532)',
            "'C. Раны': 'Приложение C. Раны и страдания'":"'C. Раны': 'Приложение C. Раны и страдания', 'D. Материалы': 'Приложение D. Материалы'",
            "('C WOUNDS', 'APPENDIX C: WOUNDS AND WOE')):":"('C WOUNDS', 'APPENDIX C: WOUNDS AND WOE'), ('D RESOURCES', 'APPENDIX D: RESOURCES')):",
            "'previous_reader_pages_5_517_unchanged': True,":"'previous_reader_pages_5_517_unchanged': True,\n        'previous_reader_pages_5_531_unchanged': True,",
            '<title>ACKS II — главы 1–12 и приложения A–C</title>':'<title>ACKS II — главы 1–12 и приложения A–D</title>',
            "body = re.split(r'\\n# ":"body = re.split(r'(?:^|\\n)# ",
            "            old = f'## {russian}\\n\\n<small>{english}</small>'":"            old = f'## {russian}\\n\\n<small>{english}</small>'\n            suffix = '<sup>*</sup>' if f'## {russian}<sup>*</sup>\\n\\n<small>{english}</small>' in body else ''\n            if suffix:\n                old = f'## {russian}{suffix}\\n\\n<small>{english}</small>'",
            "f'# {new_russian}\\n\\n<small>{new_english}</small>'":"f'# {new_russian}{suffix}\\n\\n<small>{new_english}</small>'",
            "'D. Материалы': 'Приложение D. Материалы'":"'D. Материалы': 'Приложение D. Материалы', 'D. Материалы<sup>*</sup>': 'Приложение D. Материалы<sup>*</sup>'"
        }
        for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
        proof='''    previousC = result.split('<p align="right" id="pdf-page-0532">', 1)[0]
    previousC = re.sub(r'\\n---\\s*$', '', previousC).rstrip() + '\\n'
    assert previousC == (OUT / 'ACKS II — Начало, главы 1–12 и приложения A–C.md').read_text('utf-8'), 'Previously completed reader pages 5–531 changed'
    result = result.replace('Начало, главы 1–12 и приложения A–C', 'Начало, главы 1–12 и приложения A–D', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–C', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–D', 1)
    rendered = rendered.replace('Начало, главы 1–12 и приложения A–C', 'Начало, главы 1–12 и приложения A–D', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–C', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–D', 1)
'''
        at=s.index("    TARGET.write_text(result, 'utf-8')");s=s[:at]+proof+s[at:];p.write_text(s,'utf-8')
    # Cover headings may carry editorial note marks; keep them during promotion.
    assert 'LAST_PAGE = 537' in s
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    old=next(h for name,h in baseline['protected_files'].items() if name.endswith('Примечания редактора.md'))
    if not backup.exists():
        assert hashlib.sha256(target.read_bytes()).hexdigest()==old
        shutil.copyfile(target,backup)
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==old
    additions=['','## Приложение D. Материалы','','<small>APPENDIX D: RESOURCES — EDITORIAL NOTES</small>','']
    for uid,note in json.loads((HERE/'styled_notes.json').read_text('utf-8')).items():additions.extend([f'<!-- unit: {uid} -->',f'`{uid}`: '+note,''])
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader target A–D: PDF 5–537, 533 markers, 370 tables, 731 notes')
if __name__=='__main__':main()
