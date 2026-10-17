"""Publish the current audit reports after the independent checks have passed."""
from pathlib import Path
import hashlib,json,re,sqlite3

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    structural=json.loads((HERE/'structural_audit.json').read_text('utf-8'))
    readers=json.loads((BASE/'RR_reading_validation.json').read_text('utf-8'))
    notes=json.loads((BASE/'RR_notes_validation.json').read_text('utf-8'))
    clean_reader=json.loads((BASE/'RR_clean_reader_validation.json').read_text('utf-8'))
    assert clean_reader['visible_machine_markers']==0 and clean_reader['reader_note_projections']==34
    legacy=json.loads((BASE/'RR_legacy_review.json').read_text('utf-8'))
    integration=json.loads((HERE/'integration.json').read_text('utf-8'))
    baseline=json.loads((HERE/'inventory.json').read_text('utf-8'))
    assert structural['render_comparison_candidates']==0 and not structural['chapter_csv_differences']
    assert notes['inline_notes']==751 and notes['reader_notes_equal_full_chapters']
    protected={name:digest for name,digest in baseline['protected'].items() if not name.endswith('.sqlite')}
    assert all(sha(ROOT/name)==digest for name,digest in protected.items())
    assert len(baseline['docx'])==39 and not any(d.get('unavailable') for d in baseline['docx'])
    metrics=json.loads((HERE/'visual_metrics.json').read_text('utf-8'))
    assert all(m['scroll_width']==m['viewport'] and not m['unavailable_images'] and not m['clipped_cells'] for m in metrics)
    units=[json.loads(s) for s in (BASE/'units.jsonl').read_text('utf-8').splitlines()]
    canonical=next(r for name,r in readers['outputs'].items() if name.startswith('ACKS II —'))
    human=next(r for r in readers['outputs'].values() if r['role']=='translator_review')
    for data in readers['outputs'].values():assert sha(ROOT/data['path'])==data['sha256']
    visual={'date':'2026-10-18','source_pdf_pages_inspected':[205,296,320,480],
        'reader_sample_pages':[5,205,296,320,480,520,545,550],
        'details_inspected':['исправленные абзацы rr.p0205.b019 и rr.p0296.b034','легенда ветра PDF 320','четыре вложенные зоны схемы PDF 480','вся таблица PDF 520','начало оглавления и фрагменты указателей'],
        'viewport':[1500,1800],'text_width':1080,'metrics':metrics,
        'observations':'В просмотренных образцах не обнаружены обрезанные ячейки, горизонтальное переполнение или недоступные изображения. Английские подписи видны, исправленные абзацы читаются; схема сохраняет вложенность и подписи.',
        'full_visual_review':False,'full_new_semantic_review':False,
        'limits':'Просмотр выборочный; снимки и измерения не означают чтения каждой строки всей книги. Таблица 520 просмотрена целиком для оценки размещения, без новой смысловой вычитки каждой ячейки.'}
    (BASE/'RR_visual_review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf-8')
    result={
        'date':'2026-10-18','book':'ACKS II Revised Rulebook','source_pdf_pages':[1,550],
        'source_units':30624,'translated_units':30624,'pending_units':0,'chapters':12,'appendices':5,'complete_documents':18,
        'reader':human['path'],'reader_pdf_ranges':[[5,538],[545,550]],'reader_page_markers':540,
        'reader_source_units':sum(5<=u['pdf_page']<=538 or 545<=u['pdf_page']<=550 for u in units),
        'excluded_publishing_source_units':77,'canonical_reader':canonical['path'],'canonical_reader_pdf_pages':[5,550],
        'tables':370,'notes_total':751,'editorial_notes':750,'author_footnotes':1,'index_entries':862,'index_links':975,
        'legacy_comments':112,'legacy_comment_groups':legacy['comment_groups'],'legacy_comment_states':legacy['states'],'tracked_change_elements':26,
        'source_chapter_manifest':{ch['file']:{'source_units_present':ch['units'],'sha256':readers['source_chapter_manifest'][ch['file']]} for ch in structural['chapters']},
        'reader_sha256':human['sha256'],'canonical_reader_sha256':canonical['sha256'],
        'checks':{'all_database_units_translated':True,'database_verify':structural['database'],'all_550_EN_checked_page_bodies_equal_database':True,
            'all_source_ids_rendered_in_full_chapters':True,'normalized_rendered_russian_equals_database':True,
            'documented_sail_legend_addition':structural['documented_render_additions'],'all_370_table_grids_preserved':True,
            'all_current_csv_and_jsonl_exports_match_database':True,'all_notes_preserved':True,'visible_machine_markers':0,'reader_note_projections':readers['reader_note_projections'],'all_112_legacy_comments_accounted_for':True,
            'all_26_tracked_elements_accounted_for':True,'all_index_and_navigation_targets_exist':True,
            'all_protected_sources_and_glossaries_unchanged':True,'protected_files_checked':len(protected),
            'only_ten_database_records_changed':True,'unaffected_database_records':30614,'official_import_used':True,'human_approval_assigned':False},
        'integration':integration,'omissions':readers['human_omissions'],'visual_review':visual,
        'limits':'Полнота и сшивка проверены по всему подготовленному источнику. Это не новая сплошная смысловая или визуальная вычитка 550 страниц. Вопросы к оригиналу и рабочим названиям сохранены; они не объявлены решёнными человеком. Старые поэтапные отчёты описывают свои исторические состояния.'}
    (BASE/'full_book_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    (BASE/'RR_structural_validation.json').write_text(json.dumps(structural,ensure_ascii=False,indent=2)+'\n','utf-8')
    lines=['# Итоговая проверка полноты Revised Rulebook','', '18 октября 2026 года. Перевод сшит полностью по важному материалу подготовленного RR. В базе **30 624 из 30 624 единиц**, непереведённых разделов нет. Читательская версия включает введение, главы 1–12, приложения A–E, правила, таблицы, листы и указатели.','',
        '[Открыть полный перевод для вычитки](<../Перевод Markdown/ACKS II Revised Rulebook — версия для переводчиков.md>).','',
        '## Состав читательского файла','',
        'Физические PDF **5–538 и 545–550**, 540 маркеров страниц, **370 таблиц и 751 примечание**: 750 редакторских и одна авторская сноска. Это 30 547 единиц исходника, дополненных английскими подписями и примечаниями для переводчиков. Обложки, реклама, цена и выходные сведения PDF 1–4 (37 единиц) и памятный список спонсоров PDF 539–544 (40 единиц) оставлены в полных рабочих главах. Содержательное примечание обложки перенесено к классам, примечания списка спонсоров — к началу E. Правила и таблицы при этих исключениях не удалены.','',
        'Создана отдельная чистая копия «ACKS II Revised Rulebook — версия для переводчиков.md». Существующий «ACKS II Revised Rulebook — полный перевод для вычитки.md» и общий файл прежнего состава **PDF 5–550** сохранены со всеми техническими пояснениями. Во всех трёх версиях сохранены двуязычные заголовки, повторяемые подписи специальных терминов, исходные единицы измерения и печатные ссылки. Убраны служебные rr-ID. Указатели E сохраняют 862 записи и 975 ссылок; они ведут внутри читаемого файла.','',
        'В тексте для чтения нет видимых ID, хешей, названий промежуточных файлов и пояснений о базе. 34 технически сформулированные сноски получили читательскую редакцию с сохранением содержательного замечания. Их технические оригиналы остаются в полных рабочих главах; явные соответствия заданы в tools/rr_reader_notes.json. Проверка отображаемого текста — RR_clean_reader_validation.json. Для пересылки вне репозитория подготовлен [архив Markdown с иллюстрациями](<../Для ревью/ACKS II RR — перевод для ревью.zip>).','', '## Что исправлено','',
        '| Единица / физический PDF | Поправка |','| --- | --- |',
        '| `rr.p0205.b019`, PDF 205 | В «Круге агонии» исправлены «инициация», повтор некротического урона и повреждённая подпись цели; восстановлены спасбросок от смерти, выделение рассеивания и читаемое условие окончания эффекта. Проверено по EN checked и изображению PDF. |',
        '| `rr.p0296.b034`, PDF 296 | Attack sequence приведено к словарной «последовательности атак»; уточнены оставшийся на месте и не связанный боем боец, предел до 5 футов и особые манёвры. Проверено по EN checked и изображению PDF. |','',
        'Восемь предложений из прежних переводов возвращены примечаниями возле текста: Дева клинков / Танцор с клинками, Основы магии, Тренировка в доспехах, пильтбир, Наёмник Mercenary / Sell-sword, Учёный репертуар, Капище / Госпиталь, Засада / внезапный удар. Основной глоссарий не менялся. Десять затронутых записей импортированы штатным `database_tools.py import-chapter` после SQLite Backup API; исходные revision сохранены в [пакетах](../../contributions/rr-completeness/README.md). Остальные 30 614 записей и неизменяемые таблицы базы сохранены.','',
        '## Все прежние комментарии и поправки','',
        'Проверены 39 доступных DOCX относящихся к RR, исходникам и словарю. Извлечены **112 комментариев**, включая ответы и повторы, и **26 элементов отслеживаемых правок**. В PDF текстовых аннотаций нет. Каждой записи назначены текущие единицы или словарный контекст и объяснение результата.','',
        '**101 комментарий учтён в текущем тексте; 11 комментариев в девяти группах сохранены как вопросы.** Все 26 элементов отслеживаемых правок разобраны. Это не 112 независимых исправлений. Старое удаление параметров заклинания не применено вопреки новой английской редакции; буквенные изменения «картографу желательно, но не обязательно» уже отражены в правилах. Предложения новых названий не приняты за человеческое утверждение.','',
        '[Полный реестр с исходными комментариями](RR_прежние_комментарии.md), [машиночитаемые записи и контексты](RR_legacy_review.json).','',
        '## Проверки','',
        '- Все 550 тел страниц EN checked точно сопоставлены с исходными страницами SQLite; английские поля, ID и SHA-256 не менялись.',
        '- Все 30 624 ID присутствуют в 18 полных главах после рендеринга. Их русский текст совпал с базой после документированной нормализации оформления. Единственное дополнение — русская легенда схемы ветра PDF 320; все множители и угол сверены с PDF.',
        '- Проверены все 370 сеток таблиц: размеры, координаты, порядок, пустые позиции, rowspan/colspan. Текст таблиц и прозы сохранён при сборке.',
        '- Все примечания (751) присутствуют в читателе. 749 записей сводки соответствуют 750 редакторским примечаниям: одна запись объединяет два. Ещё одна сноска — авторская, о сменной работе гребцов.',
        '- CSV всех 18 разделов и units.jsonl совпадают с текущей базой. SQLite: integrity ok; ошибок связей, истории, поиска и английских хешей нет.',
        '- Все внутренние ссылки и локальные изображения доступны. Выборочно просмотрены русские области PDF 5, 205, 296, 320, 480, 520, 545, 550, отдельно два исправленных абзаца, легенда, схема и вся таблица PDF 520. В этих образцах нет горизонтального переполнения, обрезанных ячеек или недоступных изображений.','',
        'Подробности: [структура и база](RR_structural_validation.json), [сборка](RR_reading_validation.json), [примечания](RR_notes_validation.json), [визуальные образцы и пределы](RR_visual_review.json), [итоговый снимок](full_book_validation.json).','',
        '## Что остаётся за главным переводчиком','',
        'Сохранены все прежние вопросы к механике оригинала и рабочим терминам. Среди дополнительно обнаруженных словарных вопросов — повреждённое «тельстан» в Глоссарий.md при «Этельстан» в машинном словаре и переводе, предварительное Halt, варианты названий навыков и классов. Старые предложения по Засаде, Фокусничеству и Реликварианизму также не выданы за утверждённые замены. Сами правила не исправлялись догадкой.','',
        '**Предел проверки:** выполнены полный контроль состава и сборки и адресная сверка замечаний. Новая построчная смысловая вычитка всей книги и полный визуальный просмотр 550 страниц не выполнялись. Человеческое утверждение не присваивалось.','',
        '## Изменённые материалы','',
        'Новый читательский Markdown, общий файл прежнего состава, полные главы 02/03/04/05/06/08 и сводка примечаний; десять строк SQLite, units.jsonl и актуальные CSV (включая ранее отсутствовавший 02_review.csv); пакеты contributions/rr-completeness; сборщик tools/build_rr_reader.py; отчёты RR, README-PROJECT и bilingual_style. Исходные английские файлы, PDF/DOCX и утверждённый глоссарий не менялись. Отправка в существующий приватный репозиторий выполняется по отдельному поручению владельца.']
    (BASE/'RR_проверка_полноты.md').write_text('\n'.join(lines)+'\n','utf-8')
    packet='# Поправки итоговой сверки RR\n\n18 октября 2026 года. Пакеты по главам 02, 03, 04, 05, 06 и 08 содержат десять записей: две правки русского текста и восемь дополнений примечаний. CSV — UTF-8 с BOM и разделителем `;`, JSONL — UTF-8. ID, английский текст, source_sha256 и исходная revision сохранены.\n\n**Уже импортированы** через database_tools.py import-chapter. Повторно не импортировать: номера revision в этих пакетах описывают состояние до правки. Для дальнейшей работы выгружайте текущую главу из базы. Утверждение человеком не присваивалось.\n\nРезультаты и причины: [отчёт проверки](<../../ACKSII/База перевода/RR_проверка_полноты.md>). Точные исходные и итоговые редакции сохранены в истории SQLite.\n'
    (ROOT/'contributions/rr-completeness/README.md').write_text(packet,'utf-8')
    append='\n\n## Итоговая сверка RR — 18 октября 2026 года\n\nПосле завершения книги выполнена отдельная проверка состава и учёта прежних Word-комментариев. Текущие исправления, их ID и ограничения проверки — [RR_проверка_полноты.md](RR_проверка_полноты.md). Общий читатель пересобран; прежний текст этого отчёта сохраняет своё историческое состояние. Утверждение человеком не присваивалось.\n'
    for name in ('02_review.md','03_review.md','04_review.md','05_review.md','06_review.md','08_review.md','review.md'):
        path=BASE/name;text=path.read_text('utf-8')
        if '## Итоговая сверка RR — 18 октября' not in text:path.write_text(text.rstrip()+append,'utf-8')
    path=BASE/'bilingual_style.md';text=path.read_text('utf-8')
    if '## Читатель для человеческой вычитки' not in text:
        text+='\n\n## Читатель для человеческой вычитки — 18 октября 2026 года\n\n`ACKS II Revised Rulebook — версия для переводчиков.md` содержит PDF 5–538 и 545–550, 370 таблиц и 751 примечание. Издательские блоки и спонсоры исключены, их содержательные примечания сохранены. Все 12 глав и пять приложений идут по порядку. Служебные ID убраны; указатели ссылаются внутри читаемого файла. Рабочие названия и вопросы прежних переводчиков остаются рядом с текстом. Общий файл PDF 5–550 обновляется тем же сборщиком `tools/build_rr_reader.py`; старые поэтапные количества выше описывают историю. Проверка — RR_проверка_полноты.md.\n'
        path.write_text(text,'utf-8')
    print(json.dumps({'units':30624,'tables':370,'notes':751,'legacy_comments':112,'tracked_elements':26,'protected_files':len(protected),'report':'RR_проверка_полноты.md'},ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
