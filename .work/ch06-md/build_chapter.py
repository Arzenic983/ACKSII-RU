"""Build chapter 6 and the review package, preserving all IDs and table geometry."""
from common import HERE,ROOT,read,write
from collections import defaultdict
import json,re,csv,subprocess,sys,os,shutil
from pathlib import Path
BUNDLED_NODE=Path(r'C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
NODE=os.environ.get('ACKS_NODE') or (str(BUNDLED_NODE) if BUNDLED_NODE.exists() else shutil.which('node') or 'node')
def strip(s):return re.sub(r' ?\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\]','',s)
def main():
    units=read('source_units.json');tables={t['id']:t for t in read('source_tables.json')}
    text=read('bilingual_translations.json');pure=read('pure_translations.json');notes=read('bilingual_notes.json')
    assert set(text)==set(pure)=={u['id'] for u in units}
    assert read('reviewed_pages.json')==list(range(264,316))
    for u in units:
        en=u['source_markup']
        if u['table_id'] and (u['row_index']==0 or (en.isupper() and en!='N/A' and re.search('[A-Za-z]',re.sub('<[^>]+>','',en)))):
            if re.search('[A-Za-z]',en):text[u['id']]=pure[u['id']]+'<br><small>'+en+'</small>'
    inline=json.loads(subprocess.run([NODE,str(ROOT/'.work/ch03-md/render_inline.mjs')],input=json.dumps(text,ensure_ascii=False),encoding='utf-8',text=True,capture_output=True,check=True).stdout)
    def render(tid):
        t=tables[tid];cells=[u for u in units if u['table_id']==tid];rows=defaultdict(list)
        for u in cells:rows[u['row_index']].append(u)
        result=[f'<!-- table: {tid}; rows: {t["row_count"]}; columns: {t["column_count"]} -->'];foot=[]
        def mark(u):
            marks=''
            for note in notes.get(u['id'],[]):
                n=len(foot)+1;marks+=f'<sup>*{n}</sup>';foot.append(f'> \\*{n} `{u["id"]}` — {note}')
            return marks
        if any((u['rowspan'] or 1)>1 or (u['colspan'] or 1)>1 for u in cells):
            result.append(f'<table id="{tid}">')
            for r in range(t['row_count']):
                result.append('<tr>');at={u['column_index']:u for u in rows[r]};covered=set()
                for u in cells:
                    if u['row_index']<r<u['row_index']+(u['rowspan'] or 1):covered.update(range(u['column_index'],u['column_index']+(u['colspan'] or 1)))
                for c in range(t['column_count']):
                    if c in covered:continue
                    u=at.get(c);tag='th' if r==0 else 'td'
                    if u is None:result.append(f'<{tag}></{tag}>');continue
                    attrs=f' id="{u["id"]}"'
                    for k in ('rowspan','colspan'):
                        if (u[k] or 1)>1:attrs+=f' {k}="{u[k]}"'
                    result.append(f'<{tag}{attrs}><!-- unit: {u["id"]} -->{inline[u["id"]]}{mark(u)}</{tag}>')
                    covered.update(range(c+1,c+(u['colspan'] or 1)))
                result.append('</tr>')
            result.append('</table>')
        else:
            for r in range(t['row_count']):
                at={u['column_index']:u for u in rows[r]};parts=[]
                for c in range(t['column_count']):
                    u=at.get(c)
                    if not u:parts.append('');continue
                    value=text[u['id']].replace('|',r'\|').replace('\n','<br>')
                    parts.append(f'<!-- unit: {u["id"]} --><a id="{u["id"]}"></a>{value}{mark(u)}')
                result.append('| '+' | '.join(parts)+' |')
                if r==0:result.append('| '+' | '.join(['---']*t['column_count'])+' |')
        for note in foot:result.extend(['',note])
        return '\n'.join(result)
    parts=['# Глава 6. Приключения','','<small>CHAPTER 6: ADVENTURES</small>','',
      'Перевод Revised Rulebook. Редакция: 2026-10-16. Охват: физические PDF-страницы 264–315. Внутренние ссылки сохраняют печатные страницы оригинала. Английские подписи относятся к оформлению Markdown; пакет для базы содержит русский текст без них. Вычитка Codex не означает утверждения человеком.','']
    done=set()
    for page in range(264,316):
        parts.extend([f'<a id="pdf-page-{page:04d}"></a>','',f'## PDF-страница {page}'+(f' · печатная стр. {page-2}' if page!=264 else ''),'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        for u in (u for u in units if u['pdf_page']==page):
            id=u['id']
            if u['table_id']:
                if u['table_id'] not in done:done.add(u['table_id']);parts.extend([render(u['table_id']),''])
                continue
            parts.extend([f'<!-- unit: {id} -->',f'<a id="{id}"></a>',''])
            value=text[id]
            if u['kind']=='heading':value='#'*min(6,max(3,u['heading_level'] or 3))+' '+value
            if notes.get(id):value+='<sup>*</sup>'
            if u['kind']=='heading':value+='\n\n<small>'+u['source_markup']+'</small>'
            parts.extend([value,''])
            for note in notes.get(id,[]):parts.extend(['> \\* '+note,''])
    (ROOT/'ACKSII/Перевод Markdown/06 Приключения.md').write_text('\n'.join(parts).rstrip()+'\n','utf-8')
    path=ROOT/'contributions/06/translator.jsonl';rows=[json.loads(s) for s in path.read_text('utf-8').splitlines()]
    for row,u in zip(rows,units):
        assert row['id']==u['id'] and row['english']==u['source_markup'] and row['revision']==0
        row.update(russian=pure[u['id']],status='reviewed',origin='Codex: сверка черновиков участников и новый перевод по Revised Rulebook',note='\n\n'.join(strip(s) for s in notes.get(u['id'],[])))
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf-8')
    with path.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
    print('Built chapter 6:',len(rows),'units',len(tables),'tables',sum(map(len,notes.values())),'notes')
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
