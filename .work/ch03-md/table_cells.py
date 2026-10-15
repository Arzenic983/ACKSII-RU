"""Explicit translations of non-invariant table cells, reviewed against source."""
from auto_units import HERE, write_records
import json

COMMON={
 'CLASS':'Класс','TITLE':'Звание','RANK (# OF<br>TIMES TAKEN)':'Ранг (число<br>выборов навыка)',
 'GP EARNED<br>/ MONTH':'Заработок,<br>зм/месяц','PATIENTS<br>/ DAY':'Пациентов<br>в день','SKILLS':'Умения',
 'WAGE':'Жалованье','TRAINABLE ANIMALS':'Доступные для обучения животные',
 'CONSTRUCTION<br>RATE':'Темп производства',
 'NUMBER OF WORKERS ALLOWED':'Допустимое число работников',
 'NUMBER OF WORKERS<br>ALLOWED':'Допустимое число работников',
 'FO<br>#(<br>KNAR<br>)NEKAT<br>SEMIT':'Ранг (число выборов навыка)',
 '/<br>DENRAE<br>PG<br>HTNOM':'Заработок, зм/месяц',
 'Animal Husband':'Животновод [Animal Husband]',
 'Veterinarian':'Ветеринар [Veterinarian]',
 'Veterinary Surgeon':'Ветеринарный хирург [Veterinary Surgeon]',
 'Apprentice':'Ученик [Apprentice]','Journeyman':'Подмастерье [Journeyman]',
 'Master':'Мастер [Master]','Grand Master':'Великий мастер [Grand Master]',
 'Healer':'Целитель [Healer]','Physicker':'Лекарь [Physicker]','Chirurgeon':'Хирург [Chirurgeon]',
 'Student':'Ученик [Student]','Expert':'Эксперт [Expert]','Scholar':'Учёный [Scholar]',
 'Master Performer':'Мастер выступлений [Master Performer]',
 'Licensed Practitioner':'Дипломированный практик [Licensed Practitioner]',
 'Master of Profession':'Мастер профессии [Master of Profession]',
 'N. A.':'Не применимо',
 '3 Apprentices':'3 ученика [Apprentices]',
 '2 Journeymen, 4 Apprentices':'2 подмастерья [Journeymen], 4 ученика [Apprentices]',
 '2 Masters, 4 Journeymen, 8 Apprentices':'2 мастера [Masters], 4 подмастерья [Journeymen], 8 учеников [Apprentices]',
 'Identify 11+, extra 1d3 hit points per day':'Определение 11+, дополнительно 1d3 ОЗ [hit points] в день',
 'Identify 7+, *neutralize poison, cure disease, cure light* 18+':'Определение 7+; *Нейтрализация яда [neutralize poison]*, *Исцеление болезни [cure disease]*, *Исцеление лёгкой травмы [cure light]* 18+',
 'Identify 3+, *neutralize poison, cure disease, cure serious* 14+':'Определение 3+; *Нейтрализация яда [neutralize poison]*, *Исцеление болезни [cure disease]*, *Исцеление серьёзной травмы [cure serious]* 14+',
 'Diagnose 11+, extra 1d3 hit points per day':'Диагностика 11+, дополнительно 1d3 ОЗ [hit points] в день',
 'Diagnose 7+, *neutralize poison, cure disease, cure light* 18+':'Диагностика 7+; *Нейтрализация яда [neutralize poison]*, *Исцеление болезни [cure disease]*, *Исцеление лёгкой травмы [cure light]* 18+',
 'Diagnose 3+, *neutralize poison, cure disease, cure serious* 14+':'Диагностика 3+; *Нейтрализация яда [neutralize poison]*, *Исцеление болезни [cure disease]*, *Исцеление серьёзной травмы [cure serious]* 14+',
 'Identify 11+':'Распознавание 11+','Identify 7+':'Распознавание 7+','Identify 3+':'Распознавание 3+',
 'Domestic animal (dog, hawk, horse, etc.)':'Домашнее животное (собака, ястреб, лошадь и т. п.)',
 'Wild animal (bear, lion, etc.)':'Дикое животное (медведь, лев и т. п.)',
 'Dire, giant, or prehistoric animal (cave bear, dire wolf, etc.)':'Лютое [dire], гигантское [giant] или доисторическое [prehistoric] животное (пещерный медведь, лютый волк [dire wolf] и т. п.)',
 'Monstrosity or vermin (griffon, owlbeast, giant black worm, etc.)':'Чудовищное создание [monstrosity] или вредитель [vermin] (грифон, совозверь [owlbeast], гигантский чёрный червь [giant black worm] и т. п.)',
 'CHARACTERISTICS':'Характеристики','BONUS':'Бонус',
 'Bat':'Летучая мышь [Bat]','Cat':'Кошка [Cat]','Crow/Raven':'Ворона/ворон [Crow/Raven]',
 'Eagle':'Орёл [Eagle]','Jackal':'Шакал [Jackal]','Owl':'Сова [Owl]','Rat':'Крыса [Rat]',
 'Tokay Gull':'Токайская чайка [Tokay Gull]','Vulture':'Гриф [Vulture]',
 'Missile weapon':'Дальнобойное оружие [Missile weapon]',
 'Single weapon':'Одно оружие [Single weapon]',
 'Dual weapons':'Два оружия [Dual weapons]',
 'Two-handed weapon':'Двуручное оружие [Two-handed weapon]',
 'Weapon and shield':'Оружие и щит [Weapon and shield]',
 '+1 to attack throws':'+1 к броскам атаки [attack throws]',
 '+1 to initiative':'+1 к инициативе [initiative]',
 '+1 to damage rolls':'+1 к броскам урона [damage rolls]',
 '+1 to armor class':'+1 к Классу брони [armor class]',
}

