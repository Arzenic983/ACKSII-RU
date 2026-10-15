"""Refresh current database reports; retain historical chapter-2 report fields."""
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
            'date':'2026-10-16','translated_scope_pdf_pages':[1,123],
            'pages':db.execute('SELECT count(*) FROM pages').fetchone()[0],
            'tables':db.execute('SELECT count(*) FROM source_tables').fetchone()[0],
            'glossary_entries':db.execute('SELECT count(*) FROM glossary').fetchone()[0],
            'origins':dict(db.execute('SELECT origin,count(*) FROM translations GROUP BY origin ORDER BY origin')),
            'chapter_progress':[dict(r) for r in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')],
            'chapter03_markdown':json.loads((base/'03_validation.json').read_text('utf-8')),
            'current_reading_copy':json.loads((base/'reading_validation.json').read_text('utf-8')),
        })
        (base/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n','utf-8')
    visual={
        'date':'2026-10-16','document':'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–3.md',
        'method':'Выборочная визуальная проверка локального HTML после разбора Markdown в браузере Codex',
        'pdf_page_sections_seen':[102,104,113,118,119,123],
        'checks':['русский заголовок и меньшая английская строка ниже','подписи в квадратных скобках','положение числовых столбцов таблицы навыков по уровням','недоступные уровни и пустые клетки','переносы текста и примечания у таблиц фамильяров и профессий'],
        'findings':'На просмотренных участках наложений, обрезанного текста и смещений столбцов не обнаружено.',
        'full_document_visual_review':False,
    }
    (HERE/'visual_validation.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf-8')
    review=base/'review.md'
    text=review.read_text('utf-8')
    if not text.startswith('# Сверка перевода ACKS II: PDF-страницы 1–123'):
        text=text.replace('../Перевод%20Markdown/ACKS%20II%20—%20Начало%20и%20главы%201–2.md','../Перевод%20Markdown/ACKS%20II%20—%20Начало%20и%20главы%201–3.md')
        text=text.replace('# Сверка перевода ACKS II: PDF-страницы 1–101','## Предыдущая сверка: PDF-страницы 1–101',1)
        current='# Сверка перевода ACKS II: PDF-страницы 1–123\n\nОбновлено: 16 октября 2026 года. Завершена глава 3 «Навыки» [Proficiencies], PDF 102–123: **704 / 704 единицы**, 10 таблиц и 23 новых примечания. Всего в базе **8 356** переводов. Подробная сверка, ограничения проверки и нерешённые вопросы — [03_review.md](03_review.md); технический отчёт — [03_validation.json](03_validation.json).\n\n[Общий читательский Markdown](<../Перевод Markdown/ACKS II — Начало и главы 1–3.md>) охватывает PDF 5–123: 119 маркеров страниц, 99 таблиц, 123 примечания. Прежний текст PDF 5–101 сохранён без изменений. Полная глава и пакет с исходными ID и редакциями сохранены отдельно. Оформление будущих глав закреплено в README-PROJECT.md.\n\nПроверены полнота, числа, формулы, позиции пустых ячеек и структура после разбора Markdown. SQLite, история и поиск прошли проверку; исходные английские единицы, глоссарий, DOCX и прежние переводы не изменены. Выполнена авторская вычитка Codex, без утверждения пользователем. Следующая глава — 4 «Снаряжение» [Equipment], PDF 124–179.\n\n---\n\n'
        review.write_text(current+text,'utf-8')

if __name__=='__main__':main()
