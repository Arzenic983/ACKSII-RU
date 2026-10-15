import pathlib, sqlite3, re, json, collections, hashlib, subprocess, argparse, datetime, sys, importlib.util
from bilingual import Annotator, english_subtitle, is_subheading

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
NODE=pathlib.Path('C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
DB=BASE/'acksii_translation.sqlite'
STAMP='2026-10-15'

def records(path):
    text=path.read_text('utf-8')
    matches=list(re.finditer(r'<!-- unit: (rr\.[^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',text,re.S))
    ids=[m[1] for m in matches]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate ID in '+str(path))
    return {m[1]:m[2].strip() for m in matches}

def write_records(path, values):
    path.write_text('\n\n'.join(f'<!-- unit: {k} -->\n{v}' for k,v in values.items())+'\n','utf-8')

def normalize(id,text):
    # These are editorial harmonizations of the new chapter only.
    replacements={
      'сотворение отродья какодемона':'вызов отродья какодемона',
      'камень для пращи':'метание камня',
      'камнем для пращи':'метанием камня',
      'режущий удар':'рассекающий удар',
      'очарование гуманоида':'обольщение гуманоида',
      'земной нарост':'нарост земли',
      'губительная руна':'руна погибели',
      'Большие магические исследования':'Великие магические исследования',
      'магические конструкции':'магические конструкты',
      'Прятанье':'Прятание',
      'прятанье':'прятание',
      'военного масла':'зажигательного масла',
      'дротиками для метания':'метательными стрелками',
      'дротиков для метания':'метательных стрелок',
      'бесплатно изменить направление взгляда':'бесплатно развернуться',
      'Арголле':'Арголлэ',
      'чудотворццы':'чудотворцецы',
      'кистенями-дубинками':'дубинками для оглушения',
      'Значения Интеллекта учёных заклинателей':'Интеллект учёных заклинателей',
      'Значения Интеллекта тайных заклинателей':'Интеллект учёных заклинателей',
    }
    for a,b in replacements.items(): text=text.replace(a,b)
    if id=='rr.p0027.b008':text=text.replace('относится к большим топорам','относится к секирам')
    if id=='rr.p0082.b010':text=text.replace('большими топорами','секирами').replace('большие топоры','секиры')
    if id=='rr.p0034.b010':text=text.replace('**подкрадывающимся**','**крадущимся**')
    if id=='rr.p0032.b014':text=text.replace('[обычный дробящий]','[обычного дробящего]')
    if id=='rr.p0039.b013':text=text.replace('если во время подчинения крестоносец изгоняет эту нежить','если во время подчинения эту нежить успешно изгонит любой крестоносец')
    if id=='rr.p0080.b008':text=text.replace('произносить заклинания зачарования едва слышными словами и без жестов','произносить заклинания зачарования, беззвучно проговаривая слова и не делая жестов')
    if id=='rr.p0076.b015':text=text.replace('Тотемного преимущества он не получает','Колдун не получает тотемного преимущества')
    if id in {'rr.p0044.b001','rr.p0045.b004'}:
        text=text.replace('маршрут может связывать новые рынки для торговли прежними товарами','маршрут может служить торговле прежними товарами на одном новом рынке или на новых рынках')
    if id=='rr.p0044.b002':
        text=text.replace('Если торговец допустит накопление процентных платежей до суммы в зм, превышающей его общий опыт,','Если торговец допустит накопление невыплаченных процентов и сумма его долга в зм превысит его общий опыт,')
    if id=='rr.p0090.b007':text=text.replace('участвовать в махинациях','заниматься происками')
    if id in {'rr.p0095.b015','rr.p0095.b021','rr.p0098.b007','rr.p0096.b003'}:
        text=text.replace('Закону','Порядку').replace('Закона','Порядка').replace('Закон','Порядок')
    # The unit symbol is the same throughout the chapter; decimal/dice values are untouched.
    text=re.sub(r'\bст(?![а-яёА-ЯЁ.])', 'ст.',text)
    return text

def note_map():
    notes=collections.defaultdict(list)
    for a in json.loads((ROOT/'.work/ch01-readable/annotations.json').read_text('utf-8')):
        notes[a['unit_id']].append(a['text'])
    for name in ('notes_B.md','notes_A_42_45_B.md','notes_C.md'):
        for line in (HERE/name).read_text('utf-8').splitlines():
            if not line.startswith('- ') or ' — ' not in line:continue
            loc,text=line[2:].split(' — ',1)
            for id in re.findall(r'rr\.p\d{4}\.(?:b\d{3}|t\d{2}\.r\d{3}\.c\d{2})',loc):notes[id].append(text)
    for id,text in records(HERE/'notes_D.md').items(): notes[id].append(text)
    notes['rr.p0025.b004'].append('Словарное написание «Нобирийский чудотворцец» сохранено, включая вероятную опечатку. Нормативная форма «Нобирийский чудотворец» пока не внесена в глоссарий.')
    notes['rr.p0025.b005'].append('Названия шаблонов, заклинаний и способностей, отсутствующие в глоссарии проекта, являются рабочими переводами. Они не объявлены утверждёнными дополнениями к глоссарию.')
    notes['rr.p0037.b009'].append('Так напечатано в PDF: здесь дополнительное заклинание названо последним, а на PDF-странице 25 — вторым. Для шаблона «Эрудит» с тремя заклинаниями это разные позиции. Противоречие оригинала сохранено; самостоятельно менять состав шаблона не следует.')
    notes['rr.p0039.b013'].append('Уточнено по оригиналу: подчинение снимает успешное изгнание любым крестоносцем, а не только тем, кто подчинил нежить.')
    notes['rr.p0037.b011'].append('Sling Stone передано рабочим названием «Метание камня»: по описанию на PDF-странице 247 заклинатель магически метает имеющиеся небольшие предметы.')
    notes['rr.p0072.b001'].append('В оригинале КЗ тотема на одну меньше КЗ шамана, но пример на этой же PDF-странице даёт тотему 13 КЗ при шамане 14-го уровня. Это расходится с прекращением прироста КЗ шамана после 9-го уровня. Оба положения оригинала сохранены; формулу не заменяли на «уровень минус один».')
    notes['rr.p0077.b003'].append('Ссылка оригинала на «Intellect Scores of Arcane Spellcasters» уточнена до фактического названия раздела в начале главы — «Интеллект учёных заклинателей» (PDF-страница 25).')
    notes['rr.p0044.b002'].append('Порог погони передан как сумма долга при накоплении невыплаченных процентов: английское «he owes more» и следующий пример учитывают долг, а не только накопленные проценты. Эта формулировка сохраняет неоднозначность источника, не вводя более узкого ограничения.')
    notes['rr.p0072.t01.r004.c04']=[n.replace('Требуется сверка с оригинальной вёрсткой или авторской правкой.','Вёрстка PDF-страницы 72 проверена: такая же запись напечатана в оригинале. Корректное значение остаётся вопросом к авторской эррате.') for n in notes['rr.p0072.t01.r004.c04']]
    return dict(notes)

def numeric_tokens(text):
    # Compare numerical values, accepting comma and space thousands separators.
    text=re.sub(r'(?<=\d)[ \u00a0\u202f](?=\d{3}(?:\D|$))','',text)
    text=re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))','',text)
    return collections.Counter(re.findall(r'\d+(?:[.,]\d+)?',text))

