"""Publish the checked transcription and its audit only after validation passes."""
import collections
import hashlib
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

WORK=pathlib.Path(__file__).resolve().parent
ROOT=WORK.parents[1]
SOURCE=ROOT/'ACKSII'/'Source'
CHECKED=SOURCE/'ACKSII Revised Rulebook (EN checked).md'
REPORT=SOURCE/'ACKSII Revised Rulebook — проверка извлечения.md'
checks=json.loads((WORK/'build-checks.json').read_text(encoding='utf8'))
counts=checks['counts']
assert counts['pages']==550 and counts['pages_payload_verified']==510
assert counts['visually_reviewed_image_pages']==40 and counts['tables']==361
assert not checks['flags'],checks['flags']
text=(SOURCE/'ACKSII Revised Rulebook (EN working text).md').read_text(encoding='utf8')
anchors=[int(x) for x in re.findall(r'<a id="pdf-page-(\d{4})"></a>',text)]
links=[int(x) for x in re.findall(r'ACKSII%20Revised%20Rulebook.pdf#page=(\d+)\)',text)]
assert anchors==list(range(1,551)) and links==anchors
bad=[c for c in text if (ord(c)<32 and c not in '\r\n\t') or 127<=ord(c)<160 or 0xE000<=ord(c)<=0xF8FF or c=='\ufffd']
assert not bad,collections.Counter(bad)
damage=collections.Counter(re.findall(r'\[(mundane|extraordinary) [^\]]+\]',text))
assert damage=={'mundane':275,'extraordinary':201},damage
assert all(p['body_chars']==p['used_chars'] for p in checks['pages'])
tables=json.loads((WORK/'tables.json').read_text(encoding='utf8'))
merged=0
for table in tables:
    if 'merged_cells' not in table:continue
    merged+=1
    nr,nc=len(table['ys'])-1,len(table['xs'])-1
    occupied=set()
    for cell in table['merged_cells']:
        r0,r1,c0,c1=cell['span'] or (cell['row'],cell['row']+1,cell['col'],cell['col']+1)
        for ri in range(r0,r1):
            for ci in range(c0,c1):
                assert (ri,ci) not in occupied,(table['page'],table['table'],ri,ci)
                occupied.add((ri,ci))
    assert len(occupied)==nr*nc,(table['page'],table['table'])
assert merged==counts['tables_with_merged_cells']==text.count('<table>')==47
source_hash=hashlib.file_digest((SOURCE/'ACKSII Revised Rulebook.pdf').open('rb'),'sha256').hexdigest()
native=json.loads((WORK/'corrected-collection-checks.json').read_text(encoding='utf8'))
assert not native['checks']
excluded=json.loads((WORK/'final-excluded-glyph-audit.json').read_text(encoding='utf8'))
assert not excluded['non_navigation']
preface='''# ACKS II Revised Rulebook — English source text

Checked against the supplied PDF on 14 October 2026. Each section below represents one physical PDF page; the printed page number is shown where present. In-text references retain the book’s printed page numbers.

Black damage pictograms are written as `[mundane …]`; red pictograms as `[extraordinary …]`. Their colour carries rules meaning. The words in brackets are transcription labels.

The book’s wording and numerical values are retained. Running headers and decorative page furniture are omitted. Image lettering and form fields are transcribed; repeated blank entry rows are omitted. Tables with merged cells use HTML within this Markdown file.

[Table of contents](#pdf-page-0005) · [Introduction](#pdf-page-0008) · [Characters](#pdf-page-0014) · [Classes](#pdf-page-0024) · [Proficiencies](#pdf-page-0102) · [Equipment](#pdf-page-0124) · [Spells](#pdf-page-0180) · [Adventures](#pdf-page-0264) · [Voyages](#pdf-page-0316) · [Campaigns](#pdf-page-0334) · [Armies](#pdf-page-0428) · [Maneuvers](#pdf-page-0448) · [Battles](#pdf-page-0462) · [Sieges](#pdf-page-0474) · [Appendices](#pdf-page-0488)

---

'''
text=preface+text[text.index('<a id="pdf-page-0001">'):]
normalization_file=ROOT/'.work/translation-database/source_normalizations.json'
if normalization_file.exists():
    before_normalization=text
    for patch in json.loads(normalization_file.read_text(encoding='utf8')):
        number=patch['page'];start=text.index(f'<a id="pdf-page-{number:04d}">')
        end=text.find('<a id="pdf-page-',start+10)
        if end<0:end=len(text)
        page=text[start:end];a,b=patch['before']
        if a in page and '\n\n'+b in page:
            page=page.replace(a,patch['after'],1).replace('\n\n'+b,'',1)
            text=text[:start]+page+text[end:]
    assert collections.Counter(c for c in text if c.isalnum())==collections.Counter(c for c in before_normalization if c.isalnum())
