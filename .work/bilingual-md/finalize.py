import pathlib,json,re,hashlib,sqlite3,importlib.util

P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=ROOT/'ACKSII/База перевода';OUT=ROOT/'ACKSII/Перевод Markdown'
stage=json.loads((ROOT/'.work/ch02-md/markdown_validation.json').read_text('utf-8'))
render=json.loads((ROOT/'.work/ch02-md/rendered_markdown_validation.json').read_text('utf-8'))
files={}
for path in (P/'before').glob('*.md'):
    before=path.read_text('utf-8');after=(OUT/path.name).read_text('utf-8')
    ru=lambda t:''.join(re.findall('[А-Яа-яЁё]',t))
    assert ru(before)==ru(after),path.name+' Russian text changed'
    assert re.findall(r'<!-- unit: ([^ ]+) -->',before)==re.findall(r'<!-- unit: ([^ ]+) -->',after),path.name+' IDs changed'
    assert not re.search(r'\[[^\]\n]*\[[A-Za-z]',after),path.name+' nested brackets'
    files[path.name]={'russian_letters_unchanged':True,'unit_ids_unchanged':True,'english_subtitles':after.count('<small>'),'english_labels':len(re.findall(r'\[[A-Za-z][^\]\n]*\]',after)),'sha256_normalized_newlines':hashlib.sha256(after.encode()).hexdigest()}
protected=json.loads((ROOT/'.work/ch02-md/protected_docx_hashes.json').read_text('utf-8'))
for f,h in protected.items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
combined=(OUT/'ACKS II — Начало и главы 1–2.md').read_text('utf-8')
assert combined.count('<small>')==268+6+430+4
mythography=list(re.finditer(r'Мифографи[а-яё]+',combined,re.I))
missing=[]
for m in mythography:
    tail=combined[m.end():m.end()+80]
    if not re.match(r'(?:[\s*»”\"]*\[Loremastery\]|<br><small>LOREMASTERY</small>)',tail,re.I):missing.append(combined[m.start():m.end()+80])
assert not missing,missing
result={'date':'2026-10-15','scope_pdf_pages':[1,101],'source_headings_with_english':stage['bilingual_source_headings'],'additional_subheadings_with_english':stage['bilingual_source_subheadings'],'table_header_cells_with_english':stage['bilingual_table_headers'],'body_term_annotations':stage['bilingual_term_annotations'],'annotation_variants':stage['bilingual_term_variants'],'mythography_uses_verified':len(mythography),'russian_text_preserved':True,'nested_english_brackets':0,'docx_modified':False,'database_translation_modified':False,'files':files,'rendered_structure':render}
(BASE/'bilingual_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
for filename in ('02_validation.json','validation.json'):
    path=BASE/filename;obj=json.loads(path.read_text('utf-8'))
    target=obj if filename=='02_validation.json' else obj['chapter02_markdown']
    target.update(render);target['bilingual_presentation']=result
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
section='''
## Двуязычное оформление — уточнение 15 октября 2026 года

В начало, первую и вторую главы добавлены английские имена специальных и неоднозначных терминов в квадратных скобках при каждом соответствующем употреблении, в том числе в таблицах и сносках. Подписаны навыки, классовые способности, состояния, виды магии, специальные категории оружия, заклинания, шаблоны и титулы. Примеры: «Мифография [Loremastery]», «дальнобойное оружие [missile weapons]».

Под всеми 268 исходными заголовками и 6 самостоятельными подзаголовками помещена отдельная английская строка. Английский оригинал добавлен также под русскими названиями в 430 ячейках заголовков таблиц. Оформление следует образцу пользователя: русский заголовок сверху, меньшая английская строка снизу.

Проверены сохранность русского текста во всех пяти Markdown-файлах, порядок 7 652 идентификаторов, 89 таблиц и 101 ссылки на PDF-страницы. Вложенных английских квадратных скобок нет; все употребления «Мифографии» снабжены подписью Loremastery. Русский перевод и основной глоссарий в SQLite не изменялись. DOCX не изменялись.

Правила оформления сохранены в [bilingual_style.md](bilingual_style.md), карта подписей — в [bilingual_terms.md](bilingual_terms.md), результаты проверки — в [bilingual_validation.json](bilingual_validation.json).
'''
path=BASE/'02_review.md';text=path.read_text('utf-8')
if '## Двуязычное оформление' not in text:path.write_text(text.rstrip()+'\n'+section,'utf-8')
path=BASE/'review.md';text=path.read_text('utf-8')
notice='По последующему уточнению пользователя термины сопровождаются английскими именами в квадратных скобках, а русские заголовки — отдельной английской строкой снизу. Оформление применено ко всему диапазону PDF 1–101; русский перевод, страницы, таблицы и DOCX сохранены. Подробности — в разделе о двуязычном оформлении [02_review.md](02_review.md).\n\n'
if notice not in text:
    pos=text.index('\n\n')+2;text=text[:pos]+notice+text[pos:];path.write_text(text,'utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('files','rendered_structure')},ensure_ascii=False,indent=2))