def get_data():
    db=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    units=[dict(r) for r in db.execute('SELECT * FROM units WHERE pdf_page<=101 ORDER BY pdf_page,block_order,row_index,column_index,id')]
    pages={r['pdf_page']:dict(r) for r in db.execute('SELECT * FROM pages WHERE pdf_page<=101')}
    tables={r['id']:dict(r) for r in db.execute('SELECT * FROM source_tables WHERE pdf_page<=101')}
    existing={r['unit_id']:r['text_ru'] for r in db.execute('SELECT * FROM translations')}
    files=['automatic.md','generic_A.md','labels_A.md',*[f.name for f in sorted(HERE.glob('manual_A_*.md'))], 'translated_A_42_45.md','translated_B.md','translated_C.md','translated_D.md']
    new={}
    for name in files:new.update(records(HERE/name))
    expected={u['id'] for u in units if u['chapter_id']=='02'}
    if set(new)!=expected:raise ValueError({'missing':sorted(expected-set(new)),'extra':sorted(set(new)-expected)})
    new={u['id']:normalize(u['id'],new[u['id']]) for u in units if u['chapter_id']=='02'}
    if any(not v.strip() for v in new.values()):raise ValueError('Empty translation')
    english_errors=[u['id'] for u in units if hashlib.sha256(u['source_markup'].encode()).hexdigest()!=u['source_sha256']]
    num_errors=[u['id'] for u in units if u['chapter_id']=='02' and numeric_tokens(u['source_markup'])!=numeric_tokens(new[u['id']])]
    if english_errors or num_errors:raise ValueError({'english_hash':english_errors,'numbers':num_errors})
    # Pre-existing chapters are copied verbatim from their reviewed database records.
    text={u['id']:new[u['id']] if u['chapter_id']=='02' else existing[u['id']] for u in units}
    db.close()
    return units,pages,tables,text,new

