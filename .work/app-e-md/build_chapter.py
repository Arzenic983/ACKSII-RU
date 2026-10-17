"""Build E and exchange packages; never import or overwrite another chapter."""
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote
import csv,hashlib,html,json,re,sqlite3
from assemble_texts import main as assemble
from audit import audit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/E'
MD=ROOT/'ACKSII/Перевод Markdown/E Предметный указатель.md'
READER='ACKS II — Начало, главы 1–12 и приложения A–E.md'
def inline(s):
    s=html.escape(s)
    s=re.sub(r'(?<!\\)\*\*\*(.+?)(?<!\\)\*\*\*',r'<strong><em>\1</em></strong>',s)
    s=re.sub(r'(?<!\\)\*\*(.+?)(?<!\\)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<!\\)\*(.+?)(?<!\\)\*',r'<em>\1</em>',s)
    return re.sub(r'\\([_*])',r'\1',s)
def main():
    assemble();assert not audit()
    source=[json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'));notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    review=HERE/'semantic_review.json';reviewed=review.exists();integrated=(HERE/'integration.json').exists()
    if reviewed:
        gate=json.loads(review.read_text('utf-8'))
        assert gate['complete_semantic_review_by_Codex'] and not gate['human_approval']
        assert gate['russian_units_sha256']==hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='E'")}
        pages={r['pdf_page']:r['printed_page'] for r in db.execute('SELECT pdf_page,printed_page FROM pages WHERE pdf_page BETWEEN 538 AND 550')}
        printed={r['printed_page']:r['pdf_page'] for r in db.execute('SELECT pdf_page,printed_page FROM pages WHERE printed_page IS NOT NULL')}
        assert db.execute("SELECT count(*) FROM source_tables WHERE chapter_id='E'").fetchone()[0]==0
    assert set(meta)==set(pure)=={u['id'] for u in source} and set(notes)<=set(meta)
    entries=json.loads((HERE/'styled_entries.json').read_text('utf-8'));byunit=defaultdict(list)
    for e in entries:byunit[e['unit']].append(e)
    package=[]
    for u in source:
        m=meta[u['id']]
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'):assert u[k]==m[k],(u['id'],k)
        assert hashlib.sha256(u['english'].encode()).hexdigest()==u['source_sha256']
        assert m['revision']==u['revision']+(1 if integrated else 0)
        if integrated:assert m['russian']==pure[u['id']]
        row=dict(u);row.update(russian=pure[u['id']],status='reviewed' if reviewed else 'draft',origin='new_translation',note=notes.get(u['id'],''));package.append(row)
    md=['# Приложение E. Предметный указатель','','<small>APPENDIX E: INDEX</small>','',f'Revised Rulebook. Физические PDF-страницы 538–550; 83/83 единиц. '+('Проверено Codex' if reviewed else 'Черновик')+', без утверждения человеком. Английские подписи относятся к Markdown; в SQLite и пакетах русский текст хранится без оформительских вставок.','']
    styled_notes={uid:re.sub(r'rr\.p\d{4}\.[\w.]+',lambda m:'`'+m[0]+'`',note).replace('«автархи»','«автархи [Autarchs]»').replace('«космархи»','«космархи [Cosmarchs]»').replace('«Подкрадывание»','«Подкрадывание [Sneaking]»').replace('«Крадущийся»','«Крадущийся [Sneaking]»') for uid,note in notes.items()}
    (HERE/'styled_notes.json').write_text(json.dumps(styled_notes,ensure_ascii=False,indent=2)+'\n','utf-8')
    display_order=[];links=0
    def anchor(uid):
        display_order.append(uid)
        return f'<!-- unit: {uid} --><a id="{uid}"></a>'
    def foot(uid):
        if uid in notes:md.extend(['> \\* '+styled_notes[uid],''])
    for page in range(538,551):
        suffix=f' · печатная стр. {pages[page]}' if pages[page] is not None else ''
        md.extend([f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+suffix,'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        units=[u for u in source if u['pdf_page']==page]
        if page==548:
            order=['rr.p0548.b001','rr.p0548.b004','rr.p0548.b002','rr.p0548.b003','rr.p0548.b006']
            units=[next(u for u in units if u['id']==uid) for uid in order]
        for u in units:
            uid=u['id'];mark='<sup>*</sup>' if uid in notes else ''
            if uid=='rr.p0548.b002':
                md.extend(['### '+anchor('rr.p0548.b005')+pure['rr.p0548.b005']+' '+anchor(uid)+pure[uid]+mark,'','<small>REVERSED SPELL INDEX</small>','']);foot(uid);continue
            md.extend([anchor(uid),''])
            if uid in byunit:
                md.append('<div class="index-block">')
                for e in byunit[uid]:
                    for letter in e['embedded_letters']:md.append('<p><strong>'+letter+'</strong></p>')
                    refs=[];pos=0
                    for m in re.finditer(r'\d+',e['pages']):
                        refs.append(html.escape(e['pages'][pos:m.start()]));n=int(m[0]);physical=printed[n];assert 5<=physical<=550
                        refs.append(f'<a href="{quote(READER)}#pdf-page-{physical:04}" title="Печатная стр. {n}; PDF {physical}">{n}</a>');links+=1;pos=m.end()
                    refs.append(html.escape(e['pages'][pos:]))
                    md.append('<p>'+inline(e['russian'])+' ['+html.escape(e['english'])+'] — '+''.join(refs)+'</p>')
                md.extend(['</div>','']);foot(uid)
            elif u['kind']=='heading':
                md.extend(['#'*(meta[uid]['heading_level'] or 3)+' '+pure[uid]+mark,'','<small>'+html.escape(u['english'])+'</small>','']);foot(uid)
            else:
                text=inline(pure[uid])
                if uid=='rr.p0539.b002':text=text.replace('</strong>','</strong> [Adventurer Conqueror King System Imperial Imprint]',1).replace('Ауранской империи','Ауранской империи [Auran Empire]')
                md.extend(['<div class="backer-list">'+text+mark+'</div>','']);foot(uid)
    assert len(display_order)==len(set(display_order))==83
    rendered='\n'.join(md);MD.write_text(rendered,'utf-8',newline='\n')
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in package),'utf-8',newline='\n')
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(package[0]),delimiter=';');w.writeheader();w.writerows(package)
    report={'date':'2026-10-18','chapter':'E','scope':[538,550],'first_id':source[0]['id'],'last_id':source[-1]['id'],'units':83,'headings':30,'rendered_source_heading_blocks':29,'tables':0,'index_entries':len(entries),'index_page_links':links,'notes':len(notes),'status':'reviewed_by_Codex' if reviewed else 'draft','integrated':integrated,'display_order':display_order}
    (HERE/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({k:v for k,v in report.items() if k!='display_order'},ensure_ascii=False))
if __name__=='__main__':main()
