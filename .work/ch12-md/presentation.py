"""Lossless page-480 column and diagram reconstruction, checked against PDF."""
from pathlib import Path
import json
from labels import decorate
HERE=Path(__file__).resolve().parent
def key(n,i=0):return (f'rr.p0480.b{n:03}',i)
GROUPS=[
    ('ordinary',[key(n)]) for n in range(1,10)
]+[
    ('paragraph',[key(19),key(21),key(22),key(24)]),
    ('diagram',[key(18),key(21,1),key(24,1),key(27,3),key(27)]),
    ('heading',[key(25),key(27,2)]),
    ('paragraph',[key(28)]),
    ('paragraph',[key(29),key(10)]),
]+[('ordinary',[key(n)]) for n in range(11,18)]+[
    ('paragraph',[key(20),key(21,2),key(23),key(24,2),key(26),key(27,1),key(27,4),key(30)])
]
def render(source,pure,meta,notes,inline):
    ru_parts=json.loads((HERE/'presentation_parts.json').read_text('utf-8'))
    en_parts=json.loads((HERE/'source_parts.json').read_text('utf-8'))
    for uid,parts in en_parts.items():
        assert ' '.join(parts)==meta[uid]['english'],uid
        assert len(parts)==len(ru_parts[uid])
        assert ' '.join(ru_parts[uid])==pure[uid]
    parts={u['id']:ru_parts.get(u['id'],[pure[u['id']]]) for u in source if u['pdf_page']==480}
    wanted={(uid,i) for uid,p in parts.items() for i in range(len(p))}
    refs=[ref for _,group in GROUPS for ref in group]
    assert len(refs)==len(set(refs)) and set(refs)==wanted,'Missing or repeated display fragments'
    seen=set();md=[]
    def fragment(ref,heading=False):
        uid,i=ref
        prefix=''
        if uid not in seen:
            seen.add(uid);prefix=f'<!-- unit: {uid} --><a id="{uid}"></a>'
        text=parts[uid][i]
        if not heading:text=decorate(text)
        return prefix+f'<span data-unit="{uid}" data-part="{i}">'+inline(text)+'</span>'
    def after(group):
        for uid in dict.fromkeys(uid for uid,_ in group):
            if uid in notes:md.extend(['> \\* '+notes[uid],''])
    for kind,group in GROUPS:
        uid=group[0][0]
        if kind=='ordinary':kind='heading' if meta[uid]['kind']=='heading' else 'paragraph'
        if kind=='heading':
            text=' '.join(fragment(r,True) for r in group)
            title='DEPLOYING THE ARMIES' if uid==key(25)[0] else meta[uid]['english']
            md.extend(['#'*(meta[uid]['heading_level'] or 4)+' '+text+('<sup>*</sup>' if uid in notes else ''),'','<small>'+title+'</small>',''])
        elif kind=='paragraph':
            md.extend(['<p>'+' '.join(fragment(r) for r in group)+('<sup>*</sup>' if any(r[0] in notes for r in group) else '')+'</p>',''])
        else:
            # Four nested zones reproduce the source diagram without inventing
            # a tenth source table. Each extracted label is used exactly once.
            md.append('<div role="img" aria-label="Зоны штурма: резерв, штурм, крепостные стены, внутренняя часть крепости" style="box-sizing:border-box;max-width:640px;border:2px solid;padding:16px;text-align:center;margin:20px auto;background:#f4eeee">')
            md.append(fragment(group[0]))
            md.append('<div style="border:2px solid;padding:16px;margin:12px;background:#e8dada">'+fragment(group[1]))
            md.append('<div style="border:2px solid;padding:16px;margin:12px;background:#d8c0c0">'+fragment(group[2]))
            md.append('<div style="border:2px solid;padding:28px 12px;margin:12px;background:#c9aaaa">'+fragment(group[3],True)+' '+fragment(group[4],True)+' [Stronghold Interior]</div>')
            md.extend(['</div></div></div>',''])
        after(group)
    assert seen==set(parts)
    return md
