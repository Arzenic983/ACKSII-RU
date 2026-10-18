"""One-time extension through E, preserving the completed PDF 5–537 exactly."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    build=json.loads((HERE/'build.json').read_text('utf-8'))
    assert build['units']==83 and build['integrated'] and build['status']=='reviewed_by_Codex'
    p=ROOT/'.work/reading-md/format_reading.py';s=p.read_text('utf-8')
    if 'LAST_PAGE = 537' in s:
        changes={
            "TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–D.md'":"TARGET = OUT / 'ACKS II — Начало, главы 1–12 и приложения A–E.md'",
            "'D Материалы.md')]":"'D Материалы.md', 'E Предметный указатель.md')]",
            'LAST_PAGE = 537':'LAST_PAGE = 550','EXPECTED_NOTES = 731':'EXPECTED_NOTES = 741',
            'Приложение [ABCD]\\. )':'Приложение [ABCDE]\\. )',
            "            ('D. Материалы', 'D RESOURCES', 'Приложение D. Материалы', 'APPENDIX D: RESOURCES'),":"            ('D. Материалы', 'D RESOURCES', 'Приложение D. Материалы', 'APPENDIX D: RESOURCES'),\n            ('E. Предметный указатель', 'E INDEX', 'Приложение E. Предметный указатель', 'APPENDIX E: INDEX'),",
            '(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508, 518, 532)':'(8, 14, 24, 102, 124, 180, 264, 316, 334, 428, 448, 462, 474, 488, 508, 518, 532, 538)',
            "'D. Материалы<sup>*</sup>': 'Приложение D. Материалы<sup>*</sup>'":"'D. Материалы<sup>*</sup>': 'Приложение D. Материалы<sup>*</sup>', 'E. Предметный указатель<sup>*</sup>': 'Приложение E. Предметный указатель<sup>*</sup>'",
            "('D RESOURCES', 'APPENDIX D: RESOURCES')):":"('D RESOURCES', 'APPENDIX D: RESOURCES'), ('E INDEX', 'APPENDIX E: INDEX')):",
            "'previous_reader_pages_5_531_unchanged': True,":"'previous_reader_pages_5_531_unchanged': True,\n        'previous_reader_pages_5_537_unchanged': True,\n        'all_12_chapters_and_5_appendices_in_book_order': True,",
            '<title>ACKS II — главы 1–12 и приложения A–D</title>':'<title>ACKS II — главы 1–12 и приложения A–E</title>',
            "    sources = [p.read_text('utf-8') for p in INPUTS]":"    assert len(INPUTS) == 18 and [p.name[:2].strip() for p in INPUTS] == ['00'] + [f'{n:02}' for n in range(1, 13)] + list('ABCDE')\n    sources = [p.read_text('utf-8') for p in INPUTS]"
        }
        for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
        proof='''    previousD = result.split('<p align="right" id="pdf-page-0538">', 1)[0]
    previousD = re.sub(r'\\n---\\s*$', '', previousD).rstrip() + '\\n'
    assert previousD == (OUT / 'ACKS II — Начало, главы 1–12 и приложения A–D.md').read_text('utf-8'), 'Previously completed reader pages 5–537 changed'
    result = result.replace('Начало, главы 1–12 и приложения A–D', 'Начало, главы 1–12 и приложения A–E', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–D', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–E', 1)
    rendered = rendered.replace('Начало, главы 1–12 и приложения A–D', 'Начало, главы 1–12 и приложения A–E', 1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–D', 'FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–E', 1)
'''
        at=s.index("    TARGET.write_text(result, 'utf-8')");s=s[:at]+proof+s[at:];p.write_text(s,'utf-8')
    assert 'LAST_PAGE = 550' in s
    target=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md';backup=HERE/'editor_notes_before.tmp'
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    old=next(h for name,h in baseline['protected_files'].items() if name.endswith('Примечания редактора.md'))
    if not backup.exists():
        assert hashlib.sha256(target.read_bytes()).hexdigest()==old
        shutil.copyfile(target,backup)
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==old
    additions=['','## Приложение E. Предметный указатель','','<small>APPENDIX E: INDEX — EDITORIAL NOTES</small>','']
    for uid,note in json.loads((HERE/'styled_notes.json').read_text('utf-8')).items():additions.extend([f'<!-- unit: {uid} -->',f'`{uid}`: '+note,''])
    target.write_text(backup.read_text('utf-8')+'\n'.join(additions),'utf-8')
    print('Reader target A–E: PDF 5–550, 546 markers, 370 tables, 741 notes')
if __name__=='__main__':main()
