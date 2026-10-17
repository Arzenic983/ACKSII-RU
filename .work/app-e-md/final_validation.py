"""Read-only whole-book completion, order, export and reader-link verification."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
import csv,hashlib,json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
READER=OUT/'ACKS II — Начало, главы 1–12 и приложения A–E.md'
class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.index_links=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if 'id' in a:self.ids.append(a['id'])
        if t=='a' and '#pdf-page-' in a.get('href',''):self.index_links.append(a['href'])
def main():
    progress=json.loads((BASE/'progress.json').read_text('utf-8'))
    assert [p['id'] for p in progress]==['front_matter']+[f'{n:02}' for n in range(1,13)]+list('ABCDE')
    assert sum(p['source_units'] for p in progress)==sum(p['translated_units'] for p in progress)==30624
    assert all(p['pending_units']==0 and p['review_state']=='reviewed_by_Codex' for p in progress)
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        rows={r['id']:dict(r) for r in db.execute('SELECT * FROM bilingual')}
        assert len(rows)==30624 and all(r['russian'] and r['russian'].strip() for r in rows.values())
    exported=[json.loads(s) for s in (BASE/'units.jsonl').read_text('utf-8').splitlines()]
    assert len(exported)==30624 and {u['id'] for u in exported}==set(rows)
    for u in exported:
        for k in ('english','russian','source_sha256','revision','status'):assert u[k]==rows[u['id']][k],(u['id'],k)
    manifest={}
    for p in progress:
        path=OUT/('00 Начало.md' if p['id']=='front_matter' else p['id']+' '+p['title_ru']+'.md');assert path.is_file(),str(path)
        text=path.read_text('utf-8')
        present=set(re.findall(r'rr\.p\d{4}\.(?:b\d{3}|t\d{2}\.r\d{3}\.c\d{2})',text))
        expected={uid for uid,u in rows.items() if u['chapter_id']==p['id']}
        assert expected<=present,(p['id'],sorted(expected-present)[:5])
        manifest[str(path.relative_to(ROOT))]={'source_units_present':len(expected),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    md=READER.read_text('utf-8')
    assert [int(s) for s in re.findall(r'^# Глава (\d+)\.',md,re.M)]==list(range(1,13))
    assert re.findall(r'^# Приложение ([A-E])\.',md,re.M)==list('ABCDE')
    assert [int(s) for s in re.findall(r'<p align="right" id="pdf-page-(\d+)"',md)]==list(range(5,551))
    old=md.split('<p align="right" id="pdf-page-0538">',1)[0]
    old=re.sub(r'\n---\s*$','',old).rstrip()+'\n'
    old=old.replace('Начало, главы 1–12 и приложения A–E','Начало, главы 1–12 и приложения A–D',1).replace('FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–E','FRONT MATTER, CHAPTERS 1–12 AND APPENDICES A–D',1)
    assert old==(OUT/'ACKS II — Начало, главы 1–12 и приложения A–D.md').read_text('utf-8')
    report=json.loads((BASE/'reading_validation.json').read_text('utf-8'))
    assert report['sha256']==hashlib.sha256(READER.read_bytes()).hexdigest()
    assert report['tables_preserved_verbatim_after_metadata_removal']==370 and report['all_editorial_notes_preserved']==741
    # The renderer output is saved by the reader builder and independently parsed.
    rendered=(ROOT/'.work/reading-md/preview.html').read_text('utf-8');parser=Links();parser.feed(rendered)
    assert len(parser.ids)==len(set(parser.ids))==546
    assert len(parser.index_links)==975
    for href in parser.index_links:
        name,anchor=unquote(href).split('#',1)
        assert name==READER.name and anchor in parser.ids,href
    with (BASE/'E_review.csv').open(encoding='utf-8-sig',newline='') as f:fresh=list(csv.DictReader(f,delimiter=';'))
    assert len(fresh)==83 and all(u['status']=='reviewed' and u['revision']=='1' for u in fresh)
    result={'date':'2026-10-18','book':'ACKS II Revised Rulebook','source_pdf_pages':[1,550],'translated_units':30624,'source_units':30624,'pending_units':0,'chapters':12,'appendices':5,'complete_documents':18,'reader':str(READER.relative_to(ROOT)),'reader_pdf_pages':[5,550],'reader_page_markers':546,'tables':370,'editorial_notes':741,'index_entries':862,'index_links':975,'checks':{'all_database_units_translated':True,'all_18_sections_reviewed_by_Codex':True,'full_export_matches_database':True,'all_source_ids_present_in_full_chapter_documents':True,'all_chapters_and_appendices_in_book_order':True,'all_index_targets_exist_in_reader':True,'reader_previous_pages_5_537_unchanged':True,'source_chapter_manifest_recorded':True},'source_chapter_manifest':manifest,'reader_sha256':report['sha256'],'limits':'Читательская копия по прежней схеме исключает обложки и издательские PDF 1–4; они сохранены в полном начале. Это проверка полноты и сборки, не новая смысловая вычитка прежних глав и не утверждение человеком.'}
    (BASE/'full_book_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_chapter_manifest'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
