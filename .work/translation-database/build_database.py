"""One-time database creation. Refuses to overwrite an existing database."""
import collections
import hashlib
import importlib.util
import json
import pathlib
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf8')
WORK = pathlib.Path(__file__).resolve().parent
ROOT = WORK.parents[1]
OUT = ROOT / 'ACKSII' / 'База перевода'
OUT.mkdir(exist_ok=True)
PATH = OUT / 'acksii_translation.sqlite'
if PATH.exists():
    raise SystemExit('Database already exists; use chapter import, never overwrite history.')

def read(name):
    return json.loads((WORK / (name + '.json')).read_text(encoding='utf8'))

spec = importlib.util.spec_from_file_location('database_tools', OUT / 'database_tools.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
AT = '2026-10-14'
units, tables, pages = read('all_units'), read('all_tables'), read('all_pages')
translations = {x['id']:x for x in read('translations_scope')}
glossary = read('glossary_import')
legacy = read('existing_chapter_01')
assert len(units)==30624 and len(pages)==550 and len(translations)==1689
assert not read('missing_translations')
boundaries = [('front_matter',1,13,'Front matter','Материалы перед первой главой'),('01',14,23,'Characters','Персонажи'),('02',24,101,'Classes','Классы'),('03',102,123,'Proficiencies','Навыки'),('04',124,179,'Equipment','Снаряжение'),('05',180,263,'Spells','Заклинания'),('06',264,315,'Adventures','Приключения'),('07',316,333,'Voyages','Плавания'),('08',334,427,'Campaigns','Кампании'),('09',428,447,'Armies','Армии'),('10',448,461,'Maneuvers','Манёвры'),('11',462,473,'Battles','Сражения'),('12',474,487,'Sieges','Осады'),('A',488,507,'Setting','Сеттинг'),('B',508,517,'Conditions','Состояния'),('C',518,531,'Wounds and Woe','Раны и бедствия'),('D',532,537,'Resources','Материалы для игры'),('E',538,550,'Index','Предметный указатель')]
sources = [
 ('rr_pdf','ACKSII/Source/ACKSII Revised Rulebook.pdf','original_pdf',None,'Оригинал; 550 физических страниц. Не изменён.'),
 ('rr_en','ACKSII/Source/ACKSII Revised Rulebook (EN checked).md','checked_english',None,'Исправленное извлечение; подробности и пределы проверки — в отчёте извлечения.'),
 ('glossary_docx','ACKSII/ReadMe.docx','project_glossary',read('readme'),'Словарь проекта; отдельно отмечены три решения пользователя.'),
 ('ch01_draft',legacy['path'],'existing_translation',legacy,'Исходный черновик Wiah согласно таблице прогресса. Сохранён отдельно от редакции Codex.'),
 ('progress_xlsx','ACKSII/Прогресс перевода.xlsx','project_progress',read('progress_snapshot'),'Снимок исходной таблицы; сам файл не изменён.'),
 ('obsidian_rar','ACKSII/Obsidian/ACKS2 (05).rar','existing_vault',None,'Архив содержит вариант того же черновика главы 1; сверка не выявила отдельного качественного перевода введения.')]
db = sqlite3.connect(PATH)
db.execute('PRAGMA foreign_keys=ON')
db.executescript((OUT/'schema.sql').read_text(encoding='utf8'))
draft_ids = {}
with db:
    for key,value in {'schema_version':'1','book':'ACKS II Revised Rulebook','created_at':AT,
                      'translation_scope':'front_matter,01','english_extraction_scope':'all 550 PDF pages',
                      'reviewer':'Codex','source_normalizations':json.dumps(read('source_normalizations'),ensure_ascii=False),
                      'glossary_policy':'ReadMe.docx; grammatical forms allowed; working labels are not approved glossary entries'}.items():
        db.execute('INSERT INTO metadata VALUES(?,?)',(key,value))
    for ident,rel,kind,snapshot,note in sources:
        path=ROOT/rel
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        db.execute('INSERT INTO sources VALUES(?,?,?,?,?,?)',(ident,path.relative_to(ROOT).as_posix(),kind,sha,json.dumps(snapshot,ensure_ascii=False) if snapshot else None,note))
    assert db.execute("SELECT sha256 FROM sources WHERE id='rr_pdf'").fetchone()[0]=='e9d8adb05281090e0455a0ea0e07f1d2e18eee8902a3cb6a34b23753056059da'
    label_map={line.split(' = ',1)[0].lower():line.split(' = ',1)[1] for line in (WORK/'labels_ru.txt').read_text(encoding='utf8').splitlines() if ' = ' in line}
    for cid,start,end,en,ru in boundaries:
        if cid!='front_matter':ru=label_map.get(en.lower(),ru)
        db.execute('INSERT INTO chapters VALUES(?,?,?,?,?,?)',(cid,en,ru,start,end,'reviewed_by_Codex' if cid in ('front_matter','01') else 'pending'))
    for p in pages:
        db.execute('INSERT INTO pages VALUES(?,?,?,?,?)',(p['page'],p['printed_page'],p['chapter'],p['anchor'],p['source_markup']))
    for table in tables:
        db.execute('INSERT INTO source_tables VALUES(?,?,?,?,?,?,?)',(table['id'],table['page'],table['chapter'],table['block_order'],table['rows'],table['columns'],table['source_markup']))
    for u in units:
        icons=[{'category':k,'type':t} for k,t in re.findall(r'\[(mundane|extraordinary) ([^\]]+)\]',u['plain'])]
        db.execute('INSERT INTO units VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
          (u['id'],u['chapter'],u['page'],u['order'],u['kind'],u['source'],u['plain'],u['source_sha256'],int(u['invariant']),u.get('table_id'),u.get('row'),u.get('column'),u.get('rowspan'),u.get('colspan'),u.get('heading_level'),json.dumps(icons,ensure_ascii=False)))
        db.execute('INSERT INTO unit_search VALUES(?,?,?)',(u['id'],u['plain'],''))
    for item in legacy['items']:
        raw=item['text'] if item['kind']=='paragraph' else '\n'.join(' | '.join(row) for row in item['rows'])
        cur=db.execute('INSERT INTO draft_fragments(source_id,locator,kind,raw_text,metadata_json) VALUES(?,?,?,?,?)',
              ('ch01_draft',item['locator'],item['kind'],raw,json.dumps(item,ensure_ascii=False)))
        draft_ids[item['locator']]=cur.lastrowid
        if item['kind']=='table':
            for row_index,row in enumerate(item['rows']):
                for col_index,cell in enumerate(row):
                    locator=f"{item['locator']}.r{row_index+1:03d}.c{col_index+1:02d}"
                    cur=db.execute('INSERT INTO draft_fragments(source_id,locator,kind,raw_text,metadata_json) VALUES(?,?,?,?,?)',
                      ('ch01_draft',locator,'table_cell',cell,json.dumps({'parent':item['locator'],'row':row_index,'column':col_index},ensure_ascii=False)))
                    draft_ids[locator]=cur.lastrowid
    # Map reviewed table cells to the old draft, including its different layout.
    table_map={'rr.p0016.t01':('body.29',-1),'rr.p0016.t02':('body.45',-1),
               'rr.p0019.t01':('body.117',0),'rr.p0020.t01':('body.125',0),
               'rr.p0020.t02':('body.131',0),'rr.p0021.t02':('body.151',0),
               'rr.p0021.t03':('body.153',0),'rr.p0022.t01':('body.157',0)}
    legacy_items={x['locator']:x for x in legacy['items']}
    class_order=['Assassin','Barbarian','Bard','Bladedancer','Crusader','Dwarven Craftpriest','Dwarven Vaultguard','Elven Nightblade','Elven Spellsword','Explorer','Fighter','Mage','Nobiran Wonderworker','Paladin','Priestess','Shaman','Thief','Venturer','Warlock','Witch','Zaharan Ruinguard']
    unit_map={u['id']:u for u in units}
    def normalized(s):
        return re.sub(r'\s+','',s.replace('–','-').replace('—','-').replace('**','').replace('*','')).casefold()
    for u in units:
        if u['id'] not in translations or u['kind']!='table_cell':continue
        locator=None
        if u['table_id'] in table_map:
            parent,offset=table_map[u['table_id']];ri=u['row']+offset;ci=u['column']
            if ri>=0:locator=f'{parent}.r{ri+1:03d}.c{ci+1:02d}'
        elif u['table_id']=='rr.p0021.t01':
            if u['row']==0:ri=0;ci=u['column']%2
            else:
                key=(u['table_id'],u['row'],u['column']-u['column']%2)
                name=next(x['plain'] for x in units if (x.get('table_id'),x.get('row'),x.get('column'))==key)
                ri=class_order.index(name)+1;ci=u['column']%2
            locator=f'body.149.r{ri+1:03d}.c{ci+1:02d}'
        if locator and locator in draft_ids:
            tr=translations[u['id']]
            raw=db.execute('SELECT raw_text FROM draft_fragments WHERE id=?',(draft_ids[locator],)).fetchone()[0]
            same=normalized(raw)==normalized(tr['ru'])
            tr['origin']='existing_reused' if same else 'existing_revised'
            tr['draft_locators'].append(locator)
            tr['note']='Сверено с английским оригиналом; текст и значения черновика сохранены с нормализацией оформления.' if same else 'Сверено с английским оригиналом и словарём; исправлено относительно черновика.'
    for tr in translations.values():
        assert unit_map[tr['id']]['source_sha256']==tr['source_sha256']
        note=tr.get('note','')
        if tr['id'] in ('rr.p0004.b001','rr.p0004.b002','rr.p0004.b003'):
            note='Три части единого названия; слово «Система» перенесено в начало русского названия.'
        if tr['id']=='rr.p0007.t01.r158.c01':
            note='Раздел Peoples: использована форма названия народа «Скизийцы» из полной записи Skysos в словаре.'
        values=(tr['id'],tr['ru'],tr['status'],tr['origin'],tr['reviewer'],1,note,AT)
        db.execute('INSERT INTO translations VALUES(?,?,?,?,?,?,?,?)',values)
        db.execute('INSERT INTO translation_revisions VALUES(?,?,?,?,?,?,?,?)',(tr['id'],1,tr['ru'],tr['status'],tr['origin'],tr['reviewer'],note,AT))
        for locator in tr['draft_locators']:
            assert locator in draft_ids,locator
            db.execute('INSERT OR IGNORE INTO unit_drafts VALUES(?,?,?,?)',(tr['id'],draft_ids[locator],tr['origin'],note))
    for i,term in enumerate(glossary,1):
        db.execute('INSERT INTO glossary VALUES(?,?,?,?,?,?,?,?,?,?)',(i,term['en'],term['ru'],term.get('ru_abbreviation'),term['category'],term['status'],term['raw_entry'],json.dumps(term['variants'],ensure_ascii=False),'glossary_docx',term['source_locator']))
        aliases={term['en'],re.sub(r'\s*\([A-Z]{2,4}\)$','',term['en'])}
        if term['en'].lower()=='elven spellswords':aliases.add('Elven Spellsword')
        if term['en']=='Auran (Empire)':aliases.add('Auran Empire')
        if term['en']=='Jutland (coast)':aliases.add('Jutland Coast')
        for alias in aliases:
            db.execute('INSERT INTO glossary_aliases VALUES(?,?)',(i,alias))
            pattern=re.compile(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',re.I)
            for uid,tr in translations.items():
                if pattern.search(unit_map[uid]['plain']):db.execute('INSERT OR IGNORE INTO unit_terms(unit_id,term_id) VALUES(?,?)',(uid,i))
    lookup=read('glossary_lookup')
    for line in (WORK/'labels_ru.txt').read_text(encoding='utf8').splitlines():
        if ' = ' not in line:continue
        en,ru=line.split(' = ',1)
        if en.lower() not in lookup:
            db.execute('INSERT OR REPLACE INTO working_labels VALUES(?,?,?,?)',(en,ru,'working','Рабочий перевод подписи или термина, которого нет в словаре; при переводе соответствующей главы нужно проверить контекст.'))
    issues=[
      (None,'glossary','open','В ReadMe.docx указано «Nobiran wonderworker — Нобирийский чудотворцец?». Вероятная опечатка и вопросительная помета.','В текущем переводе сохранено написание словаря. Предложение: Нобирийский чудотворец. Требует решения владельца словаря.'),
      (None,'glossary','open','В словаре есть предварительные пометы и варианты: Фокусничество?, Реликварианизм, Ведьма / Ворожей и другие.','Сохранены выбранные словарные формы и все исходные пометы; спорные варианты не выданы за утверждённые пользователем.'),
      ('rr.p0002.b006','source','open','На обложке оригинала указано 18 классов; в оглавлении и главе 2 перечислен 21 класс.','Переведено исходное число 18; это расхождение оригинала, а не ошибка извлечения.'),
      ('rr.p0020.b011','source','open','Ссылка на Appendix A (p. 487) ведёт к началу текста сеттинга; заставка приложения на печатной стр. 486.','Сохранена ссылка оригинала. В базе физическая и печатная нумерация хранятся отдельно.'),
      ('rr.p0019.t01.r002.c02','draft','resolved','В старом черновике скорость в бою для ненагруженного персонажа: 30 вместо 40 футов за раунд.','Исправлено: 40 футов за раунд, как в PDF.'),
      ('rr.p0016.b010','draft','resolved','Черновик связывал лимит Харизмы с наёмниками.','Исправлено: лимит относится к приспешникам (henchmen).'),
      ('rr.p0017.b023','draft','resolved','Черновик неверно описывал потерю бонусов при использовании оружия или доспехов без владения ими.','Исправлено: не применяются бонусы атрибутов к атаке и КБ; сохранены все прочие ограничения.'),
      ('rr.p0021.b004','draft','resolved','Черновик утверждал, что эльфы и нобирийцы не достигают взрослого возраста.','Исправлено: они не стареют дальше взрослого возраста.'),
      ('rr.p0016.b013','draft','resolved','В исходном переводе отсутствовал отдельный абзац о минимальном значении каждого ключевого атрибута.','Восстановлено: не менее 9 в каждом ключевом атрибуте плюс дополнительные требования класса.'),
      ('rr.p0018.b004','draft','resolved','Черновик путал перебрасывание костей здоровья и переписывание ОЗ.','Уточнены повторный бросок всех КЗ, минимум прироста +1 ОЗ и правила 10-го и последующих уровней.'),
      ('rr.p0020.b004','draft','resolved','Черновик подменял примеры комплектов предметов и ошибался в пересчёте фунтов.','Восстановлены исходные единицы и примеры: 6 железных шипов, 20 стрел. Добавленные метрические пересчёты удалены.'),
      ('rr.p0020.b015','draft','resolved','Черновик терял правило грамотности во всех известных языках.','Восстановлено: при Интеллекте не ниже среднего персонаж грамотен во всех языках, на которых говорит.'),
      ('rr.p0023.b007','draft','resolved','В черновике отсутствовало правило прерывания продолжительных занятий.','Восстановлено: обычно занятие можно прервать без штрафа или нарушения хода работы.'),
      ('rr.p0007.t01.r158.c01','glossary','resolved','Skysos в оглавлении обозначает народ, а не страну.','Использована словарная форма Скизийцы; Скизия сохраняется как название страны.'),
      (None,'review_scope','documented','Проверка английского извлечения всей книги: кодировки, специальные значки, таблицы, порядок и полнота текста.','Построчная смысловая вычитка английского оригинала вне PDF 1–23 не выполнялась. Дальнейшие главы имеют статус pending.')]
    db.executemany('INSERT INTO issues(unit_id,category,state,detail,resolution) VALUES(?,?,?,?,?)',issues)
db.close()
with module.connect(PATH) as checked:
    result=module.verify(checked)
    module.export(checked,OUT)
    result['pages']=checked.execute('SELECT count(*) FROM pages').fetchone()[0]
    result['tables']=checked.execute('SELECT count(*) FROM source_tables').fetchone()[0]
    result['glossary_entries']=checked.execute('SELECT count(*) FROM glossary').fetchone()[0]
    result['origins']={row[0]:row[1] for row in checked.execute('SELECT origin,count(*) FROM translations GROUP BY origin')}
    result['chapter_progress']=[dict(row) for row in checked.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')]
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='chapter_progress'},ensure_ascii=False,indent=2))