def render_table(table,cells,text,inline,notes):
    rows=collections.defaultdict(list)
    for u in cells:rows[u['row_index']].append(u)
    merged=any((u['rowspan'] or 1)>1 or (u['colspan'] or 1)>1 for u in cells)
    out=[f'<!-- table: {table["id"]}; rows: {table["row_count"]}; columns: {table["column_count"]} -->']
    foot=[]
    if merged:
        out.append(f'<table id="{table["id"]}">')
        for rid in range(table['row_count']):
            out.append('<tr>')
            for u in sorted(rows[rid],key=lambda x:x['column_index']):
                id=u['id'];tag='th' if rid==0 else 'td'
                attrs=f' id="{id}"'
                if (u['rowspan'] or 1)>1:attrs+=f' rowspan="{u["rowspan"]}"'
                if (u['colspan'] or 1)>1:attrs+=f' colspan="{u["colspan"]}"'
                mark=''
                for note in notes.get(id,[]):
                    n=len(foot)+1;mark+=f'<sup>*{n}</sup>';foot.append((n,id,note))
                out.append(f'<{tag}{attrs}><!-- unit: {id} -->{inline[id]}{mark}</{tag}>')
            out.append('</tr>')
        out.append('</table>')
    else:
        for rid in range(table['row_count']):
            cols=[]
            for u in sorted(rows[rid],key=lambda x:x['column_index']):
                id=u['id'];value=text[id].replace('|',r'\|').replace('\n','<br>')
                mark=''
                for note in notes.get(id,[]):
                    n=len(foot)+1;mark+=f'<sup>*{n}</sup>';foot.append((n,id,note))
                cols.append(f'<!-- unit: {id} --><a id="{id}"></a>{value}{mark}')
            out.append('| '+' | '.join(cols)+' |')
            if rid==0:out.append('| '+' | '.join(['---']*table['column_count'])+' |')
    for n,id,note in foot:out.extend(['','> '+chr(92)+f'*{n} `{id}` — {note}'])
    return '\n'.join(out)

