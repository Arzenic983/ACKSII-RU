"""Record the semantic review and image inspections already performed by Codex."""
from pathlib import Path
import hashlib,json
from audit import audit
HERE=Path(__file__).resolve().parent
assert not (HERE/'semantic_review.json').exists(),'Review already recorded; do not replace a completed review mechanically'
assert not audit()
assert len(json.loads((HERE/'pure.json').read_text('utf-8')))==809
assert len(json.loads((HERE/'notes.json').read_text('utf-8')))==21
metrics=json.loads((HERE/'visual_metrics.json').read_text('utf-8'))
assert len(metrics)==11 and all(m['scroll_width']<=m['viewport'] for m in metrics)
report={
    'date':'2026-10-17','reviewer':'Codex','complete_semantic_review_by_Codex':True,'independent_second_agent_review':False,'human_approval':False,
    'scope':{'book':'Revised Rulebook','chapter':'12','physical_pdf_pages':[474,487],'units':809,'headings':43,'paragraphs':164,'list_items':14,'table_cells':588,'tables':9},
    'method':'Перевод и повторная смысловая сверка одним Codex по EN checked.md и неизменным английским единицам. Все 14 тел страниц совпали с pages.source_markup. Сопоставлены условия, исключения, примеры, таблицы, названия заклинаний и межглавные ссылки. Числовые ячейки сохранены с русскими разделителями; словесные единицы переведены вручную.',
    'russian_units_sha256':hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest(),
    'checked_topics':[
        'Три способа осады, КОЗ, вместимость, соотношение штурма и обороны, создание брешей',
        'Блокада подразделениями, кораблями и циркумвалацией; запрет одновременного строительства блокирующими войсками',
        'Запасы, предел хранения, еженедельные расходы, контрабанда и диверсии без выдуманного знака модификатора',
        'Обстрел, боеприпасы, их сбор и дуэли; все строки таблицы артиллерии',
        'Заклинания, области воздействия, размеры существ, подкопы и контрподкопы, аварии и петарды',
        'Поджог, подрыв обороны, вечерний ремонт и ограничение половиной ущерба',
        'Восстановленный по PDF порядок колонок, схема четырёх вложенных зон, развёртывание и все семь фаз штурма',
        'Пороги 18+/17+/16+, одновременные потери, осадное снаряжение, бреши, бонусы обороны и ограничения конницы',
        'Героические вылазки, дистанции, прорывы, вылазки защитников, отход рассыпных подразделений и подземелья',
        'Исходы осады, добровольная и вынужденная сдача, пленные, добыча, Опыт и упрощённая длительность'
    ],
    'terminology_sources':['ACKSII/Глоссарий.md','ACKSII/База перевода/glossary.json','ACKSII/База перевода/bilingual_terms.md','главы 4–5 и 9–11'],
    'terminology_resolution':'Сохранены Арбитр, Приспешник, Домен/Владение, Подкрадывание как навык и Прятание, БР, КОЗ, В беспорядке. Колебание отличается от Нерешительности; rallied здесь означает восстановление строя, а не результат Rally. Заклинания согласованы с главой 5; Земляная трясина/Земляная топь отмечены как прежние рабочие варианты. Утверждённый глоссарий не менялся. Новые осадные термины рабочие.',
    'cross_chapter_evidence':'cross_chapter_evidence.json: английские места обеих глав, включая /30 против /50 и стандартную вместимость донжона',
    'source_questions':'21 примечание; числа, формулы, слова reserve/assault phase/battle turn и противоречащие примеры сохранены. Числовых исключений аудита нет.'
}
(HERE/'semantic_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
visual={'date':'2026-10-17','source_pdf_pages_inspected':[476,477,478,480,482,486],'russian_full_table_images_inspected':['rr.p0475.t01','rr.p0477.t01','rr.p0478.t01','rr.p0481.t01','rr.p0482.t01','rr.p0483.t01','rr.p0486.t01','rr.p0486.t02','rr.p0487.t01'],'russian_page480_regions_inspected':['diagram','setup paragraph','apply casualties paragraph'],'viewport':[1500,1800],'browser':'Headless Microsoft Edge via Playwright','all_11_html_samples_without_horizontal_overflow':True,'full_russian_visual_review':False,'observations':'Таблицы читаемы, объединённые заголовки и все 15 столбцов длительности сохранены. Схема имеет четыре вложенных зоны и двуязычные подписи. Восстановленные абзацы подготовки и применения потерь читаются последовательно. Вложенных квадратных скобок в тегах урона нет.','limits':'Технический разбор охватывает все единицы и таблицы; визуальный просмотр охватывает перечисленные изображения и фрагменты, а не всю прозу 14 страниц.'}
(HERE/'visual_review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Recorded semantic review by one Codex; human approval not assigned.')
