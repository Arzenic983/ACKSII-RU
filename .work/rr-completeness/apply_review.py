"""Apply the documented RR audit corrections to full chapters and exchange files."""
from pathlib import Path
import csv, hashlib, json, re, sqlite3

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'
PACK=ROOT/'contributions/rr-completeness'

UPDATES={
 'rr.p0205.b019':{
  'russian':'В начале своей инициативы каждое существо, ставшее беспомощным под действием этого заклинания, получает 1d4 [особого некротического] урона от мучительной боли во всём теле, а затем совершает ещё один спасбросок от смерти. Если спасбросок успешен, действие заклинания заканчивается для этого существа. Если спасбросок провален, существо остаётся беспомощным. Эффекты *Круга агонии* продолжаются, пока **не будут рассеяны** либо пока цели не умрут или не совершат успешный спасбросок. Заклинателю не нужно концентрироваться, чтобы поддерживать эти эффекты.',
  'markdown':'В начале своей инициативы [initiative] каждое существо, ставшее беспомощным [helpless] под действием этого заклинания, получает 1d4 [особого некротического] [extraordinary necrotic] урона от мучительной боли во всём теле, а затем совершает ещё один спасбросок от смерти [Death saving throw]. Если спасбросок [saving throw] успешен, действие заклинания заканчивается для этого существа. Если спасбросок [saving throw] провален, существо остаётся беспомощным [helpless]. Эффекты *Круга агонии [Circle of Agony]* продолжаются, пока **не будут рассеяны [dispelled]** либо пока цели [targets] не умрут или не совершат успешный спасбросок [saving throw]. Заклинателю [caster] не нужно концентрироваться, чтобы поддерживать эти эффекты.',
  'note':'Исправление при итоговой сверке RR: initiative передано как «инициатива», убран повтор слова «некротического», восстановлены категория спасброска от смерти, выделение dispelled и читаемое условие окончания эффекта. Повреждённое Markdown-сочетание «цель [target](и)» заменено формой множественного числа. Сверено по EN checked и изображению PDF 205; числа и условия оригинала сохранены.'},
 'rr.p0296.b034':{
  'russian':"**Атака:** Совершите одну или несколько атак в зависимости от последовательности атак. Если боец оставался на месте и не находится **вплотную** к противнику, при атаке он может переместиться на расстояние до 5 футов в сторону противника, если это нужно, чтобы вступить с ним в бой вплотную. Атака может включать особые манёвры, рассечения и т. д.",
  'markdown':"**Атака:** Совершите одну или несколько атак в зависимости от последовательности атак [attack sequence]. Если боец [combatant] оставался на месте и не находится **вплотную [engaged]** к противнику, при атаке он может переместиться на расстояние до 5 футов в сторону противника, если это нужно, чтобы вступить с ним в бой вплотную [engage]. Атака может включать особые манёвры [special maneuvers], рассечения [Cleave] и т. д.",
  'note':'Учтены комментарии 7–9 к старому разделу COMBAT: attack sequence — «последовательность атак» по глоссарию, а не «очередность атаки». Уточнены remained stationary и is not engaged; восстановлены «до 5 футов» и исходное выделение. Проверены EN checked и изображение PDF 296; новое правило не добавлено.'},
}
NOTES={
 'rr.p0058.b001':'Прежний комментарий к словарю предлагает название «Танцор с клинками» для Bladedancer. В переводе сохранена словарная «Дева клинков [Bladedancer]»; предложение о смене названия передано главному переводчику и не считается утверждённым.',
 'rr.p0108.b015':'В прежнем переводе предложено пересмотреть название Arcane Dabbling. Здесь сохранена действующая словарная форма «Основы магии [Arcane Dabbling]»; отдельного утверждения нового названия нет.',
 'rr.p0109.b003':'В прежнем переводе предложено пересмотреть название Armor Training. Здесь сохранена действующая словарная форма «Тренировка в доспехах [Armor Training]»; отдельного утверждения нового названия нет.',
 'rr.p0112.b002':'Вопрос прежнего переводчика о пильтбире [piltbier] остаётся открытым: RR не даёт самостоятельного определения этого названия и отсылает за подробностями к главе 9 «Дварфийская микокультура [Dwarven Mycoculture]» книги By This Axe. Русская передача названия рабочая; состав напитка не придуман.',
 'rr.p0171.b001':'В комментарии к прежнему словарю отмечено, что Наёмник [Mercenary] и Наёмник [Sell-sword / Man-at-arms] имеют одно русское имя. Словарные формы сохранены с английскими привязками; разведение названий требует решения главного переводчика.',
 'rr.p0182.b009':'Прежний комментарий предлагает заменить название «Учёный» для заклинателей [studious spellcasters] и их репертуара [studious repertoire]. Сохранена действующая словарная форма «Учёные заклинатели [Studious Spellcasters]»; иное название не утверждено.',
 'rr.p0336.t01.r017.c02':'В прежних комментариях к словарю для Капища [Medicine Lodge] предложен «Госпиталь» и уточнено, что речь идёт о месте молитвы Шамана [Shaman]. Сохранено словарное «Капище [Medicine Lodge]»; выбор нового русского названия остаётся за главным переводчиком.',
}

