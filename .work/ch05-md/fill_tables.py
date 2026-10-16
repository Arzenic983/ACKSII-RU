"""Explicit table translations and fixed mechanical labels; no database writes."""
import json,re,sys
from auto_units import HERE
def main():
    us=json.loads((HERE/'source_units.json').read_text('utf-8'));byid={u['id']:u['source_markup'] for u in us}
    labels=json.loads((HERE/'table_terms.json').read_text('utf-8'))
    for line in (HERE/'table_terms_extra.txt').read_text('utf-8').splitlines():
        if line:
            en,ru=line.split(' | ',1);labels[en]=ru
    levels={'FIRST':'ПЕРВОГО','SECOND':'ВТОРОГО','THIRD':'ТРЕТЬЕГО','FOURTH':'ЧЕТВЁРТОГО','FIFTH':'ПЯТОГО','SIXTH':'ШЕСТОГО'}
    for u in us:
        en=u['source_markup']
        m=re.fullmatch(r'(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH) LEVEL (ARCANE|DIVINE) SPELLS',en)
        if m:labels[en]=('ТАЙНЫЕ' if m[2]=='ARCANE' else 'БОЖЕСТВЕННЫЕ')+' ЗАКЛИНАНИЯ '+levels[m[1]]+' УРОВНЯ'
        if re.fullmatch(r'\d+d\d+ \[mundane bludgeoning\](?: \(\d+’ radius\))?',en):
            labels[en]=en.replace('[mundane bludgeoning]','[обычного дробящего] [mundane bludgeoning]').replace('radius','радиус')
    long={
    'rr.p0182.t01.r002.c03':'Используют Девы клинков [Bladedancer], Крестоносцы [Crusader], Жрицы [Priestess] и Шаманы [Shaman], молитвой обращающиеся к силе бессмертных божеств.',
    'rr.p0182.t01.r003.c02':'Используют Эльфийские ночные клинки [Elven Nightblade], Эльфийские мечники-чародеи [Elven Spellsword], Маги [Mage], Нобиранские чудотворцы [Nobiran Wonderworker], Колдуны [Warlock] и Захарские стражи руин [Zaharan Ruinguard], установленными процедурами обращающиеся к разлитой в космосе силе.',
    'rr.p0182.t01.r003.c03':'Используют Дварфийские мастера-жрецы [Dwarven Craftpriest], установленными процедурами обращающиеся к духам предков и древним реликвиям; и Ведьмы [Witch], такими процедурами уговаривающие, принуждающие и упрашивающие древние силы.',
    'rr.p0211.t01.r002.c02':'Экспедиционная скорость [expedition speed] вдвое меньше. Без защитной одежды или при намокании существо сразу получает Переохлаждение [hypothermic], теряет 1d3 ТЕЛ [CON] в час и немедленно делает спасбросок Смерть [Death] или получает обморожение [frostbitten]. Грязь сразу замерзает. -2 к броскам Соблазнения [Seduction].',
    'rr.p0211.t01.r004.c02':'Экспедиционная скорость [expedition speed] вдвое меньше. В тяжёлых доспехах [heavy armor] немедленно делают спасбросок Смерть [Death] или становятся Истощёнными [fatigued]. Норма воды больше на 25%, Обезвоживание [Dehydration] вызывает двойную потерю ТЕЛ [CON]. Снег тает и грязь сохнет мгновенно; при естественном зное [sweltering] на это нужен день.',
    'rr.p0211.t01.r009.c02':'Все дальнобойные атаки [missile attacks] и броски Подслушивания [listening throws] получают -4. Воздушная [air speed] и экспедиционная [expedition speed] скорости вдвое меньше. На всех действует *порыв ветра [gale of wind]*. В пустошах [barren] и пустыне [desert] пыль снижает максимальную видимость [maximum visibility] до 20’. Морские суда [vessels] могут пострадать или дрейфовать (стр. 319).',
    'rr.p0211.t01.r011.c02':'В выбранной точке области [area of effect] возникает смерч [tornado] высотой 100’ и диаметром 25’. Он перекрывает линию видимости [line of sight], не пропускает снаряды [missiles] и магию. В свою инициативу [initiative] заклинатель [caster] может перемещать его внутри области [area of effect] на 120’ за раунд [round]. На существо, на которое смерч [tornado] надвинулся в инициативу [initiative] заклинателя [caster] или которое вошло само, совершается атака как подготовленным [readied] чудовищем с 2 КЗ [HD]: одна атака с 1d8 [особого рубящего] [extraordinary slashing] урона. Затем нужен успешный спасбросок Паралич [Paralysis], иначе существо Опрокинуто [prone] и отброшено на 5’ от края. Большие [Large] и более крупные получают +4 к спасброску [saving throw] за каждую категорию размера [size category] выше человеческой [man-sized]. До вызова смерча [tornado] сначала необходимо установить бурю [stormy].',
    }
    for id,ru in long.items():labels[byid[id]]=ru
    (HERE/'table_terms.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2),'utf-8')
if __name__=='__main__':main()
