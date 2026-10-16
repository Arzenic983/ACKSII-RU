"""Build chapter 5 or an explicitly incomplete draft; never write to SQLite."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import os
import re
import shutil
import subprocess
from auto_units import HERE, ROOT
from review_tools import get_text, strip_english

BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
NODE=os.environ.get('ACKS_NODE') or shutil.which('node') or 'node'
STAMP='2026-10-16'

def is_header(u):
    en=re.sub(r'<br\s*/?>',' ',u['source_markup'])
    return bool(re.search('[A-Za-z]',en)) and (u['row_index']==0 or (en.isupper() and en!='N/A' and not re.fullmatch(r'[IVX /–-]+',en)))

def subtitle(u):return '<small>'+u['source_markup']+'</small>'

def build(reviewed=False,draft=False):
    if reviewed:
        gate=json.loads((HERE/'semantic_review.json').read_text('utf-8'))
        assert gate['complete_semantic_review'], 'Finish and record the semantic review before assigning reviewed.'
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    tables={t['id']:t for t in json.loads((HERE/'source_tables.json').read_text('utf-8'))}
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    text=get_text();expected={u['id'] for u in units}
    assert not set(text)-expected
    missing=expected-set(text)
    assert draft or not missing,sorted(missing)
    assert not(reviewed and missing)
    assert set(notes)<=expected
    pure={id:strip_english(value) for id,value in text.items()}
    for u in units:
        if u['id'] in missing:
            text[u['id']]='> **Перевод этого фрагмента ещё не подготовлен.**'
        elif u['table_id'] and is_header(u):
            text[u['id']]=pure[u['id']]+'<br>'+subtitle(u)
    rendered=subprocess.run([NODE,str(ROOT/'.work/ch03-md/render_inline.mjs')],input=json.dumps(text,ensure_ascii=False),encoding='utf-8',text=True,capture_output=True,check=True)
    inline=json.loads(rendered.stdout)
    def render_table(tid):
        table=tables[tid];cells=[u for u in units if u['table_id']==tid]
        rows=defaultdict(list)
        for u in cells:rows[u['row_index']].append(u)
        merged=any((u['rowspan'] or 1)>1 or (u['colspan'] or 1)>1 for u in cells)
        result=[f'<!-- table: {tid}; rows: {table["row_count"]}; columns: {table["column_count"]} -->'];foot=[]
        def mark(u):
            marks=''
            for note in notes.get(u['id'],[]):
                n=len(foot)+1;marks+=f'<sup>*{n}</sup>'
                foot.append(f'> \\*{n} `{u["id"]}` — {note}')
            return marks
        if merged:
            result.append(f'<table id="{tid}">')
            for rid in range(table['row_count']):
                result.append('<tr>');at={u['column_index']:u for u in rows[rid]};covered=set()
                for other in cells:
                    if other['row_index']<rid<other['row_index']+(other['rowspan'] or 1):
                        covered.update(range(other['column_index'],other['column_index']+(other['colspan'] or 1)))
                for col in range(table['column_count']):
                    if col in covered:continue
                    u=at.get(col);tag='th' if rid==0 else 'td'
                    if u is None:result.append(f'<{tag}></{tag}>');continue
                    attrs=f' id="{u["id"]}"'
                    for key in ('rowspan','colspan'):
                        if (u[key] or 1)>1:attrs+=f' {key}="{u[key]}"'
                    result.append(f'<{tag}{attrs}><!-- unit: {u["id"]} -->{inline[u["id"]]}{mark(u)}</{tag}>')
                    covered.update(range(col+1,col+(u['colspan'] or 1)))
                result.append('</tr>')
            result.append('</table>')
        else:
            for rid in range(table['row_count']):
                parts=[];at={u['column_index']:u for u in rows[rid]}
                for col in range(table['column_count']):
                    u=at.get(col)
                    if u is None:parts.append('');continue
                    value=text[u['id']].replace('|',r'\|').replace('\n','<br>')
                    parts.append(f'<!-- unit: {u["id"]} --><a id="{u["id"]}"></a>{value}{mark(u)}')
                result.append('| '+' | '.join(parts)+' |')
                if rid==0:result.append('| '+' | '.join(['---']*table['column_count'])+' |')
        for note in foot:result.extend(['',note])
        return '\n'.join(result)
    parts=['# Глава 5. Заклинания','','<small>CHAPTER 5: SPELLS</small>','',
        f'Перевод Revised Rulebook. Редакция: {STAMP}. Охват: физические PDF-страницы 180–263. Номера ссылок внутри правил сохранены по печатному оригиналу. Английские подписи служат оформлению Markdown; в пакете для базы хранится русский текст без них. Вычитка Codex не означает утверждения главным переводчиком.','']
    if draft:parts.extend([f'> **НЕЗАВЕРШЁННЫЙ ЧЕРНОВИК.** Подготовлено {len(pure)} из {len(units)} единиц; не переведено {len(missing)}. Общая смысловая и визуальная вычитка главы не закончена.',''])
    done=set()
    for page in range(180,264):
        selected=[u for u in units if u['pdf_page']==page]
        printed=None if page==180 else page-2
        parts.extend([f'<a id="pdf-page-{page:04d}"></a>','',f'## PDF-страница {page}'+(f' · печатная стр. {printed}' if printed is not None else ''),'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        if not selected:parts.extend(['<!-- Original page contains illustration only; no source translation units. -->',''])
        for u in selected:
            id=u['id']
            if u['table_id']:
                if u['table_id'] not in done:done.add(u['table_id']);parts.extend([render_table(u['table_id']),''])
                continue
            parts.extend([f'<!-- unit: {id} -->',f'<a id="{id}"></a>','']);value=text[id]
            if u['kind']=='heading':value='#'*min(6,max(3,u['heading_level'] or 3))+' '+value
            if notes.get(id):value+='<sup>*</sup>'
            if u['kind']=='heading':value+='\n\n'+subtitle(u)
            spell=re.fullmatch(r'\*\*\*([^*]+)\*\*\*(?:\s*\\?\*)?\s*',u['source_markup'])
            if spell:
                name=spell[1].rstrip('\\')
                value='#### '+pure[id].replace('***','').strip()+('<sup>*</sup>' if notes.get(id) else '')+'\n\n<small>'+name+'</small>'
            parts.extend([value,''])
            for note in notes.get(id,[]):parts.extend(['> \\* '+note,''])
    target=ROOT/'contributions/05/Черновик главы 5.md' if draft else OUT/'05 Заклинания.md'
    document='\n'.join(parts).rstrip()+'\n'
    if draft:
        document=document.replace('(../Source/','(../../ACKSII/Source/')
    target.write_text(document,'utf-8')
    package=ROOT/'contributions/05/translator.jsonl'
    rows=[json.loads(line) for line in package.read_text('utf-8').splitlines()]
    assert [r['id'] for r in rows]==[u['id'] for u in units]
    for row,u in zip(rows,units):
        assert row['english']==u['source_markup'] and row['source_sha256']==u['source_sha256'] and row['revision']==0
        row['russian']=pure.get(row['id'],'');row['status']='reviewed' if reviewed else 'draft'
        row['note']='\n\n'.join(strip_english(n) for n in notes.get(row['id'],[]))
    package.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf-8')
    with package.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');writer.writeheader();writer.writerows(rows)
    (HERE/'pure_translations.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'target':str(target),'translated_units':len(pure),'missing':len(missing),'tables':len(tables),'notes':sum(map(len,notes.values())),'status':rows[0]['status']},ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');build('--reviewed' in sys.argv,'--draft' in sys.argv)