def main():
    assert not (HERE/'applied.json').exists(),'Already applied; do not replay stale revisions'
    db=sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    rows={u['id']:dict(u) for u in db.execute('SELECT * FROM bilingual')}
    chapters={u['id']:dict(u) for u in db.execute('SELECT * FROM chapters')}
    edits={};packages={};new_notes={**NOTES,**{uid:item['note'] for uid,item in UPDATES.items()}}
    for uid,note in new_notes.items():
        u=rows[uid];ch=chapters[u['chapter_id']]
        path=OUT/('00 Начало.md' if ch['id']=='front_matter' else ch['id']+' '+ch['title_ru']+'.md')
        md=edits.setdefault(path,path.read_text('utf-8'))
        marker='<!-- unit: '+uid+' -->';start=md.index(marker)
        if u['kind']=='table_cell':
            end=md.index('</td>',start)
            md=md[:end]+'<sup>*</sup>'+md[end:]
            end=md.index('</table>',end)+len('</table>')
            md=md[:end]+'\n\n> \\* '+note+md[end:]
        else:
            anchor='<a id="'+uid+'"></a>'
            body_start=md.index(anchor,start)+len(anchor)
            next_match=re.search(r'\n(?:<!-- unit:|<a id="pdf-page-|<!-- table:)',md[body_start:])
            end=body_start+next_match.start() if next_match else len(md)
            body=md[body_start:end].strip()
            if uid in UPDATES:body=UPDATES[uid]['markdown']
            if u['kind']=='heading':
                body=re.sub(r'^(#{1,6} [^\n]+)',r'\1<sup>*</sup>',body,count=1)
            else:body+='<sup>*</sup>'
            md=md[:body_start]+'\n\n'+body+'\n\n> \\* '+note+'\n\n'+md[end:].lstrip('\n')
        edits[path]=md
        record={k:u[k] for k in ('id','chapter_id','pdf_page','printed_page','kind','english','russian','status','revision','note','source_sha256')}
        record['russian']=UPDATES.get(uid,{}).get('russian',u['russian'])
        record['note']=((u['note'] or '')+'\n\n'+note).strip()
        record['status']='reviewed';packages.setdefault(ch['id'],[]).append(record)
    PACK.mkdir(parents=True,exist_ok=True)
    for ch,records in packages.items():
        with (PACK/(ch+'_corrections.jsonl')).open('w',encoding='utf-8') as f:
            for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
        with (PACK/(ch+'_corrections.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]),delimiter=';');w.writeheader();w.writerows(records)
    for path,md in edits.items():path.write_text(md,'utf-8')
    summary=OUT/'Примечания редактора.md'
    extra='\n\n## Итоговая сверка RR — замечания прежних переводчиков\n\n'
    for uid,note in new_notes.items():extra+='<!-- unit: '+uid+' -->\n'+note+'\n\n'
    summary.write_text(summary.read_text('utf-8').rstrip()+extra,'utf-8')
    (HERE/'applied.json').write_text(json.dumps({'units':list(new_notes),'chapters':list(packages),'notes':new_notes,
        'meaning_changes':list(UPDATES),'files':[str(p.relative_to(ROOT)) for p in edits]},ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Prepared',sum(map(len,packages.values())),'records;',len(UPDATES),'text corrections;',len(new_notes),'notes')

if __name__=='__main__':main()