CHECKED.write_text(text,encoding='utf8')
final_hash=hashlib.sha256(CHECKED.read_bytes()).hexdigest()
validation={'source_sha256':source_hash,'transcription_sha256':final_hash,'checks':{
    'physical_pages':550,'native_text_pages_payload_checked':510,'image_pages_visually_reviewed':40,
    'page_links':550,'tables':361,'tables_with_merged_cells':47,'merged_spans':139,
    'source_grid_positions':22099,'unresolved_glyphs':0,'unplaced_body_characters':0,
    'damage_labels':dict(damage),'table_grid_errors':0,
}}
(WORK/'final-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
report=f'''# Revised Rulebook: проверка английского текста

Дата: 14 октября 2026 года.

Рабочий источник для перевода: [ACKSII Revised Rulebook (EN checked).md](ACKSII%20Revised%20Rulebook%20%28EN%20checked%29.md).

Исходный [PDF](ACKSII%20Revised%20Rulebook.pdf) содержит 550 физических страниц. Использован его собственный текстовый слой, с восстановлением кодировки встроенных шрифтов. Видимые надписи на страницах без полноценного текстового слоя сверены по изображениям.

| Проверка | Результат |
| --- | --- |
| Страницы и ссылки на PDF | 550 из 550, в исходном порядке |
| Страницы с полноценным текстовым слоем | 510; постраничная сверка букв и цифр до и после форматирования без расхождений |
| Обложки, разделители, иллюстрации, карта и игровые листы | 40 страниц просмотрены; надписи перенесены, пустые поля и повторные пустые строки описаны |
| Таблицы | 361; восстановлено распределение текста по 22 099 позициям сетки |
| Объединённые ячейки | 139 объединений в 47 таблицах; проверена полнота сеток без пересечений |
| Повёрнутые таблицы | 11 страниц приведены к правильному порядку чтения |
| Обозначения урона | 476: 275 обычного и 201 особого; сохранено значение цвета |
| Неразрешённые символы, служебные управляющие коды, потерянные фрагменты основного текста | 0 по итоговым проверкам |

Исправлены неверные Unicode-соответствия букв и малых прописных во встроенных шрифтах, дубли от теней заголовков, лигатуры, повреждённые маркеры списков и точки в оглавлении. Например, `dEX`, `Ac`, `nPc` восстановлены как `DEX`, `AC`, `NPC`. Дефект кодировки затрагивал {native['counts']['font_encoding_repairs']:,} выводимых символов PDF до удаления дублирующих слоёв.

Оглавление восстановлено по трём колонкам. Для основного текста учтены обычные и меняющиеся по высоте колонки, широкие таблицы, подписи и примечания. Включены фрагменты ниже стандартного текстового поля: подписи к цитатам, примечание на печатной стр. 271, сноска на стр. 333, строка Heavy Trebuchet на стр. 475 и крайние фрагменты таблицы на стр. 528. На стр. 479 исправлено смешение колонок и возвращена таблица модификаторов атак.

В 47 таблицах использована HTML-разметка с `colspan` и `rowspan`: она сохраняет объединённые заголовки наподобие «Mage Spell Progression». Остальные таблицы записаны обычным Markdown. Сохранены смысловые выделения, включая выбранные специализации Weapon Focus в шаблонах классов.

Чёрные значки урона переданы как `[mundane fire]` и аналогичные подписи; красные — как `[extraordinary fire]`. Номер PDF в каждом блоке обозначает физическую страницу файла. Числа в ссылках внутри правил обозначают печатные страницы книги.

Формулировки автора и числовые значения сохранены. Замеченные печатные опечатки также сохранены для сверки: на обороте обложки — «system that let you set up a trade routes», на стр. 479 — «Heroes can be move like units». На листе владения (PDF 536) подпись расчёта «Revenue per Family minus Expenses» перенесена буквально. Эти места следует учитывать при редактуре перевода.

Проверка охватывает извлечение, полноту текстового слоя, расположение таблиц и обнаруженные проблемные места. Буквы и цифры сверены автоматически на всех 510 текстовых страницах; визуально проверены все 40 страниц с малым количеством текста и выбранные страницы со сложной структурой. Сплошная ручная пословная корректура всех 550 страниц отдельно не проводилась. Для иллюстраций, географии карты и внешнего вида бланков используется исходный PDF.

SHA-256 исходного PDF: `{source_hash}`

Технические журналы и сценарии воспроизведения находятся в `.work/revised-rulebook-extraction/`; итоговая проверка — `final-validation.json`.
'''
REPORT.write_text(report,encoding='utf8')
print(json.dumps({'checked':str(CHECKED),'report':str(REPORT),'validation':validation},ensure_ascii=False,indent=2))
