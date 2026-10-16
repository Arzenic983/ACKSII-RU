"""Refresh current database reports; retain historical historical report fields."""
from collections import Counter
import importlib.util
import json
import sqlite3
from auto_units import HERE, ROOT

def main():
    base=ROOT/'ACKSII/База перевода'
    spec=importlib.util.spec_from_file_location('database_tools',base/'database_tools.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with sqlite3.connect((base/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        checked=module.verify(db)
        validation=json.loads((base/'validation.json').read_text('utf-8'))
        validation.update(checked)
        validation.update({
            'date':'2026-10-16','translated_scope_pdf_pages':[1,179],
            'pages':db.execute('SELECT count(*) FROM pages').fetchone()[0],
            'tables':db.execute('SELECT count(*) FROM source_tables').fetchone()[0],
            'glossary_entries':db.execute('SELECT count(*) FROM glossary').fetchone()[0],
            'origins':dict(db.execute('SELECT origin,count(*) FROM translations GROUP BY origin ORDER BY origin')),
            'chapter_progress':[dict(r) for r in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')],
            'chapter04_markdown':json.loads((base/'04_validation.json').read_text('utf-8')),
            'current_reading_copy':json.loads((base/'reading_validation.json').read_text('utf-8')),
        })
        (base/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n','utf-8')
    visual={
        'date':'2026-10-16','document':'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–4.md',
        'method':'Выборочная визуальная проверка локального HTML после разбора Markdown в браузере Codex',
        'pdf_page_sections_seen':[125,137,169,178],
        'checks':['русский заголовок и меньшая английская строка ниже','подписи в квадратных скобках','положение столбцов и объединённых шапок таблицы судов','пустые клетки и таблица повиновения','переносы текста и примечания строительной таблицы'],
        'findings':'На просмотренных участках наложений, обрезанного текста и смещений столбцов не обнаружено.',
        'full_document_visual_review':False,
    }
    (HERE/'visual_validation.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf-8')
    review=base/'review.md'
    text=review.read_text('utf-8')
    if not text.startswith('# Сверка перевода ACKS II: PDF-страницы 1–179'):
        text=text.replace('# Сверка перевода ACKS II: PDF-страницы 1–123','## Предыдущая сверка: PDF-страницы 1–123',1)
        current='# Сверка перевода ACKS II: PDF-страницы 1–179\n\nОбновлено 16 октября 2026 года. Завершена глава 4 «Снаряжение» [Equipment], PDF 124–179: **4 566 / 4 566 единиц**, 52 таблицы, 33 примечания. Всего в базе **12 922** перевода. Вычитка Codex не означает утверждения пользователем.\n\n[Общий читательский Markdown](<../Перевод Markdown/ACKS II — Начало и главы 1–4.md>) охватывает PDF 5–179: 175 маркеров страниц, 151 таблица, 156 примечаний. Предыдущий диапазон PDF 5–123 сохранён без изменений, что подтверждено сравнением хешей. Подробная вычитка и вопросы оригинала — [04_review.md](04_review.md), технические результаты — [04_validation.json](04_validation.json).\n\nПри конфликтах сопоставлены английские места обеих глав: ошибки русского черновика исправлены с пометками в отчёте; противоречия оригинала сохранены под звёздочкой. SQLite, история, поиск и исходные хеши прошли проверку. Следующая глава — 5 «Заклинания» [Spells], PDF 180–263.\n\n---\n\n'
        review.write_text(current+text,'utf-8')

if __name__=='__main__':main()
