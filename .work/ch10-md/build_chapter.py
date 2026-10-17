"""Build chapter 10 and exchange packages; reads SQLite without modifying it."""
from pathlib import Path
import csv,hashlib,html,json,re,sqlite3,sys
from assemble_texts import main as assemble
from audit import audit
from labels import decorate,undecorate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/10'
MD=ROOT/'ACKSII/Перевод Markdown/10 Манёвры.md'
def inline(s):
    s=html.escape(s)
    s=re.sub(r'&lt;br\s*/?&gt;','<br>',s)
    s=re.sub(r'\*\*\*(.*?)\*\*\*',r'<strong><em>\1</em></strong>',s)
    s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<!\\)\*(.*?)(?<!\\)\*',r'<em>\1</em>',s)
    return s.replace('\\*','*')
def header(u):
    if u['table_id']=='rr.p0460.t02':return u['column_index']==0
    return u['row_index']==0 or (u['table_id'] in ('rr.p0450.t01','rr.p0457.t01') and u['row_index']==1) or (u['english'].isupper() and len(re.findall('[A-Z]',u['english']))>4)
def main():
    assemble()
    assert not audit(),'Resolve mechanics differences before building'
    source=[json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'))
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    id_pattern=r'rr\.p\d{4}\.(?:b\d{3}|t\d{2}(?:\.r\d{3}(?:\.c\d{2})?)?)(?:[–-](?:rr\.p\d{4}\.)?[bcr]\d{2,3})*'
    styled_notes={uid:re.sub(id_pattern,lambda m:'`'+m[0]+'`',decorate(undecorate(text))) for uid,text in notes.items()}
    review=HERE/'semantic_review.json'
    reviewed=review.exists() and json.loads(review.read_text('utf-8'))['complete_semantic_review_by_Codex']
    state=HERE/'integration.json';integrated=state.exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='10'")}
        tables={r['id']:dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='10'")}
    assert set(meta)==set(pure)=={u['id'] for u in source}
    assert set(notes).issubset(meta)
    package=[];styled={}
    for u in source:
        m=meta[u['id']]
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'):
            assert u[k]==m[k],(u['id'],k)
        expected_revision=json.loads(state.read_text('utf-8')).get('revisions',{}).get(u['id'],u['revision']+1) if integrated else u['revision']
        assert m['revision']==expected_revision
        assert hashlib.sha256(u['english'].encode()).hexdigest()==u['source_sha256']
        if integrated:assert m['russian']==pure[u['id']]
        text=pure[u['id']]
        styled[u['id']]=text if u['kind']=='heading' or (u['kind']=='table_cell' and header(m)) else decorate(text)
        assert undecorate(styled[u['id']])==text,u['id']
        row=dict(u)
        row.update(russian=text,status='reviewed' if reviewed else 'draft',origin='new_translation',note=undecorate(notes.get(u['id'],'')))
        package.append(row)
    md=['# Глава 10. Манёвры','','<small>CHAPTER 10: MANEUVERS</small>','',
        'Revised Rulebook. Физические PDF-страницы 448–461; 521/521 единица. '+('Проверено Codex' if reviewed else 'Черновик')+', без утверждения человеком. Английские подписи относятся к Markdown; в пакете и SQLite — русский текст без них.','']
    emitted=set();page=None;geometry={}
    for u in source:
        m=meta[u['id']]
        if page!=u['pdf_page']:
            page=u['pdf_page']
            printed=f' · печатная стр. {u["printed_page"]}' if u['printed_page'] is not None else ''
            md += [f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+printed,'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})','']
        if u['kind']=='table_cell':
            tid=m['table_id']
            if tid in emitted:continue
            emitted.add(tid)
            members=[v for v in source if meta[v['id']]['table_id']==tid]
            starts={(meta[v['id']]['row_index'],meta[v['id']]['column_index']):v for v in members}
            covered=set()
            for v in members:
                vm=meta[v['id']]
                for r in range(vm['row_index'],vm['row_index']+vm['rowspan']):
                    for c in range(vm['column_index'],vm['column_index']+vm['colspan']):
                        assert (r,c) not in covered,(tid,r,c)
                        covered.add((r,c))
            t=tables[tid]
            md.append(f'<table id="{tid}">')
            for r in range(t['row_count']):
                md.append('<tr>')
                for c in range(t['column_count']):
                    cell=starts.get((r,c))
                    if cell is None:
                        if (r,c) not in covered:md.append('<td></td>')
                        continue
                    cm=meta[cell['id']];tag='th' if header(cm) else 'td'
                    attrs=''.join(f' {k}="{cm[k]}"' for k in ('rowspan','colspan') if cm[k]>1)
                    text=inline(styled[cell['id']])
                    if header(cm):text+='<br><small>'+inline(cell['english'])+'</small>'
                    if cell['id'] in notes:text+='<sup>*</sup>'
                    md.append(f'<{tag}{attrs}><!-- unit: {cell["id"]} --><a id="{cell["id"]}"></a>{text}</{tag}>')
                md.append('</tr>')
            md += ['</table>','']
            for cell in members:
                if cell['id'] in notes:md += ['> \\* '+styled_notes[cell['id']],'']
            geometry[tid]={'rows':t['row_count'],'columns':t['column_count'],'source_cells':len(members),'empty_unrepresented_positions':t['row_count']*t['column_count']-len(covered)}
        else:
            md += [f'<!-- unit: {u["id"]} -->',f'<a id="{u["id"]}"></a>','']
            text=styled[u['id']]
            if u['kind']=='heading':
                md += ['#'*(m['heading_level'] or 3)+' '+text,'','<small>'+u['english']+'</small>','']
            else:
                # Page-split continuations such as "1. This means..." are prose,
                # not Markdown ordered lists. Escape the punctuation in display.
                text=re.sub(r'^(\d+)\.',r'\1\\.',text)
                md += [text+('<sup>*</sup>' if u['id'] in notes else ''),'']
            if u['id'] in notes:md += ['> \\* '+styled_notes[u['id']],'']
    rendered='\n'.join(md)
    assert re.findall(r'<!-- unit: (.*?) -->',rendered)==list(pure)
    assert emitted==set(tables)
    assert re.findall(r'<a id="pdf-page-(\d+)"',rendered)==[f'{p:04}' for p in range(448,462)]
    MD.write_text(rendered,'utf-8',newline='\n')
    (HERE/'styled.json').write_text(json.dumps(styled,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'styled_notes.json').write_text(json.dumps(styled_notes,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in package),'utf-8')
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(package[0]),delimiter=';');writer.writeheader();writer.writerows(package)
    result={'date':'2026-10-17','chapter':'10','scope':[448,461],'first_id':source[0]['id'],'last_id':source[-1]['id'],'units':len(source),'tables':geometry,'notes':len(notes),'headings':43,'status':'reviewed_by_Codex' if reviewed else 'draft','integrated':integrated}
    (HERE/'build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='tables'},ensure_ascii=False))
if __name__=='__main__':main()
