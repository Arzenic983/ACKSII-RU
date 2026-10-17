"""Build current RR reading copies from all 18 complete chapters; never write SQLite.

Unlike the historical incremental builder, this command permits documented edits
to earlier chapters. It checks current source text, notes, tables and references.
"""
from pathlib import Path
from collections import Counter
from html import escape
from html.parser import HTMLParser
from urllib.parse import unquote
import hashlib, json, os, re, shutil, subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
CANONICAL=OUT/'ACKS II — Начало, главы 1–12 и приложения A–E.md'
REVIEW_SOURCE=OUT/'ACKS II Revised Rulebook — полный перевод для вычитки.md'
HUMAN=OUT/'ACKS II Revised Rulebook — версия для переводчиков.md'
WORK=ROOT/'.work/rr-completeness'
NODE=os.environ.get('ACKS_NODE') or shutil.which('node') or 'C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
PAGE=re.compile(r'<a id="pdf-page-(\d{4})"></a>\s*## PDF-страница (\d+)(?: · печатная стр\. (\d+))?\s*\[Английский оригинал: PDF-страница \d+\]\([^\n]+\)\s*')
REDUNDANT={9:('Введение','INTRODUCTION'),15:('Персонажи','CHARACTERS'),25:('Классы','CLASSES'),103:('Навыки','PROFICIENCIES'),125:('Снаряжение','EQUIPMENT'),181:('Заклинания','SPELLS'),265:('Приключения','ADVENTURES'),317:('Плавания','VOYAGES'),335:('Кампании','CAMPAIGNS'),429:('Армии','ARMIES'),449:('Манёвры','MANEUVERS'),463:('Сражения','BATTLES'),475:('Осады','SIEGES'),489:('Сеттинг','SETTING'),509:('Состояния','CONDITIONS'),519:('Раны и страдания','WOUNDS AND WOE')}
NOTE_PROJECTIONS=json.loads((ROOT/'tools/rr_reader_notes.json').read_text('utf-8'))

def clean(s, project_notes=True):
    s=re.sub(r'<!-- (?:unit:|table:)[^>]*-->\s*','',s)
    s=re.sub(r'<a id="rr\.[^"]+"></a>\s*','',s)
    s=re.sub(r' id="rr\.[^"]+"','',s)
    s=re.sub(r' data-(?:unit|part)="[^"]*"','',s)
    s=re.sub(r'`rr\.p\d{4}\.t\d{2}\.r\d{3}\.c\d{2}` — ','',s)
    s=re.sub(r'`rr\.p(\d{4})[^`]*`',lambda m:'PDF '+str(int(m[1])),s)
    s=re.sub(r'rr\.p(\d{4})\.(?:b\d{3}|t\d{2}(?:\.r\d{3}\.c\d{2})?)',lambda m:'PDF '+str(int(m[1])),s)
    s=s.replace('<!-- Original page contains illustration only; no source translation units. -->','')
    s=s.replace('<!-- На этой странице нет текстовых единиц подготовленного исходника. -->','')
    if project_notes:
        for note in NOTE_PROJECTIONS:s=s.replace(note['original'],note['reading'])
    return re.sub(r'\n{3,}','\n\n',s).strip()

def notes(s, project_notes=True):return [clean(line,project_notes=project_notes) for line in s.splitlines() if line.startswith('> ')]
def tables(s):return re.findall(r'<table(?: [^>]*)?>.*?</table>',s,re.S)+re.findall(r'^\|[^\n]*(?:\n\|[^\n]*)*',s,re.M)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.assets=[];self.tables=0
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if t=='a' and a.get('href','').startswith('#'):self.links.append(a['href'][1:])
        if t=='img':self.assets.append(a.get('src',''))
        if t=='table':self.tables+=1

