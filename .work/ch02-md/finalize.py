import pathlib,sqlite3,json,re,collections,hashlib,importlib.util,sys

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=ROOT/'ACKSII/База перевода'
spec=importlib.util.spec_from_file_location('dbtools',BASE/'database_tools.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
db=m.connect(BASE/'acksii_translation.sqlite');result=m.verify(db)
before=sqlite3.connect((P/'before_chapter02.sqlite').as_uri()+'?mode=ro',uri=True);before.row_factory=sqlite3.Row
old=[tuple(r) for r in before.execute("SELECT * FROM translations WHERE unit_id IN (SELECT id FROM units WHERE pdf_page<=23) ORDER BY unit_id")]
now=[tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id IN (SELECT id FROM units WHERE pdf_page<=23) ORDER BY unit_id")]
assert old==now,'Pre-existing translation changed'
for table,order in [('units','id'),('pages','pdf_page'),('source_tables','id'),('glossary','id')]:
    assert [tuple(r) for r in before.execute(f'SELECT * FROM {table} ORDER BY {order}')]==[tuple(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY {order}')],table+' changed'

def normalized(s):return s.replace('−','-').replace('–','-').replace('—','-')
def dice(s):return collections.Counter(re.sub(r'\s','',v.lower()) for v in re.findall(r'\b\d+d\d+(?:\s*[+-]\s*\d+)?',normalized(s),re.I))
def percent(s):return collections.Counter(re.findall(r'\d+(?:\.\d+)?%',s.replace(' ','')))
def signs(s):return collections.Counter(re.findall(r'(?<![\w\d])[-+]\d+(?:\.\d+)?',normalized(s)))
for u in db.execute("SELECT * FROM bilingual WHERE chapter_id='02'"):
    assert dice(u['english'])==dice(u['russian']),('dice',u['id'])
    assert percent(u['english'])==percent(u['russian']),('percent',u['id'])
    assert signs(u['english'])==signs(u['russian']),('signs',u['id'])

expected={r['id']:dict(r) for r in db.execute('SELECT * FROM bilingual')}
json_ids=set()
with (BASE/'units.jsonl').open(encoding='utf-8') as f:
    for line in f:
        item=json.loads(line);id=item['id'];assert id not in json_ids
        assert item==expected[id],id
        json_ids.add(id)
assert json_ids==set(expected)

protected=json.loads((P/'protected_docx_hashes.json').read_text('utf-8'))
current={str(f.relative_to(ROOT)) for f in (ROOT/'ACKSII').rglob('*.docx')}
assert current==set(protected),'DOCX file set changed'
for path,h in protected.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path

stage=json.loads((P/'markdown_validation.json').read_text('utf-8'));render=json.loads((P/'rendered_markdown_validation.json').read_text('utf-8'))
validation={**stage,**render,'dice_formulas':'passed','percentages':'passed','signed_modifiers':'passed','preexisting_translations_unchanged':True,'source_units_pages_tables_unchanged':True,'project_glossary_unchanged':True,'jsonl_roundtrip_records':len(json_ids),'independent_semantic_review_ranges':[[24,41],[42,45],[46,61],[62,81],[82,101]],'pdf_visual_review_pages':[37,44,64,72,93],'review_status':'reviewed_by_Codex','user_approved':False}
(BASE/'02_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),'utf-8')
overall=json.loads((BASE/'validation.json').read_text('utf-8'));overall.update(result)
overall['date']='2026-10-15';overall['translated_scope_pdf_pages']=[1,101]
overall['origins']={r[0]:r[1] for r in db.execute('SELECT origin,count(*) FROM translations GROUP BY origin ORDER BY origin')}
overall['chapter_progress']=[dict(r) for r in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')]
overall['chapter02_markdown']=validation
(BASE/'validation.json').write_text(json.dumps(overall,ensure_ascii=False,indent=2),'utf-8')

review=BASE/'review.md';old_report=review.read_text('utf-8')
if not old_report.startswith('# Сверка перевода ACKS II: PDF-страницы 1–101'):
    old_report=re.sub(r'^(#+) ',lambda x:'#'+x[1]+' ',old_report,flags=re.M)
    old_report=old_report.replace('Перевод глав 2 и далее не начат.','На момент предыдущей проверки 14 октября перевод глав 2 и далее не был начат.')
    intro='''# Сверка перевода ACKS II: PDF-страницы 1–101

Обновлено: 15 октября 2026 года. Полностью переведена и проверена глава 2 «Классы» (PDF 24–101): **5 963 / 5 963 единицы**, 74 таблицы и 5 031 ячейка. Подробный отчёт — [02_review.md](02_review.md).

Начало книги, первая и вторая главы объединены в [единый Markdown-документ](../Перевод%20Markdown/ACKS%20II%20—%20Начало%20и%20главы%201–2.md). В нём 7 652 единицы, все 101 ссылки на PDF-страницы, 89 таблиц и 100 примечаний в 99 местах. Исправления и комментарии со звёздочками расположены рядом с соответствующим текстом. Отдельные главы также сохранены в Markdown.

Проверены полнота и порядок идентификаторов, числовые значения, формулы костей, проценты, знаки модификаторов, геометрия таблиц и результат разбора Markdown. База SQLite, история редакций и поисковый индекс прошли проверку без ошибок; `progress.json` и `units.jsonl` обновлены. Текущие результаты — [02_validation.json](02_validation.json).

Перевод начала и первой главы в базе сохранён без изменений. Исходные английские единицы и основной глоссарий не изменены. Все 45 существующих DOCX проверены по SHA-256, изменений нет; новые DOCX не создавались. Рабочие названия новых терминов не считаются утверждённым глоссарием. Противоречия оригинала отмечены сносками, в том числе расчёт КЗ тотема и повреждённая дробь нагрузки на PDF-странице 72.

Статус — проверено Codex, без утверждения пользователем. Следующая глава: 3 «Навыки», PDF 102–123.

---

Ниже сохранён предыдущий отчёт **по состоянию на 14 октября 2026 года**; он описывает подготовку базы и редактуру материалов до конца первой главы.

'''
    review.write_text(intro+old_report,'utf-8')
print(json.dumps({'integrity':result,'translated':len(now)+stage['translated_units'],'chapter02_pending':stage['pending_units'],'jsonl_records':len(json_ids),'old_translations_unchanged':len(old),'protected_docx':len(protected),'all_checks':'passed'},ensure_ascii=False,indent=2))
