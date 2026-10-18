"""Build appendix A and exchange packages; never imports into SQLite."""
from pathlib import Path
import csv,hashlib,html,json,re,sqlite3
from assemble_texts import main as assemble
from audit import audit
from labels import decorate,undecorate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/A'
MD=ROOT/'ACKSII/Перевод Markdown/A Сеттинг.md'
def inline(s):
    s=html.escape(s)
    s=re.sub(r'&lt;br\s*/?&gt;','<br>',s)
    s=re.sub(r'\*\*\*(.*?)\*\*\*',r'<strong><em>\1</em></strong>',s)
    s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
    return re.sub(r'\*(.*?)\*',r'<em>\1</em>',s)
def main():
    assemble();assert not audit()
    source=[json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    pure=json.loads((HERE/'pure.json').read_text('utf-8'))
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    nodes=json.loads((HERE/'language_nodes.json').read_text('utf-8'))
    reviewed=(HERE/'semantic_review.json').exists()
    if reviewed:assert hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest()==json.loads((HERE/'semantic_review.json').read_text('utf-8'))['russian_units_sha256']
    integrated=(HERE/'integration.json').exists()
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='A'")}
        tables={r['id']:dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='A'")}
        pages={r['pdf_page']:r['printed_page'] for r in db.execute('SELECT pdf_page,printed_page FROM pages WHERE pdf_page BETWEEN 488 AND 507')}
    assert set(meta)==set(pure)=={u['id'] for u in source}
    assert set(notes).issubset(meta)
    styled={};package=[]
    for u in source:
        uid=u['id'];m=meta[uid];text=pure[uid]
        for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'):assert u[k]==m[k],(uid,k)
        assert hashlib.sha256(u['english'].encode()).hexdigest()==u['source_sha256']
        assert m['revision']==u['revision']+(1 if integrated else 0)
        if integrated:assert m['russian']==text
        value=text if u['kind']=='heading' or (u['kind']=='table_cell' and m['row_index']==0) else decorate(text)
        if re.fullmatch(r'rr\.p0491\.b00[4-8]',uid):
            ru_parts=text.rstrip('.').split('; ');en_parts=u['english'].rstrip('.').split('; ')
            assert len(ru_parts)==len(en_parts)
            value='; '.join(r+' ['+e+']' for r,e in zip(ru_parts,en_parts))+'.'
        if uid=='rr.p0491.b009':value=text+' [N.]'
        if uid=='rr.p0500.b006':value=value.replace('[Drakönir]','[Drakonir]')
        if uid=='rr.p0504.b010':value=value.replace('Дракон [dragon]','Дракон [Drakon]')
        if uid=='rr.p0489.b015':value=value.replace('[Komean Sea]','[Comean Sea]')
        if u['kind']=='table_cell' and m['table_id']=='rr.p0496.t01' and m['column_index']==1 and m['row_index']>0:
            value=text+' ['+u['english'].replace('<br>',' ')+']'
        # Individual names retain their exact English spellings, including diacritics.
        if re.match(r'^\*\*(?:Male Names|Female Names|Surnames):',u['english']):
            prefix,items=text.split('** ',1);en_items=u['english'].split('** ',1)[1].split(', ');ru_items=items.split(', ')
            assert len(en_items)==len(ru_items)
            value=decorate(prefix+'**')+' '+', '.join(r+' ['+e+']' for r,e in zip(ru_items,en_items))
        assert undecorate(value)==text,(uid,value,text)
        styled[uid]=value
        row=dict(u);row.update(russian=text,status='reviewed' if reviewed else 'draft',origin='new_translation',note=undecorate(notes.get(uid,'')));package.append(row)
    md=['# Приложение A. Сеттинг','','<small>APPENDIX A: CAMPAIGN SETTING</small>','',
        'Revised Rulebook. Физические PDF-страницы 488–507; 344/344 единицы. '+('Проверено Codex' if reviewed else 'Черновик')+', без утверждения человеком. Английские подписи — оформление Markdown; в пакете и SQLite хранится русский текст без них.','']
    emitted=set();geometry={}
    def note(uid):
        if uid in notes:md.extend(['> \\* '+re.sub(r'rr\.p\d{4}\.[bt][\w.]+',lambda m:'`'+m[0]+'`',decorate(notes[uid])),''])
    for page in range(488,508):
        units=[u for u in source if u['pdf_page']==page]
        printed=pages[page]
        print_label=f' · печатная стр. {printed}' if printed is not None else ''
        md.extend([f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+print_label,'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        if page==491:md.extend(['![Карта Ауранской империи и соседних королевств из оригинала; русская легенда ниже.](assets/appendix-a-map.png)',''])
        if page==506:md.extend(['<!-- На этой странице нет текстовых единиц подготовленного исходника. -->','','![Иллюстрация осады из оригинала.](assets/appendix-a-siege.png)',''])
        for u in units:
            uid=u['id'];m=meta[uid]
            if u['kind']=='table_cell':
                tid=m['table_id']
                if tid in emitted:continue
                emitted.add(tid);t=tables[tid]
                members=[v for v in source if meta[v['id']]['table_id']==tid]
                starts={(meta[v['id']]['row_index'],meta[v['id']]['column_index']):v for v in members}
                assert len(starts)==t['row_count']*t['column_count']
                md.append(f'<table id="{tid}">')
                for r in range(t['row_count']):
                    md.append('<tr>')
                    for c in range(t['column_count']):
                        v=starts[(r,c)];vid=v['id'];tag='th' if r==0 else 'td'
                        body=inline(styled[vid])
                        if r==0:body+='<br><small>'+inline(v['english'])+'</small>'
                        if vid in notes:body+='<sup>*</sup>'
                        md.append(f'<{tag}><!-- unit: {vid} --><a id="{vid}"></a>{body}</{tag}>')
                    md.append('</tr>')
                md.extend(['</table>',''])
                for v in members:note(v['id'])
                geometry[tid]={'rows':t['row_count'],'columns':t['column_count'],'source_cells':len(members)}
                continue
            md.extend([f'<!-- unit: {uid} -->',f'<a id="{uid}"></a>',''])
            body=styled[uid]
            if u['kind']=='heading':md.extend(['#'*(m['heading_level'] or 3)+' '+body,'','<small>'+u['english']+'</small>',''])
            elif uid in ('rr.p0507.b003','rr.p0507.b005'):
                # Explicit depth on each node preserves both source trees. CSS
                # borders express branches without injecting text into the unit.
                md.append('<div class="language-tree">')
                for n in nodes:
                    ru=n[2] if uid.endswith('003') else '['+n[3]+']'
                    en=n[1].replace('*','') if uid.endswith('003') else n[4][1:-1]
                    md.append(f'<div data-depth="{n[0]}" style="margin-left:{int(n[0])*1.5}em;border-left:1px solid #aaa;padding:0.2em 0.6em">'+inline(ru+' ['+en+']')+'</div>')
                md.extend(['</div>'+('<sup>*</sup>' if uid in notes else ''),''])
            elif re.fullmatch(r'rr\.p0505\.b00[7-9]|rr\.p0505\.b010',uid):
                md.extend(['<br>\n'.join(re.findall(r'\*[^*]+\*',body))+('<sup>*</sup>' if uid in notes else ''),''])
            else:md.extend([body+('<sup>*</sup>' if uid in notes else ''),''])
            note(uid)
    rendered='\n'.join(md)
    assert re.findall(r'<!-- unit: (.*?) -->',rendered)==list(pure)
    assert re.findall(r'<a id="pdf-page-(\d+)"',rendered)==[f'{p:04}' for p in range(488,508)]
    assert emitted==set(tables)
    MD.write_text(rendered,'utf-8',newline='\n')
    (HERE/'styled.json').write_text(json.dumps(styled,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in package),'utf-8')
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(package[0]),delimiter=';');writer.writeheader();writer.writerows(package)
    result={'date':'2026-10-17','chapter':'A','scope':[488,507],'first_id':source[0]['id'],'last_id':source[-1]['id'],'units':len(source),'tables':geometry,'notes':len(notes),'status':'reviewed_by_Codex' if reviewed else 'draft','integrated':integrated}
    (HERE/'build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