FAMILIARS={
 'rr.p0113.t01.r002.c02':'Скорость [Spd] полёта 120 футов, КБ [AC] 3, КЗ [HD] 1/4, атак [#AT] 1, урон [Dmg] 1, эхолокация [echolocation]',
 'rr.p0113.t01.r003.c02':'Скорость [Spd] 210 футов, КБ [AC] 3, КЗ [HD] 1/2, атак [#AT] 3, урон [Dmg] 1/1/1, острый слух и обоняние [acute hearing & olfaction], проворство [agile], лазание [climber] 6+, наскок [pounce], природная скрытность [naturally stealthy]',
 'rr.p0113.t01.r004.c02':'Скорость [Spd] полёта 330, КБ [AC] 3, КЗ [HD] 1/4, атак [#AT] 1, урон [Dmg] 1d2-1, острое зрение [acute vision]',
 'rr.p0113.t01.r005.c02':'Скорость [Spd] полёта 480 футов, КБ [AC] 3, КЗ [HD] 1/2, атак [#AT] 2, урон [Dmg] 1d2/1d2, острое зрение [acute vision], внимательность [alertness], пикирование [dive]',
 'rr.p0113.t01.r006.c02':'Скорость [Spd] 180 футов, КБ [AC] 2, КЗ [HD] 1-1, атак [#AT] 1, урон [Dmg] 1d4, острое … и обоняние [acute & olfaction], выслеживание [tracking]',
 'rr.p0113.t01.r007.c02':'Скорость [Spd] полёта 300 футов, КБ [AC] 3, КЗ [HD] 1/4, атак [#AT] 2, урон [Dmg] 1/1, острый слух [acute hearing], острое зрение [acute vision], внимательность [alertness], пикирование [dive], ночное зрение [night vision], подкрадывание [sneak] 6+',
 'rr.p0113.t01.r008.c02':'Скорость [Spd] 120 футов / плавание [swim] 60 футов, КБ [AC] 2, КЗ [HD] 1/2, атак [#AT] 1, урон [Dmg] 1d3, острый слух [acute hearing], умелое лазание [skilled climber] 5+',
 'rr.p0113.t01.r009.c02':'Скорость [Spd] полёта 150 футов, КБ [AC] 2, КЗ [HD] 1/2, атак [#AT] 1, урон [Dmg] 1d3, лай [bark], ночное зрение [night vision], природное лазание [natural climber]',
 'rr.p0113.t01.r010.c02':'Скорость [Spd] полёта 300 футов, КБ [AC] 3, КЗ [HD] 1/2, атак [#AT] 2, урон [Dmg] 1d2/1d2, острое обоняние и зрение [acute olfaction & vision], неуязвимость [immunity] к обычным болезням [mundane disease] и яду [poison]',
}

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    values={u['id']:COMMON[u['source_markup']] for u in units if u['table_id'] and u['source_markup'] in COMMON}
    values.update(FAMILIARS)
    write_records(HERE/'tables.md',values)
    print('Explicit table units:',len(values))

if __name__=='__main__':main()
