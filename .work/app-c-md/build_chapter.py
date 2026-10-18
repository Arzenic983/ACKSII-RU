"""Build appendix C and revision-0 exchange packages; never imports SQLite."""
from pathlib import Path
import csv,hashlib,html,json,re,sqlite3
from assemble_texts import main as assemble
from audit import audit
from labels import decorate,undecorate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/C'
MD=ROOT/'ACKSII/Перевод Markdown/C Раны и страдания.md'
def inline(s):
    s=html.escape(s)
    s=re.sub(r'&lt;br\s*/?&gt;','<br>',s)
    s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<!\\)\*(.*?)(?<!\\)\*',r'<em>\1</em>',s)
    return s.replace('\\*','*')
def main():
    assemble();assert not audit()
    source=[json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'))
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    review=HERE/'semantic_review.json';reviewed=review.exists()
    if reviewed:
        data=json.loads(review.read_text('utf-8'))
        assert data['complete_semantic_review_by_Codex'] and not data['human_approval']
        assert data['russian_units_sha256']==hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest()
    integrated=(HERE/'integration.json').exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='C'")}
        tables={r['id']:dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='C'")}
        pages={r['pdf_page']:r['printed_page'] for r in db.execute('SELECT pdf_page,printed_page FROM pages WHERE pdf_page BETWEEN 518 AND 531')}
    assert set(meta)==set(pure)=={u['id'] for u in source} and set(notes).issubset(meta)
    styled={};package=[]
    styled_notes={uid:re.sub(r'rr\.p\d{4}\.[\w.]+',lambda m:'`'+m[0]+'`',decorate(note)) for uid,note in notes.items()}
    for u in source:
        uid=u['id'];m=meta[uid];text=pure[uid]
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'):assert u[k]==m[k],(uid,k)
        assert hashlib.sha256(u['english'].encode()).hexdigest()==u['source_sha256']
        assert m['revision']==u['revision']+(1 if integrated else 0),uid
        if integrated:assert m['russian']==text,uid
        styled[uid]=text if u['kind']=='heading' or (u['kind']=='table_cell' and m['row_index']==0) else decorate(text,u['english'])
        assert undecorate(styled[uid])==text,uid
        row=dict(u);row.update(russian=text,status='reviewed' if reviewed else 'draft',origin='new_translation',note=undecorate(notes.get(uid,'')));package.append(row)
    md=['# Приложение C. Раны и страдания','','<small>APPENDIX C: WOUNDS AND WOE</small>','',
        'Revised Rulebook. Физические PDF-страницы 518–531; 827/827 единиц. '+('Проверено Codex' if reviewed else 'Черновик')+', без утверждения человеком. Английские подписи относятся к Markdown; в пакете и SQLite хранится русский текст без них.','']
    emitted=set();geometry={}
    for page in range(518,532):
        printed=f' · печатная стр. {pages[page]}' if pages[page] is not None else ''
        md += [f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+printed,'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})','']
        for u in (u for u in source if u['pdf_page']==page):
            uid=u['id'];m=meta[uid]
            if u['kind']=='table_cell':
                tid=m['table_id']
                if tid in emitted:continue
                emitted.add(tid);t=tables[tid]
                members=[v for v in source if meta[v['id']]['table_id']==tid]
                starts={(meta[v['id']]['row_index'],meta[v['id']]['column_index']):v for v in members}
                assert len(starts)==72 and t['row_count']==9 and t['column_count']==8
                md.append(f'<table id="{tid}" style="overflow-wrap:anywhere">')
                for r in range(9):
                    md.append('<tr>')
                    for c in range(8):
                        cell=starts[r,c];cm=meta[cell['id']]
                        assert cm['rowspan']==cm['colspan']==1
                        tag='th' if r==0 else 'td';text=inline(styled[cell['id']])
                        if r==0 and re.search('[A-Za-z]',cell['english']):text+='<br><small>'+inline(cell['english'])+'</small>'
                        if cell['id'] in notes:text+='<sup>*</sup>'
                        attrs=f' style="width:{110 if c==0 else 170}px"' if r==0 and c<2 else ''
                        md.append(f'<{tag}{attrs}><!-- unit: {cell["id"]} --><a id="{cell["id"]}"></a>{text}</{tag}>')
                    md.append('</tr>')
                md += ['</table>','']
                for cell in members:
                    if cell['id'] in notes:md += ['> \\* '+styled_notes[cell['id']],'']
                geometry[tid]={'rows':9,'columns':8,'source_cells':72,'empty_unrepresented_positions':0}
            else:
                md += [f'<!-- unit: {uid} -->',f'<a id="{uid}"></a>','']
                text=styled[uid]+('<sup>*</sup>' if uid in notes else '')
                if u['kind']=='heading':md += ['#'*(m['heading_level'] or 3)+' '+text,'','<small>'+u['english']+'</small>','']
                else:md += [text,'']
                if uid in notes:md += ['> \\* '+styled_notes[uid],'']
    rendered='\n'.join(md)
    assert re.findall(r'<!-- unit: (.*?) -->',rendered)==list(pure)
    assert emitted==set(tables)
    assert re.findall(r'<a id="pdf-page-(\d+)"',rendered)==[f'{p:04}' for p in range(518,532)]
    MD.write_text(rendered,'utf-8',newline='\n')
    for name,data in [('styled.json',styled),('styled_notes.json',styled_notes)]: (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in package),'utf-8')
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(package[0]),delimiter=';');w.writeheader();w.writerows(package)
    result={'date':'2026-10-17','chapter':'C','scope':[518,531],'first_id':source[0]['id'],'last_id':source[-1]['id'],'units':827,'headings':15,'tables':geometry,'notes':len(notes),'status':'reviewed_by_Codex' if reviewed else 'draft','integrated':integrated}
    (HERE/'build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='tables'},ensure_ascii=False))
if __name__=='__main__':main()
