"""Build chapter 3 and its revision-preserving exchange package, without DB writes."""
from collections import defaultdict
from pathlib import Path
import csv
import importlib.util
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
CORRECTED_HEADERS={
 'rr.p0118.t01.r001.c02':'RANK (# OF TIMES TAKEN)',
 'rr.p0118.t01.r001.c03':'GP EARNED / MONTH',
 'rr.p0119.t01.r001.c02':'RANK (# OF TIMES TAKEN)',
 'rr.p0119.t01.r001.c03':'GP EARNED / MONTH',
}
# PDF 104 marks levels above these maxima with a dark fill, absent from extraction.
MAX_LEVELS={6:10,7:13,8:11,9:10,13:12,21:12}

def subtitle(u):
    return '<small>'+CORRECTED_HEADERS.get(u['id'],u['source_markup'])+'</small>'

def build(reviewed=False):
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    tables={t['id']:t for t in json.loads((HERE/'source_tables.json').read_text('utf-8'))}
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    text=get_text()
    assert set(text)=={u['id'] for u in units}
    assert set(notes)<=set(text)
    pure={id:strip_english(value) for id,value in text.items()}
    for u in units:
        if u['table_id'] and u['row_index']==0 and re.search('[A-Za-z]',u['source_markup']):
            text[u['id']]=pure[u['id']]+'<br>'+subtitle(u)
    rendered=subprocess.run([NODE,str(HERE/'render_inline.mjs')],input=json.dumps(text,ensure_ascii=False),encoding='utf-8',text=True,capture_output=True,check=True)
    inline=json.loads(rendered.stdout)
    def render_table(tid):
        table=tables[tid]
        cells=[u for u in units if u['table_id']==tid]
        rows=defaultdict(list)
        for u in cells:rows[u['row_index']].append(u)
        merged=any((u['rowspan'] or 1)>1 or (u['colspan'] or 1)>1 for u in cells)
        html_table=merged or tid=='rr.p0104.t01'
        result=[f'<!-- table: {tid}; rows: {table["row_count"]}; columns: {table["column_count"]} -->']
        foot=[]
        def mark(u):
            marks=''
            for note in notes.get(u['id'],[]):
                n=len(foot)+1
                marks+=f'<sup>*{n}</sup>'
                foot.append(f'> \\*{n} `{u["id"]}` — {note}')
            return marks
        if html_table:
            result.append(f'<table id="{tid}">')
            for rid in range(table['row_count']):
                result.append('<tr>')
                at={u['column_index']:u for u in rows[rid]}
                covered=set()
                for other in cells:
                    if other['row_index']<rid<other['row_index']+(other['rowspan'] or 1):
                        covered.update(range(other['column_index'],other['column_index']+(other['colspan'] or 1)))
                for col in range(table['column_count']):
                    if col in covered:continue
                    tag='th' if rid==0 else 'td'
                    u=at.get(col)
                    if u is None:
                        unavailable=tid=='rr.p0104.t01' and rid in MAX_LEVELS and col>MAX_LEVELS[rid]
                        result.append('<td title="Уровень недоступен" style="background:#5b1333;color:#fff">-</td>' if unavailable else f'<{tag}></{tag}>')
                        continue
                    attrs=f' id="{u["id"]}"'
                    for key in ('rowspan','colspan'):
                        if (u[key] or 1)>1:attrs+=f' {key}="{u[key]}"'
                    result.append(f'<{tag}{attrs}><!-- unit: {u["id"]} -->{inline[u["id"]]}{mark(u)}</{tag}>')
                    covered.update(range(col+1,col+(u['colspan'] or 1)))
                result.append('</tr>')
            result.append('</table>')
        else:
            for rid in range(table['row_count']):
                parts=[]
                at={u['column_index']:u for u in rows[rid]}
                for col in range(table['column_count']):
                    u=at.get(col)
                    if u is None:
                        parts.append('')
                        continue
                    value=text[u['id']].replace('|',r'\|').replace('\n','<br>')
                    parts.append(f'<!-- unit: {u["id"]} --><a id="{u["id"]}"></a>{value}{mark(u)}')
                result.append('| '+' | '.join(parts)+' |')
                if rid==0:result.append('| '+' | '.join(['---']*table['column_count'])+' |')
        for note in foot:result.extend(['',note])
        return '\n'.join(result)
    parts=['# Глава 3. Навыки','', '<small>CHAPTER 3: PROFICIENCIES</small>','',f'Перевод Revised Rulebook. Редакция: {STAMP}. Охват: физические PDF-страницы 102–123. Номера ссылок внутри правил сохранены по печатному оригиналу. Английские подписи служат оформлению Markdown; в пакете для базы хранится русский текст без них. Вычитка Codex не означает утверждения главным переводчиком.','']
    done=set()
    for page in range(102,124):
        selected=[u for u in units if u['pdf_page']==page]
        printed=None if page==102 else page-2
        parts.extend([f'<a id="pdf-page-{page:04d}"></a>','',f'## PDF-страница {page}'+(f' · печатная стр. {printed}' if printed is not None else ''),'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})',''])
        for u in selected:
            id=u['id']
            if u['table_id']:
                if u['table_id'] not in done:
                    done.add(u['table_id'])
                    parts.extend([render_table(u['table_id']),''])
                continue
            parts.extend([f'<!-- unit: {id} -->',f'<a id="{id}"></a>',''])
            value=text[id]
            if u['kind']=='heading':
                value='#'*min(6,max(3,u['heading_level'] or 3))+' '+value
            if notes.get(id):value+='<sup>*</sup>'
            if u['kind']=='heading':value+='\n\n'+subtitle(u)
            parts.extend([value,''])
            for note in notes.get(id,[]):parts.extend(['> \\* '+note,''])
    chapter='\n'.join(parts).rstrip()+'\n'
    (OUT/'03 Навыки.md').write_text(chapter,'utf-8')
    # Preserve the exact exported source fields and original revision 0.
    package=ROOT/'contributions/03/translator.jsonl'
    rows=[json.loads(line) for line in package.read_text('utf-8').splitlines()]
    assert [r['id'] for r in rows]==[u['id'] for u in units]
    for row,u in zip(rows,units):
        assert row['english']==u['source_markup'] and row['source_sha256']==u['source_sha256'] and row['revision']==0
        row['russian']=pure[row['id']]
        row['status']='reviewed' if reviewed else 'draft'
        row['note']='\n\n'.join(strip_english(n) for n in notes.get(row['id'],[]))
    package.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf-8')
    with package.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';')
        writer.writeheader();writer.writerows(rows)
    (HERE/'pure_translations.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'chapter_units':len(units),'tables':len(tables),'notes':sum(map(len,notes.values())),'status':rows[0]['status']},ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    build('--reviewed' in sys.argv)
