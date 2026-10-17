"""Explicit reviewed lexical map for PDF430; numeric cells are copied verbatim."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=[json.loads(s) for s in (ROOT/'contributions/09/source.jsonl').read_text('utf-8').splitlines()]
lex={
'MERCENARY AVAILABILITY BY REALM SIZE':'Доступность Наёмников по размеру Владения',
'MERCENARY TYPE':'Тип Наёмников','SPECIALIST TYPE':'Тип специалистов',
'CONTINENT':'Континент','EMPIRE':'Империя','KINGDOM':'Королевство','PRINCIPALITY':'Княжество','DUCHY':'Герцогство','COUNTY':'Графство','VISCOUNTY':'Виконтство','BARONY':'Баронство',
'*Population (Families)*':'*Население (семьи) [Population (Families)]*',
'*Time Period*':'*Период [Time Period]*','*Year*':'*Год*','*Season*':'*Сезон*','*Month*':'*Месяц*','*Week*':'*Неделя*',
'Light Infantry':'Лёгкая пехота [Light Infantry]','Heavy Infantry':'Тяжёлая пехота [Heavy Infantry]',
'Slingers':'Пращники [Slingers]','Bowmen':'Лучники [Bowmen]','Crossbowmen':'Арбалетчики [Crossbowmen]',
'Comp. Bowmen/Longbowmen':'Лучники с составными луками / Стрелки [Comp. Bowmen/Longbowmen]',
'Light Cavalry':'Лёгкая конница [Light Cavalry]','Horse Archers':'Конные лучники [Horse Archers]',
'Medium Cavalry':'Средняя конница [Medium Cavalry]','Heavy Cavalry':'Тяжёлая конница [Heavy Cavalry]',
'Cataphract Cavalry':'Катафрактная конница [Cataphract Cavalry]',
'Camel Archers':'Лучники на верблюдах [Camel Archers]','Camel Lancers':'Копейщики на верблюдах [Camel Lancers]',
'War Elephants':'Боевые слоны [War Elephants]','Mtd. Crossbowman':'Конный арбалетчик [Mtd. Crossbowman]',
'Beast Riders':'Всадники на зверях [Beast Riders]',
'AVAILABILITY OF MILITARY SPECIALISTS IN THE REALM':'Доступность военных специалистов во Владении',
'HIRING MERCENARIES AND SPECIALISTS':'Найм Наёмников и специалистов',
'MILITARY SPECIALIST AVAILABILITY BY REALM SIZE':'Доступность военных специалистов по размеру Владения',
'Artillerist':'Артиллерист [Artillerist]','Armorer':'Оружейник [Armorer]',
'Creature Handler — Domestic':'Погонщик — домашние существа [Creature Handler — Domestic]',
'Creature Handler — Wild':'Погонщик — дикие существа [Creature Handler — Wild]',
'Creature Handler — Giant/Prehistoric':'Погонщик — гигантские/доисторические существа [Creature Handler — Giant/Prehistoric]',
'Creature Handler — Fantastic':'Погонщик — фантастические существа [Creature Handler — Fantastic]',
'Marshal — Light Infantry':'Военный наставник — лёгкая пехота [Marshal — Light Infantry]',
'Marshal — Bow, Hvy. Inf., or Light Cavalry':'Военный наставник — лучники, тяжёлая пехота или лёгкая конница [Marshal — Bow, Hvy. Inf., or Light Cavalry]',
'Marshal — Heavy Cavalry or Horse Archer':'Военный наставник — тяжёлая конница или конные лучники [Marshal — Heavy Cavalry or Horse Archer]',
'Marshal — Cataphract':'Военный наставник — катафракты [Marshal — Cataphract]',
'Mercenary Officer — Lieutenant':'Офицер наёмников — лейтенант [Mercenary Officer — Lieutenant]',
'Mercenary Officer — Captain':'Офицер наёмников — капитан [Mercenary Officer — Captain]',
'Mercenary Officer — Colonel':'Офицер наёмников — полковник [Mercenary Officer — Colonel]',
'Mercenary Officer — General':'Офицер наёмников — генерал [Mercenary Officer — General]',
'Quartermaster':'Квартирмейстер [Quartermaster]','Siege Engineer':'Осадный инженер [Siege Engineer]',
}
prose={
'rr.p0430.b004':'Предводители [leaders] Домена [domain] или Владения [realm] (либо их представители) также могут набирать военных специалистов [military specialists] по всему Домену [domain] или Владению [realm] для службы в своих армиях [armies]. Таблица «Доступность военных специалистов по размеру Владения» [Military Specialist Availability by Realm Size] показывает, сколько специалистов [specialists] каждого типа доступно во Владении [realm] каждого размера и сколько времени требуется на их прибытие. Как и для Наёмников [mercenaries], указано минимальное население Владения [realm] данного типа; для более крупных Владений [realms] значения можно пропорционально увеличить. Специалисты [specialists] прибывают с той же скоростью, что и Наёмники [mercenaries]. Как и поиск и найм Наёмников [mercenaries] во Владении [realm], поиск и найм специалистов [specialists] по всему Владению [realm] требует затрат в зм [gp]. Сбор такой же, как при вербовке Наёмников [mercenaries].',
'rr.p0430.b006':'Доступность Наёмников [mercenaries] и специалистов [specialists] ещё не означает, что они автоматически поступят на службу персонажу. Наёмников [mercenaries] нужно завербовать путём переговоров по правилам **«Найм** **Спутников» [Recruiting Hirelings]** (стр. 162). Однако предводители [leaders], собирающие армии [armies], обычно нанимают сразу много Наёмников [mercenaries] и специалистов [specialists], и переговоры с каждым по отдельности заняли бы слишком много времени. Для бросков по таблице «Реакция на предложение найма» [Reaction to Hiring Offer] Арбитр [Judge] объединяет Наёмников [mercenaries] в роты [companies] (120), батальоны [battalions] (500) или бригады [brigades] (2,000). Арбитр [Judge] может закрепить некоторых специалистов [specialists] за конкретными подразделениями [units] Наёмников [mercenaries].',
}
texts={}
for u in source:
    if u['pdf_page']!=430:continue
    e=u['english']
    if u['id'] in prose:t=prose[u['id']]
    elif e in lex:t=lex[e]
    else:
        assert not re.search('[A-Za-zА-Яа-я]',e),(u['id'],e)
        t=e
    texts[u['id']]=t
out=HERE/'parts/p430';out.mkdir(parents=True,exist_ok=True)
(out/'translations.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2)+'\n','utf-8')
(out/'notes.json').write_text('{}\n','utf-8')
(out/'term_map.json').write_text(json.dumps(lex,ensure_ascii=False,indent=2)+'\n','utf-8')
print(len(texts),'units translated; both 19x9 tables retained')