def render_chapter(cid,title,units,pages,tables,text,inline,notes):
    chosen=[u for u in units if u['chapter_id']==cid]
    out=[f'# {title}','',f'Перевод по подготовленной базе. Редакция: {STAMP}. Номера в ссылках внутри правил сохранены по печатному оригиналу; ниже отдельно указаны физические PDF-страницы. Сноски со звёздочками расположены рядом с соответствующим текстом.','']
    done=set()
    for page in sorted(p for p in pages if pages[p]['chapter_id']==cid):
        printed=pages[page]['printed_page']
        out.extend([f'<a id="pdf-page-{page:04d}"></a>','',f'## PDF-страница {page}'+(f' · печатная стр. {printed}' if printed is not None else ''),'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        if not any(u['pdf_page']==page for u in chosen):
            out.extend(['<!-- На этой странице нет текстовых единиц подготовленного исходника. -->',''])
        for u in [u for u in chosen if u['pdf_page']==page]:
            id=u['id']
            if u['table_id']:
                tid=u['table_id']
                if tid in done:continue
                done.add(tid)
                out.extend([render_table(tables[tid],[v for v in chosen if v['table_id']==tid],text,inline,notes),''])
                continue
            out.extend([f'<!-- unit: {id} -->',f'<a id="{id}"></a>',''])
            value=text[id]
            if u['kind']=='heading':value='#'*min(6,max(3,u['heading_level'] or 3))+' '+value
            if notes.get(id):value+='<sup>*</sup>'
            if u['kind']=='heading' or is_subheading(u):value+='\n\n'+english_subtitle(u)
            out.extend([value,''])
            for note in notes.get(id,[]):out.extend(['> '+chr(92)+'* '+note,''])
    return '\n'.join(out).rstrip()+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--commit',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    units,pages,tables,pure_text,new=get_data();notes=note_map()
    annotator=Annotator(DB,units,pure_text)
    text=annotator.decorate(units,pure_text)
    for u in units:
        if u['table_id'] and u['row_index']==0 and re.search(r'[A-Za-z]{2,}',u['source_plain']):
            text[u['id']]+='<br>'+english_subtitle(u)
    notes={id:[annotator.annotate(id,n,next(u['source_plain'] for u in units if u['id']==id)+' '+n,track=False) for n in values] for id,values in notes.items()}
    annotator.write_catalog(BASE/'bilingual_terms.md')
    if not set(notes)<=set(text):raise ValueError('Notes reference missing units')
    write_records(HERE/'normalized_units.md',new)
    node=subprocess.run([str(NODE),str(HERE/'render_inline.mjs')],input=json.dumps(text,ensure_ascii=False),text=True,encoding='utf-8',capture_output=True,check=True)
    inline=json.loads(node.stdout)
    docs={}
    for cid,title,name in [('front_matter','Материалы перед первой главой','00 Начало.md'),('01','Глава 1. Персонажи','01 Персонажи.md'),('02','Глава 2. Классы','02 Классы.md')]:
        docs[cid]=render_chapter(cid,title,units,pages,tables,text,inline,notes)
        subtitle={'front_matter':'FRONT MATTER','01':'CHAPTER 1: CHARACTERS','02':'CHAPTER 2: CLASSES'}[cid]
        docs[cid]=docs[cid].replace('# '+title+'\n','# '+title+'\n\n<small>'+subtitle+'</small>\n',1)
        (OUT/name).write_text(docs[cid],'utf-8')
    combined='# ACKS II — Начало и главы 1–2\n\n<small>ACKS II — FRONT MATTER AND CHAPTERS 1–2</small>\n\nРедакция перевода: 15 октября 2026 года. Охват: PDF-страницы 1–101. Идентификаторы единиц, порядок исходного текста, ссылки на оригинал и размеры таблиц сохранены.\n\n'
    combined+='\n\n---\n\n'.join(docs[cid] for cid in ('front_matter','01','02'))
    combined_path=OUT/'ACKS II — Начало и главы 1–2.md';combined_path.write_text(combined,'utf-8')
    note_text='# Примечания редактора\n\n<small>EDITORIAL NOTES</small>\n\nЭти же примечания помещены сносками со звёздочками рядом с соответствующим текстом в отдельных главах и общем документе.\n\n'
    note_text+='\n\n'.join(f'<!-- unit: {u["id"]} -->\n'+'\n\n'.join(notes[u['id']]) for u in units if u['id'] in notes)
    (OUT/'Примечания редактора.md').write_text(note_text+'\n','utf-8')
    expected=[u['id'] for u in units]
    found=re.findall(r'<!-- unit: ([^ ]+) -->',combined)
    if found!=expected:raise ValueError('Combined unit order mismatch')
    protected=json.loads((HERE/'protected_docx_hashes.json').read_text('utf-8'))
    changed_docx=[s for s,h in protected.items() if hashlib.sha256((ROOT/s).read_bytes()).hexdigest()!=h]
    if changed_docx:raise ValueError('Protected DOCX changed')
    result={'date':STAMP,'chapter_id':'02','pdf_pages':[24,101],'source_units':len(new),'translated_units':len(new),'pending_units':0,'combined_units':len(units),'chapter_tables':sum(t['chapter_id']=='02' for t in tables.values()),'chapter_table_cells':sum(u['chapter_id']=='02' and u['table_id'] is not None for u in units),'combined_tables':len(tables),'editor_note_locations':len(notes),'editor_notes':sum(map(len,notes.values())),'unit_order_and_coverage':'passed','numeric_values':'passed','english_hashes':'passed','protected_docx_count':len(protected),'changed_docx':changed_docx,'docx_created':False,'docx_updated':False,'committed':False,'output':str(combined_path.relative_to(ROOT))}
    # Table geometry must match every occupied cell, including rowspan/colspan.
    for tid,t in tables.items():
        occupied=set()
        for u in [v for v in units if v['table_id']==tid]:
            for r in range(u['row_index'],u['row_index']+(u['rowspan'] or 1)):
                for c in range(u['column_index'],u['column_index']+(u['colspan'] or 1)):
                    if (r,c) in occupied or r>=t['row_count'] or c>=t['column_count']:raise ValueError('Table geometry: '+tid)
                    occupied.add((r,c))
        if len(occupied)!=t['row_count']*t['column_count']:raise ValueError('Table missing cells: '+tid)
    result['table_geometry']='passed'
    result['bilingual_term_annotations']=sum(annotator.stats.values())
    result['bilingual_term_variants']=len(annotator.stats)
    result['bilingual_source_headings']=sum(u['kind']=='heading' for u in units)
    result['bilingual_source_subheadings']=sum(is_subheading(u) for u in units)
    result['bilingual_table_headers']=sum(bool(u['table_id'] and u['row_index']==0 and re.search(r'[A-Za-z]{2,}',u['source_plain'])) for u in units)
    (HERE/'bilingual_annotation_audit.json').write_text(json.dumps(dict(annotator.by_unit),ensure_ascii=False,indent=2),'utf-8')
    if args.commit:
        backup=HERE/'before_chapter02.sqlite'
        db=sqlite3.connect(DB);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
        if not backup.exists():
            with sqlite3.connect(backup) as dest:db.backup(dest)
        at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        with db:
            unit_by_id={u['id']:u for u in units}
            for id,value in new.items():
                old=db.execute('SELECT * FROM translations WHERE unit_id=?',(id,)).fetchone()
                if old and old['text_ru']==value and old['status']=='reviewed':continue
                rev=(old['revision'] if old else 0)+1
                note='Перевод главы 2 в Markdown; сверены исходник, глоссарий, числовые значения и структура таблиц. Редакторские сноски находятся рядом с текстом в Markdown.'
                origin='manual_edit' if old else ('invariant' if unit_by_id[id]['invariant'] else 'new_translation')
                values=(id,value,'reviewed',origin,'Codex',rev,note,at)
                db.execute('INSERT INTO translations VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(unit_id) DO UPDATE SET text_ru=excluded.text_ru,status=excluded.status,origin=excluded.origin,reviewer=excluded.reviewer,revision=excluded.revision,note=excluded.note,updated_at=excluded.updated_at',values)
                db.execute('INSERT INTO translation_revisions VALUES(?,?,?,?,?,?,?,?)',(id,rev,value,'reviewed',values[3],'Codex',note,at))
            db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='02'")
            working={'Dart':'Метательная стрелка','Javelin':'Дротик','Great Axe':'Секира','Military Oil':'Зажигательное масло','Hiding':'Прятание','Trapbreaking':'Обезвреживание ловушек','Minor Magical Research':'Малые магические исследования','Major Magical Research':'Великие магические исследования','Supreme Magical Research':'Высшие магические исследования','Sling Stone':'Метание камня','Conjure Cacodemon Spawn':'Вызов отродья какодемона','Slicing Blow':'Рассекающий удар','Earth’s Excrescence':'Нарост земли','Beguile Humanoid':'Обольщение гуманоида','Bane-rune':'Руна погибели','Inspire Courage':'Внушение отваги','Inspire Hope':'Внушение надежды','Jack of All Trades':'Мастер на все руки','Savage Resilience':'Дикая живучесть','Arcane Striking':'Тайный удар','Death Healing':'Исцеление смертью','Spell Storing':'Хранение заклинания'}
            for en,ru in working.items():
                db.execute('INSERT OR IGNORE INTO working_labels VALUES(?,?,?,?)',(en,ru,'working','Рабочая форма при переводе главы 2, 15 октября 2026 года. Не является утверждённым дополнением к глоссарию.'))
        spec=importlib.util.spec_from_file_location('database_tools',BASE/'database_tools.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result['database']=module.verify(db)
        (BASE/'progress.json').write_text(json.dumps([dict(r) for r in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')],ensure_ascii=False,indent=2),'utf-8')
        with (BASE/'units.jsonl').open('w',encoding='utf-8',newline='\n') as f:
            for r in db.execute('SELECT * FROM bilingual ORDER BY pdf_page,block_order,row_index,column_index,id'):f.write(json.dumps(dict(r),ensure_ascii=False)+'\n')
        result['committed']=True
        db.close()
    (HERE/'markdown_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    main()