def render(s):
    return subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=s,text=True,encoding='utf-8',capture_output=True,check=True).stdout

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    progress=json.loads((BASE/'progress.json').read_text('utf-8'))
    assert [ch['id'] for ch in progress]==['front_matter']+[f'{n:02}' for n in range(1,13)]+list('ABCDE')
    assert sum(ch['source_units'] for ch in progress)==sum(ch['translated_units'] for ch in progress)==30624
    paths=[OUT/('00 Начало.md' if ch['id']=='front_matter' else ch['id']+' '+ch['title_ru']+'.md') for ch in progress]
    manifest={str(p.relative_to(ROOT)):sha(p) for p in paths}
    sources=[p.read_text('utf-8') for p in paths]
    technical_source=clean('\n\n'.join(sources),project_notes=False)
    for note in NOTE_PROJECTIONS:
        assert technical_source.count(note['original'])==1,('Projection must match exactly one source note',note['pdf_page'])
    all_notes=notes('\n\n'.join(sources));raw_notes=notes('\n\n'.join(sources),False)
    cover_note=next(n for n in raw_notes if 'На обложке оригинала указано 18 классов' in n)
    pages={};printed={};raw_bodies={}
    for ch,s in zip(progress,sources):
        matches=list(PAGE.finditer(s))
        assert [int(m[1]) for m in matches]==list(range(ch['first_pdf_page'],ch['last_pdf_page']+1))
        for i,m in enumerate(matches):
            n=int(m[1]);body=s[m.end():matches[i+1].start() if i+1<len(matches) else len(s)]
            body=re.sub(r'\n---\s*$','',body)
            body=clean(body,project_notes=False);raw_bodies[n]=body;printed[n]=int(m[3]) if m[3] else None
            if n in REDUNDANT:
                ru,en=REDUNDANT[n];repeated=f'### {ru}\n\n<small>{en}</small>'
                assert repeated in body,(n,repeated);body=body.replace(repeated,'',1).strip()
            body=re.sub(r'^(#{3,6}) ',lambda m:m[1][1:]+' ',body,flags=re.M)
            if ch['id']!='front_matter' and n==ch['first_pdf_page']:
                title=('Глава '+str(int(ch['id']))+'. ' if ch['id'].isdigit() else 'Приложение '+ch['id']+'. ')+ch['title_ru']
                body,count=re.subn(r'^## [^\n]+?(<sup>\*</sup>)?\n\n<small>([^\n]+)</small>',lambda m:'# '+title+(m[1] or '')+'\n\n<small>'+m[2]+'</small>',body,count=1,flags=re.M)
                assert count==1,n
            if n==25:
                p=re.search(r'^В \*\*\*Adventurer Conqueror King System\*\*\*[^\n]+',body,re.M);assert p
                body=body[:p.end()]+'<sup>*</sup>\n\n'+cover_note+body[p.end():]
            pages[n]=body
    assert sorted(pages)==list(range(1,551))
    # Apart from documented heading presentation and the relocated cover note,
    # every prose token and every table remains in its original page body.
    for n in range(5,551):
        def prose(t):
            t=re.sub(r'^#{1,6} [^\n]+\n\n<small>[^\n]+</small>','',t,flags=re.M)
            return re.sub(r'\s+',' ',t).strip()
        before=raw_bodies[n]
        after=pages[n]
        if n==25:
            after=after.replace(cover_note,'',1)
            after=re.sub(r'(^В \*\*\*Adventurer Conqueror King System\*\*\*[^\n]+)<sup>\*</sup>',r'\1',after,count=1,flags=re.M)
        assert prose(before)==prose(after),('prose changed',n)
        assert tables(before)==tables(pages[n]),('table changed',n)
    def marker(n):
        title=f'Страница PDF {n}'+(f' · печатная стр. {printed[n]}' if printed[n] is not None else '')
        return f'<p align="right" id="pdf-page-{n:04d}"><small><a href="../Source/ACKSII%20Revised%20Rulebook.pdf#page={n}" title="{escape(title)}">страница {n}</a></small></p>'
    def assemble(title,selected,bodies):
        result=title+'\n\n'+'\n\n---\n\n'.join(marker(n)+('\n\n'+bodies[n] if bodies[n] else '') for n in selected)+'\n'
        # Both reading files must navigate within themselves.
        result=re.sub(r'href="[^"#]*#pdf-page-(\d{4})"',r'href="#pdf-page-\1"',result)
        return result
    canonical=assemble('# ACKS II — Начало, главы 1–12 и приложения A–E\n\n<small>ACKS II — FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–E</small>',list(range(5,551)),pages)
    assert Counter(notes(canonical,False))==Counter(raw_notes)
    assert Counter(notes(canonical))==Counter(all_notes)
    selected=[n for n in range(5,551) if not 539<=n<=544]
    human_bodies=dict(pages)
    omitted_notes=[note for n in range(539,545) for note in notes(pages[n],False)]
    if omitted_notes:human_bodies[538]+='\n\n'+ '\n\n'.join(omitted_notes)
    title='# ACKS II Revised Rulebook — полный перевод для вычитки\n\n<small>ACKS II REVISED RULEBOOK — RUSSIAN TRANSLATION FOR REVIEW</small>\n\n'
    title+='Введение, все 12 глав и приложения A–E, включая листы и указатели. Сноски со звёздочками сохраняют исправления, вопросы к оригиналу и рабочим терминам для решения переводчиков и редакторов.\n\n'
    title+='Ссылки «страница N» ведут к физическим страницам английского PDF. Числа страниц внутри правил сохранены по печатному оригиналу. Обложки и выходные сведения PDF 1–4, памятный список спонсоров PDF 539–544 оставлены в полных рабочих главах. Примечания к исключённому списку сохранены перед указателями.\n\n'
    title+='Результаты проверки и реестр всех 112 комментариев прежних переводчиков: [отчёт о полноте RR](<../База перевода/RR_проверка_полноты.md>).\n\n'
    nav=[('Оглавление',5),('Введение',8)]+[(('Глава '+str(int(ch['id']))+'. ' if ch['id'].isdigit() else 'Приложение '+ch['id']+'. ')+ch['title_ru'],ch['first_pdf_page']) for ch in progress[1:]]
    title+='\n'.join(f'- [{label}](#pdf-page-{n:04d})' for label,n in nav)+'\n'
    source_title=title.replace('Введение, все 12 глав и приложения A–E, включая листы и указатели. Сноски со звёздочками сохраняют исправления, вопросы к оригиналу и рабочим терминам для решения переводчиков и редакторов.','Введение, все 12 глав и приложения A–E, включая листы и указатели. Сноски со звёздочками сохраняют исправления, вопросы к оригиналу и рабочим терминам. Они требуют внимания переводчиков; вычитка Codex не означает утверждения человеком.')
    review_source=assemble(source_title,selected,human_bodies)
    assert Counter(notes(review_source,False))==Counter(raw_notes)
    title=title.replace('полный перевод для вычитки','версия для переводчиков',1)
    human=clean(assemble(title,selected,human_bodies))+'\n'
    assert Counter(notes(human))==Counter(all_notes)
    assert tables(human)==tables(canonical) and len(tables(human))==370
    assert not re.search(r'<!-- (?:unit:|table:)|rr\.p\d{4}|data-unit=|data-part=|## PDF-страница',human)
    validation={'date':'2026-10-18','source_units':30624,'source_pdf_pages':[1,550],'source_chapter_manifest':manifest,'tables':370,'notes':len(all_notes),'reader_note_projections':{'count':len(NOTE_PROJECTIONS),'mapping':'tools/rr_reader_notes.json','all_source_notes_matched_once':True,'original_technical_notes_retained_in_full_chapters':True},'outputs':{}}
    for path,md,expected_pages,role in ((CANONICAL,canonical,list(range(5,551)),'technical_full'),(REVIEW_SOURCE,review_source,selected,'technical_review'),(HUMAN,human,selected,'translator_review')):
        rendered=render(md);dom=Links();dom.feed(rendered)
        assert len(dom.ids)==len(set(dom.ids))==len(expected_pages)
        assert dom.ids==[f'pdf-page-{n:04}' for n in expected_pages]
        assert all(target in dom.ids for target in dom.links)
        assert dom.tables==370
        for asset in dom.assets:assert (OUT/unquote(asset)).is_file(),asset
        assert [int(n) for n in re.findall(r'^# Глава (\d+)\.',md,re.M)]==list(range(1,13))
        assert re.findall(r'^# Приложение ([A-E])\.',md,re.M)==list('ABCDE')
        path.write_text(md,'utf-8')
        validation['outputs'][path.name]={'path':str(path.relative_to(ROOT)),'role':role,'bytes':path.stat().st_size,'sha256':sha(path),'pdf_pages':expected_pages,'page_markers':len(expected_pages),'internal_links':len(dom.links),'assets':sorted(set(dom.assets))}
        if path==HUMAN:
            css='body{font:17px/1.55 Georgia,serif;max-width:1080px;margin:32px auto;padding:0 24px;color:#202020}h1,h2,h3{line-height:1.2;margin-bottom:.25em}small{font-size:.75em;color:#666}table{border-collapse:collapse;width:100%;font-size:14px;table-layout:auto}td,th{border:1px solid #bbb;padding:5px;overflow-wrap:anywhere}th{background:#f3f3f3}blockquote{border-left:3px solid #bbb;margin-left:0;padding-left:12px;color:#555;font-size:15px}hr{border:0;border-top:1px solid #ccc;margin:28px 0 4px}p[align=right]{margin:4px 0 18px;font-size:13px}img{max-width:100%;height:auto}'
            (WORK/'reader_preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><base href="../../ACKSII/Перевод%20Markdown/"><title>RR — полный перевод для вычитки</title><style>'+css+'</style><body>'+rendered+'</body></html>','utf-8')
    assert all(sha(ROOT/name)==digest for name,digest in manifest.items())
    validation['checks']={'all_notes_preserved':True,'all_table_text_preserved':True,'all_rule_prose_preserved_in_order':True,'all_reader_links_resolve':True,'all_assets_exist':True,'source_chapters_unchanged_by_build':True}
    validation['human_omissions']=[{'pdf_pages':[1,4],'reason':'обложки, реклама, цена, выходные данные'},{'pdf_pages':[539,544],'reason':'памятный список спонсоров; примечания перенесены перед указателями'}]
    (BASE/'RR_reading_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n','utf-8')
    # Existing report names remain current for consumers of the canonical reader.
    (BASE/'reading_validation.json').write_text(json.dumps({'date':'2026-10-18','target':str(CANONICAL.relative_to(ROOT)),'pdf_pages':[5,550],'compact_page_markers':546,'all_editorial_notes_preserved':len(all_notes),'tables_preserved_verbatim_after_metadata_removal':370,'sha256':sha(CANONICAL),'checks':validation['checks'],'details':'RR_reading_validation.json','builder':'tools/build_rr_reader.py'},ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'outputs':[str(p.relative_to(ROOT)) for p in (CANONICAL,REVIEW_SOURCE,HUMAN)],'tables':370,'notes':len(all_notes),'human_page_markers':len(selected)},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
