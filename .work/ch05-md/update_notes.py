"""Retain source disagreements and identify explicit draft corrections beside the text."""
import json
from auto_units import HERE,records
def main():
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    for id in list(notes):
        notes[id]=[n for n in notes[id] if not n.startswith(('Исправление перевода:','Разночтение типов в оригинале:'))]
        if not notes[id]:del notes[id]
    corrected=set()
    for p in HERE.glob('corrections_review_*.md'):corrected.update(records(p))
    corrected.update(json.loads((HERE/'glossary_corrections.json').read_text('utf-8')))
    sections=json.loads((HERE/'candidate_alignment.json').read_text('utf-8'))
    for s in sections:
        touched=corrected&{u['id'] for u in s['source']}
        if touched:
            id=s['source'][0]['id']
            notes.setdefault(id,[]).append('Исправление перевода: черновик сопоставлен с английским описанием; восстановлены пропущенные условия, ссылки, текст и значения. Исправленные фрагменты: '+', '.join(sorted(touched))+'.')
    diffs=json.loads((HERE/'english_list_differences.json').read_text('utf-8'))
    for d in diffs:
        notes.setdefault(d['id'],[]).append('Разночтение типов в оригинале: здесь указано '+', '.join('['+t+']' for t in d['list_types'])+'; английское описание на PDF '+str(int(d['description_id'][4:8]))+' (`'+d['description_id']+'`) указывает «'+d['description']+'». Оба английских места сверены, оба исходных набора типов сохранены без исправления.')
    notes.setdefault('rr.p0204.b009',[])
    detail='Сверка двух глав: английские PDF 119 (`rr.p0119.b023`) и PDF 204 одинаково дают мастеру-моряку [master mariner] с тремя рангами Мореплавания [Seafaring] бонус +4; ошибочные +5 в черновике исправлены в пользу обоих оригиналов.'
    if detail not in notes['rr.p0204.b009']:notes['rr.p0204.b009'].append(detail)
    extra={
      'rr.p0207.b024':'Неопределённость оригинала: английское описание требует saving throw, но не называет категорию спасброска. Категория не добавлена переводчиком.',
      'rr.p0211.b011':'Ошибка ссылки в оригинале: здесь указана глава 12, Sailing the Seas, печатные стр. 318–319. Английский заголовок SAILING THE SEAS (`rr.p0320.b003`, PDF 320, печатная стр. 318) находится в главе 7 VOYAGES (`rr.p0316.b001`). Обе английские главы сверены; исходная ссылка «глава 12» сохранена.',
      'rr.p0236.b016':'Разночтение оригинала: предыдущий английский абзац (`rr.p0236.b015`) ограничивает ковёр тремя существами человеческого размера [man-sized], а здесь падение начинается при числе более четырёх. Оба ограничения переданы как напечатано. В предыдущем абзаце скорость 240/180 футов за ход [turn] также названа encounter speed; термин и единица сохранены.',
      'rr.p0250.b003':'Разночтение оригинала: в Duration и описании указаны три дополнительных раунда [rounds] после прекращения концентрации [concentration], но в конце того же английского предложения сказано «в конце следующей инициативы [initiative] заклинателя [caster]». Оба условия сохранены.',
      'rr.p0261.b012':'Особенность оригинала: ограничение человеческим размером [man-sized] здесь относится к заклинателю [caster], хотя способность получает другой получатель [recipient]. Условие сохранено без переноса на получателя [recipient].',
      'rr.p0181.b003':'Сверка со словарём: в прежнем черновике исправлены КБ [AC], Кости Здоровья [Hit Dice], Очки Здоровья [hit points], Подкрадывание [Sneaking] как навык, Глухой [Deafened], Обессиленный [Enervated], Скованный [Restrained], Изгнание нежити [Rebuke undead], Подслушивание [Listening], Природоведение [Naturalism], Санктум [Sanctum] и Игра со смертью [Tampering with Mortality]. Новые названия заклинаний и существ остаются рабочими; утверждённый глоссарий не изменён.',
    }
    for id,note in extra.items():
        if note not in notes.setdefault(id,[]):notes[id].append(note)
    (HERE/'notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),'utf-8')
    print('Notes',sum(map(len,notes.values())))
if __name__=='__main__':main()
