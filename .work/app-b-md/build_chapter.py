"""Build appendix B and review packages without mutating the database."""
from pathlib import Path
import csv,hashlib,json,re,sqlite3
from assemble_texts import main as assemble
from audit import audit
from labels import decorate,undecorate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/B'
MD=ROOT/'ACKSII/Перевод Markdown/B Состояния.md'
def main():
    assemble();assert not audit(),'Unresolved mechanical differences'
    source=[json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'))
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    reviewed=(HERE/'semantic_review.json').exists()
    if reviewed:assert hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest()==json.loads((HERE/'semantic_review.json').read_text('utf-8'))['russian_units_sha256']
    integrated=(HERE/'integration.json').exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='B'")}
        assert db.execute("SELECT count(*) FROM source_tables WHERE chapter_id='B'").fetchone()[0]==0
    assert set(pure)==set(meta)=={u['id'] for u in source} and set(notes).issubset(meta)
    package=[];styled={};styled_notes={}
    md=['# Приложение B. Состояния','','<small>APPENDIX B: CONDITIONS</small>','',
        'Revised Rulebook. Физические PDF-страницы 508–517; 283/283 единицы. '+('Проверено Codex' if reviewed else 'Черновик')+', без утверждения человеком. Английские подписи — оформление Markdown; в пакете и SQLite хранится русский текст без них.','']
    page=None
    for u in source:
        uid=u['id'];m=meta[uid];text=pure[uid]
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'):assert u[k]==m[k],(uid,k)
        assert hashlib.sha256(u['english'].encode()).hexdigest()==u['source_sha256']
        assert m['revision']==u['revision']+(1 if integrated else 0)
        if integrated:assert m['russian']==text
        value=text if u['kind']=='heading' else decorate(text,u['english'])
        if uid=='rr.p0513.b031':value=value.replace('неуязвимые [immune]','неуязвимые [invulnerable]')
        if uid in ('rr.p0513.b033','rr.p0515.b002'):value=value.replace('обычному','обычному [mundane]',1)
        if uid=='rr.p0516.b032':value=value.replace('обычный урон','обычный урон [ordinary damage]')
        assert undecorate(value)==text,(uid,value,text)
        styled[uid]=value
        row=dict(u);row.update(russian=text,status='reviewed' if reviewed else 'draft',origin='new_translation',note=undecorate(notes.get(uid,'')));package.append(row)
        if page!=u['pdf_page']:
            page=u['pdf_page'];printed=f' · печатная стр. {u["printed_page"]}' if u['printed_page'] is not None else ''
            md.extend([f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+printed,'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        md.extend([f'<!-- unit: {uid} -->',f'<a id="{uid}"></a>',''])
        if u['kind']=='heading':md.extend(['#'*(m['heading_level'] or 3)+' '+value,'','<small>'+u['english']+'</small>',''])
        else:md.extend([value+('<sup>*</sup>' if uid in notes else ''),''])
        if uid in notes:
            if u['kind']=='heading':md[-4]+='<sup>*</sup>'
            note=re.sub(r'rr\.p\d{4}\.[bt][\w.]+',lambda m:'`'+m[0]+'`',decorate(notes[uid]))
            styled_notes[uid]=note;md.extend(['> \\* '+note,''])
    rendered='\n'.join(md)
    assert re.findall(r'<!-- unit: (.*?) -->',rendered)==list(pure)
    assert re.findall(r'<a id="pdf-page-(\d+)"',rendered)==[f'{p:04}' for p in range(508,518)]
    MD.write_text(rendered,'utf-8',newline='\n')
    for name,data in [('styled.json',styled),('styled_notes.json',styled_notes)]: (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in package),'utf-8')
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(package[0]),delimiter=';');writer.writeheader();writer.writerows(package)
    result={'date':'2026-10-17','chapter':'B','scope':[508,517],'first_id':source[0]['id'],'last_id':source[-1]['id'],'units':len(source),'headings':65,'tables':{},'notes':len(notes),'status':'reviewed_by_Codex' if reviewed else 'draft','integrated':integrated}
    (HERE/'build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
