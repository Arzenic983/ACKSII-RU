"""Adapt the previously inspected chapter07 fragment builder to chapter09."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=(ROOT/'.work/ch07-md/fragment_tools.py').read_text('utf-8')
source=source.replace('chapter 07','chapter 09').replace("contributions/07","contributions/09").replace('07 Плавания.md','09 Армии.md').replace('07_review','09_review').replace('07_validation','09_validation').replace("'07'","'09'").replace('главы 7','главы 9').replace('Глава 7. Плавания','Глава 9. Армии').replace('CHAPTER 7: VOYAGES','CHAPTER 9: ARMIES').replace('964','3179').replace('2026-10-16','2026-10-17').replace('16 октября 2026','17 октября 2026')
# Use the corrected English-label stripper (Russian damage brackets can contain br).
safe=(ROOT/'.work/ch08-md/build_chapter.py').read_text('utf-8').split('def plain(s):',1)[1].split('\n\ndef numbers',1)[0]
start=source.index('def plain(text):');end=source.index('\ndef numbers',start)
source=source[:start]+'def plain(s):'+safe+'\n\n'+source[end:]
(HERE/'build_fragment.py').write_text(source,'utf-8')
out=ROOT/'contributions/09'
if not (out/'translator.jsonl').exists():(out/'translator.jsonl').write_text('','utf-8')
for p,title in ((ROOT/'ACKSII/База перевода/09_review.md','# Начало перевода главы 9 «Армии»'),(out/'README.md','# Глава 09: неполный пакет')):
    if not p.exists():p.write_text(title+'\n\nПервый фрагмент PDF 428–429; вся глава PDF428–447. Статус draft, без утверждения человеком. Подробная точка продолжения будет сохранена в .work/ch09-md/checkpoint.json.\n','utf-8')
(HERE/'visual_review.json').write_text('{"source_pdf_pages_inspected":[429],"scope":"Просмотрено изображение PDF429: таблица платы за вербовку и расчёт48 000 в примере. Другие страницы и весь русский Markdown визуально не вычитывались."}\n','utf-8')
print('Chapter09 fragment builder prepared; SQLite is read-only.')
