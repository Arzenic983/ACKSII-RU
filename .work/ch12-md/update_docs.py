"""Update chapter-12 navigation after successful import and reader assembly."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
assert json.loads((HERE/'integration.json').read_text('utf-8'))['translated_total']==28924
reader=json.loads((BASE/'reading_validation.json').read_text('utf-8'))
assert reader['compact_page_markers']==483 and reader['previous_reader_pages_5_473_unchanged']
p=ROOT/'README-PROJECT.md';s=p.read_text('utf-8')
assert '**28 115 единиц**' in s
s=s.replace('**28 115 единиц**','**28 924 единиц**').replace('1–11','1–12')
s=s.replace('**342 таблицы** и **633 примечания**','**351 таблицу** и **654 примечания**').replace('PDF 5–473','PDF 5–487').replace('PDF 5–461 сохранён','PDF 5–473 сохранён')
s=s.replace('469 маркеров PDF-страниц','483 маркера PDF-страниц')
s=s.replace('| Остальная книга | 474–550', '| Остальная книга | 488–550')
row='| Глава 11 «Сражения» | 462–473 | 618 / 618 | Проверено Codex |'
assert row in s;s=s.replace(row,row+'\n| Глава 12 «Осады» | 474–487 | 809 / 809 | Проверено Codex |')
line=next(line for line in s.splitlines() if line.startswith('- [11 Сражения.md]'))
s=s.replace(line,line+'\n- [12 Осады.md](<ACKSII/Перевод Markdown/12 Осады.md>) — PDF 474–487, ID `rr.p0474.b001`–`rr.p0487.t01.r015.c02`, 809 единиц, проверено и импортировано; [отчёт](<ACKSII/База перевода/12_review.md>).')
old='Глава 11 собирается `.work/ch11-md/build_chapter.py`; техническая проверка — `.work/ch11-md/validate.py`, порядок воспроизведения — `.work/ch11-md/README.md`.'
assert old in s;s=s.replace(old,old+' Глава 12 собирается `.work/ch12-md/build_chapter.py`; техническая проверка, включая восстановление PDF 480, — `.work/ch12-md/validate.py`, порядок — `.work/ch12-md/README.md`.')
s=s.replace('для главы 11 — на `11_validation.json`','для главы 12 — на `12_validation.json`')
old='Если задача касается дальнейшего перевода Revised Rulebook, следующая глава в базе — **12 «Осады», PDF 474–487**. Глава 11 завершена, проверена и импортирована; её пакет сохраняет исходную редакцию 0, база — редакцию 1.'
new='Если задача касается дальнейшего перевода Revised Rulebook, следующий раздел базы — **приложение A «Сеттинг», PDF 488–507**. Все основные главы 1–12 завершены, проверены и импортированы. Пакет главы 12 сохраняет исходную редакцию 0, база — редакцию 1.'
assert old in s;s=s.replace(old,new)
p.write_text(s,'utf-8')
p=BASE/'README.md';s=p.read_text('utf-8');tail=s.split('## Файлы',1)[1]
intro='''# База перевода ACKS II Revised Rulebook

На 17 октября 2026 года переведены и проверены начало книги и все основные главы 1–12: **PDF 1–487, 28 924 из 30 624 единиц**. Глава 12 «Осады» — 809/809, reviewed_by_Codex. Следующий раздел — приложение A «Сеттинг», PDF 488–507, pending. Вычитка Codex не означает утверждения человеком.

Для чтения — `../Перевод Markdown/ACKS II — Начало и главы 1–12.md`: PDF 5–487, 483 маркера страниц, 351 таблица, 654 примечания. Прежний диапазон PDF 5–473 сохранён без изменений; полные отдельные главы сохраняют ID.

Проверка главы 12: [12_review.md](12_review.md), [12_validation.json](12_validation.json); воспроизведение — `../../.work/ch12-md/README.md`. Пакеты `../../contributions/12/translator.csv` и `.jsonl` сохраняют revision 0; текущая база и 12_review.csv — revision 1. Старый пакет повторно не импортировать. Для главы 10 сведения об исключениях revision 2 остаются в 10_review.md.

Общий Markdown собирается `../../.work/reading-md/format_reading.py`; текущая проверка — [reading_validation.json](reading_validation.json). Дальнейшие описания прежних этапов и счётчиков исторические. При интеграции главы 12 сохранены английский источник, геометрия таблиц, утверждённый глоссарий и все переводы других глав. Перемешанные колонки PDF 480 восстановлены только в представлении с проверкой каждого фрагмента.

## Файлы'''
p.write_text(intro+tail,'utf-8')
p=BASE/'bilingual_style.md';s=p.read_text('utf-8');assert '## Продолжение до главы 12' not in s
s+='''
## Продолжение до главы 12 — 17 октября 2026 года

Текущая читательская копия — `../Перевод Markdown/ACKS II — Начало и главы 1–12.md`, PDF 5–487. Глава 12 сохраняет 809 единиц, 43 исходных заголовка, 9 таблиц и 21 примечание. Английский оригинал остаётся меньшей строкой под заголовками и в заголовках таблиц; специальные термины подписаны повторно, в том числе в примечаниях и схеме. В тегах урона русская и английская квадратные скобки стоят последовательно, без вложенности.

На PDF 480 исходное извлечение перемешало колонки и подписи схемы. `../../.work/ch12-md/source_parts.json` точно соединяется обратно в английские единицы; `presentation_parts.json` хранит соответствующие русские части. Все 30 единиц страницы отображены в 38 фрагментах, каждый ровно один раз. Заголовок DEPLOYING THE ARMIES восстановлен из заголовка и части абзаца, вложенная схема воспроизведена HTML-блоками без добавления таблицы. В полной главе фрагменты имеют `data-unit`/`data-part`; читательская копия удаляет эти служебные атрибуты. Английские ID, хеши и структура SQLite не менялись. Числовых исключений сопоставления нет.

Сохранён прежний диапазон PDF 5–473. Проверки — `12_validation.json` и `reading_validation.json`, отчёт — `12_review.md`. Новые осадные термины рабочие; утверждение человеком не назначено.
'''
p.write_text(s,'utf-8')
p=BASE/'bilingual_terms.md';s=p.read_text('utf-8');assert '## Глава 12: рабочая карта' not in s
s+='''
## Глава 12: рабочая карта — 17 октября 2026 года

PDF 474–487. Утверждённый глоссарий сохранён. Карта подписей — `../../.work/ch12-md/term_map.json`; сверка — `glossary_check.json` и `cross_chapter_evidence.json` там же. Новые формы ниже рабочие.

| English | Рабочая русская форма |
| --- | --- |
| siege / blockade / reduction / assault | осада / блокада / разрушение / штурм |
| besieging army / defending army | осаждающая армия / обороняющаяся армия |
| unit capacity | вместимость в подразделениях |
| structural hit points (shp) | конструкционные очки здоровья (КОЗ) |
| breach | брешь |
| circumvallation | циркумвалационная линия |
| siege-mine / countermine | осадный подкоп / контрподкоп |
| subversion | подрыв обороны |
| artillery duel | артиллерийская дуэль |
| assault turn | ход штурма |
| assaulting unit / defending unit | штурмующее подразделение / обороняющееся подразделение |
| breakthrough / sally | прорыв / вылазка обороняющихся |
| stronghold walls / stronghold interior | крепостные стены / внутренняя часть крепости |
| unit advantage / bonus units | преимущество в подразделениях / дополнительные подразделения |
| voluntary surrender / involuntary surrender | добровольная сдача / вынужденная сдача |

КОЗ, донжон, строительный проект и темп строительства согласованы с главой 4. Подъёмник, бур, ловец тарана, передвижная галерея, передвижной мантелет и осадный крюк сохраняют её названия с английскими подписями. Заклинания согласованы с главой 5; Земляная трясина [Earth’s Mire] соответствует прежней рабочей Земляной топи главы 4, что отмечено рядом с текстом. Rallied в правилах отхода означает восстановление строя; результат морали Rally и состояние Wavering остаются различёнными согласно главе 11. Имена Морувай и Баал Ужасный также рабочие.
'''
p.write_text(s,'utf-8')
print('Updated current navigation and working terminology through chapter 12.')
