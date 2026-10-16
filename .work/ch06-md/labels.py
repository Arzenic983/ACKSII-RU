from common import read,write,HERE
import re
HEADINGS=r'''
6 ADVENTURES | 6. Приключения
ADVENTURES | Приключения
DELVES, EXPEDITIONS, AND VOYAGES | Вылазки, экспедиции и плавания
DUNGEON DELVES | Вылазки в подземелья
TURNS AND ROUNDS | Ходы и раунды
SPEED AND DISTANCE | Скорость и расстояние
MARCHING AND MAPPING | Походный порядок и картографирование
LIGHT AND DARKNESS | Свет и тьма
SEARCHING AND LISTENING | Поиск и Подслушивание
LISTENING | Подслушивание
EARSHOT BY SOUND AND ENVIRONMENT | Слышимость в зависимости от звука и обстановки
DOORS AND DUNGEONBASHING | Двери и Проламывание
DOOR AND PORTAL ARMOR CLASS AND STRUCTURAL HIT POINTS TABLE | Класс брони и конструкционные ОЗ дверей и проёмов
OPENING DOOR METHOD TABLE | Способы открывания дверей
DISABLING TRAPS METHOD TABLE | Способы обезвреживания ловушек
TRAPS AND TRAPBREAKING | Ловушки и Обезвреживание ловушек
CAVING AND SPELUNKING | Преодоление препятствий в пещерах
RAPPELLING | Спуск по верёвке
BALANCING TRAVERSE | Прорывание с балансированием
BELAYING | Страховка
JUMPING AND LEAPING | Прыжки в длину и высоту
PROFICIENCY BONUSES TO JUMPING AND LEAPING | Бонусы навыков к прыжкам в длину и высоту
SQUEEZING | Протискивание
SWIMMING AND DROWNING | Плавание и утопление
REST AND RECUPERATION | Отдых и восстановление
WILDERNESS EXPEDITIONS | Экспедиции в диких землях
HOURS AND DAYS | Часы и дни
COMBAT AND RUNNING SPEED | Боевая скорость и скорость бега
FLIGHT SPEED | Скорость полёта
VISIBILITY IN THE WILD | Видимость в диких землях
SEARCHING THE WILD | Поиск в диких землях
SEARCHING FOR SPECIFIC POINTS OF INTEREST | Поиск определённого интересного места
AERIAL RECONNAISSANCE | Воздушная разведка
WANDERING MONSTERS | Блуждающие монстры
SPLITTING UP | Разделение группы
NAVIGATING THE WILD | Навигация в диких землях
SURVIVING THE WILD | Выживание в диких землях
STARVATION | Голодание
DEHYDRATION | Обезвоживание
HUNTING AND FORAGING | Охота и собирательство
SURVIVAL, SIMPLIFIED | Упрощённое выживание
WEATHERING THE WILD | Погода в диких землях
FRIGID TEMPERATURES | Мороз
COLD TEMPERATURES | Холод
SWELTERING TEMPERATURES | Зной
MODERATE TEMPERATURES | Умеренная температура
DRIZZLY CONDITIONS | Морось
FAIR CONDITIONS | Хорошая погода
FLURRY CONDITIONS | Слабый снег
FOGGY CONDITIONS | Туман
RAINY CONDITIONS | Дождь
SNOWY CONDITIONS | Снегопад
SUNBAKED CONDITIONS | Солнцепёк
STORMY CONDITIONS | Шторм
WINDY CONDITIONS | Ветер
MUD AND SNOW | Грязь и снег
EFFECTS OF TEMPERATURE ON CREATURES | Влияние температуры на существ
SLEEPING WITH EQUIPMENT | Сон со снаряжением
ENCOUNTERS | Столкновения
ENCOUNTER DISTANCE | Дистанция столкновения
DUNGEON ENCOUNTERS | Столкновения в подземельях
WILDERNESS ENCOUNTERS | Столкновения в диких землях
WILDERNESS ENCOUNTER DISTANCE TABLE | Дистанция столкновения в диких землях
SURPRISE MATRIX | Матрица внезапности
SURPRISE | Внезапность
SURPRISE TABLE | Таблица внезапности
SURPRISE AND HIDING | Внезапность и Прятание
SURPRISE AND SNEAKING | Внезапность и Подкрадывание
SURPRISE AND SLEEPING | Внезапность и сон
EVASION | Избегание
EVASION THROW BY TERRAIN TABLE | Бросок Избегания в зависимости от местности
AFTERMATH OF EVASION | После избегания
EVASION BY MONSTERS | Избегание монстрами
REACTIONS | Реакции
ENCOUNTER REACTION TABLE | Реакция при столкновении
ATTEMPTING TO INFLUENCE REACTIONS | Попытки повлиять на реакцию
OFFERING BRIBES | Предложение взятки
COST OF BRIBES | Размер взятки
COMBAT | Бой
SIMULATING COMBAT ON THE BATTLEMAP | Симуляция боя на боевой карте
SQUARE SCALE | Масштаб клеток
COMBATANT FRONTAGE AND INTERVAL | Фронт и интервал бойцов
FACING, FIELD OF VIEW AND LINE OF SIGHT | Направление, поле зрения и линия видимости
PASSAGE OF LINES | Прохождение сквозь строй
ROUND AND INITIATIVE | Раунд и инициатива
ROUND SEQUENCE | Порядок раунда
ACTING BEFORE INITIATIVE NUMBER | Действия до своего номера инициативы
ENGAGEMENT | Связывание боем Вплотную
DELAYING ACTIONS | Задержка действий
ENGAGEMENT BY SMALLER OR LARGER CREATURES | Бой Вплотную с существами меньшего или большего размера
SIMULTANEOUS INITIATIVE | Одинаковая инициатива
ACTIONS | Действия
FULL ROUND ACTIONS | Действия полного раунда
MOVEMENT ACTIONS | Действия движения
COMBAT ACTIONS | Боевые действия
READIED ACTIONS | Подготовленные действия
CONDUCTING AN ATTACK | Проведение атаки
ATTACK THROWS BY LEVEL AND HD | Броски атаки по уровню и КЗ
MELEE ATTACKS | Ближние атаки
MISSILE ATTACKS | Дальнобойные атаки
MISSILE WEAPON RANGES | Дистанции дальнобойного оружия
MISSILE ATTACKS VS. TROOP FORMATIONS | Дальнобойные атаки по войсковым построениям
MISSILE ATTACKS WITH BURNING OIL, HOLY WATER, AND TORCHES | Дальнобойные атаки горящим маслом, святой водой и факелами
MISSILE ATTACKS WITH ARTILLERY | Дальнобойные атаки артиллерией
DEALING DAMAGE | Нанесение урона
DAMAGE TYPE IMMUNITY AND RESISTANCE | Неуязвимость и устойчивость к типу урона
EFFECTS OF DAMAGE | Последствия урона
HEALING | Лечение
NONLETHAL DAMAGE | Нелетальный урон
CLEAVING | Рассечение
CLEAVING IN MELEE | Рассечение в ближнем бою
CLEAVING WITH MISSILE WEAPONS | Рассечение дальнобойным оружием
CLEAVING IN MASS COMBAT (OPTIONAL) | Рассечение в массовом бою (опциональное правило)
SAVING THROWS | Спасброски
SAVING THROW ADJUSTMENTS FROM COVER | Модификаторы спасбросков от укрытия
SIZE-ADJUSTED SAVING THROWS | Спасброски с поправкой на размер
SAVING THROW TABLES | Таблицы спасбросков
FIGHTER SAVING THROWS | Спасброски воина
CRUSADER SAVING THROWS | Спасброски крестоносца
THIEF SAVING THROWS | Спасброски вора
MAGE SAVING THROWS | Спасброски мага
CASTING SPELLS AND USING MAGIC | Произнесение заклинаний и применение магии
SPECIAL MANEUVERS | Специальные манёвры
BRAWLING | Кулачный бой
CLAMBER | Вскарабкивание
COUP DE GRACE | Добивание
DISARM | Разоружение
FORCE BACK | Отталкивание
INCAPACITATE | Выведение из строя
KNOCK DOWN | Сбить с ног
OVERRUN | Пробиться
SUNDER | Разделение
SWEEP ATTACK | Размашистая атака
WRESTLING | Борьба
CONDITIONS | Состояния
GENERAL RULES FOR CONDITIONS | Общие правила состояний
ESCAPING FROM THE GRABBED, RESTRAINED, AND WRESTLED CONDITIONS | Освобождение из состояний Схваченный, Скованный и Скрученный
MONSTER MORALE TABLE | Боевой дух монстров
MORALE RESULTS | Результаты боевого духа
MOUNTED ATTACK TABLE | Атаки верхом
THE PERILS OF COWARDICE | Опасности трусости
MOUNTED INITIATIVE AND MOVEMENT | Инициатива и передвижение верхом
MOUNTED ATTACKS | Атаки верхом
MOUNTED DEFENSES | Защита верхом
VEHICLE ATTACK TABLE | Атаки на транспорте
VEHICLE COMBAT | Бой на транспорте
VEHICLE INITIATIVE, MOVEMENT, AND ATTACKS | Инициатива, передвижение и атаки транспорта
VEHICLE ATTACKS | Атаки транспорта
VEHICLES AND DAMAGE | Транспорт и урон
EARNING EXPERIENCE FROM ADVENTURES | Получение Опыта за приключения
EXPERIENCE FROM TREASURE | Опыт за сокровища
NON-MAGICAL TREASURE | Немагические сокровища
MAGICAL TREASURE | Магические сокровища
OTHER TREASURE | Прочие сокровища
EXPERIENCE FROM MONSTERS | Опыт за монстров
MONSTER EXPERIENCE POINTS TABLE | Очки Опыта за монстров
ALLOCATING XP | Распределение Опыта
ADJUSTMENTS TO XP | Модификаторы Опыта
CHARACTER ADVANCEMENT | Развитие персонажа
CHARACTER DEATH | Смерть персонажа
RESERVE XP FUND | Резервный фонд Опыта
HEROIC FUNERALS | Героические похороны
INHERITANCE | Наследство
0TH LEVEL CHARACTERS AND EXPERIENCE FROM ADVENTURING | Персонажи 0-го уровня и Опыт за приключения
'''
CELLS=r'''
SOUND | Звук
QUIET ENVIRONMENT | Тихая обстановка
NORMAL ENVIRONMENT | Обычная обстановка
LOUD ENVIRONMENT | Шумная обстановка
Exploring, Quiet Spellcasting, Sneaking\*, Whispering | Исследование, тихое произнесение заклинаний, Подкрадывание\*, шёпот
Spellcasting, Talking, Walking | Произнесение заклинаний, разговор, ходьба
Fighting, Hustling, Shouting, Singing | Бой, быстрое движение, крик, пение
Blast Spell | Заклинание с громким взрывом
Deafening Blast Spell | Заклинание с оглушительным взрывом
SEARCHING & LISTENING | Поиск и Подслушивание
HASTY SEARCH | Поспешный поиск
METHODICAL SEARCH | Методичный поиск
LISTEN | Подслушивание
Time Required | Требуемое время
1 round or exploration movement | 1 раунд или движение со скоростью исследования
1 round, once per turn | 1 раунд, раз в ход
Area Investigated | Исследуемая область
5’ reach, or 10’ reach with pole | Досягаемость 5 футов или 10 футов с шестом
Door or intersection | Дверь или перекрёсток
Using Adventuring | С Авантюризмом
Not permitted | Недоступно
Using Adventuring + Alertness | С Авантюризмом + Внимательностью
Using Searching/Listening | С Поиском/Подслушиванием
By class level | По уровню класса
By class level, +4 bonus | По уровню класса, бонус +4
Successful Throw | Успешный бросок
Feature discovered | Объект обнаружен
Featured discovered | Объект обнаружен
Sound heard | Звук услышан
Failed Throw | Проваленный бросок
Nothing discovered, cannot repeat | Ничего не найдено; повторять нельзя
Nothing discovered, try again | Ничего не найдено; можно повторить
Nothing heard, try again | Ничего не услышано; можно повторить
DOOR | Дверь
NOTES | Примечания
Harmed as stone structure | Повреждается как каменное строение
Broken down in 3 turns with axe or harmed as wood structure | Разрубается топором за 3 хода или повреждается как деревянное строение
Broken down in 1 turn with axe or harmed as wood structure | Разрубается топором за 1 ход или повреждается как деревянное строение
Broken open in 1 round with any weapon | Разбивается любым оружием за 1 раунд
OPENING DOORS | Открывание дверей
USE KEY | Ключ
HASTILY PICK | Поспешный взлом
METHODICALLY PICK | Методичный взлом
BATTER DOWN | Разрубить
BASH OPEN | Вышибить
1 action | 1 действие
1 – 3 turns | 1–3 хода
Throw Required | Требуемый бросок
Lockpicking | Взлом
Lockpicking, +4 bonus | Взлом, бонус +4
Dungeonbashing | Проламывание
Open lock | Замок открыт
Door opens | Дверь открыта
Cannot hastily pick | Поспешный взлом недоступен
Failed to pick, try again | Не взломан; можно повторить
Failed to bash, try again | Не вышиблена; можно повторить
Botch (2 - 3) | Грубая ошибка (2–3)
Lock jammed | Замок заклинило
Botched Throw (1) | Грубая ошибка (1)
Suffer 1 [mundane bludgeoning] damage, try again | Получить 1 обычного дробящего урона; можно повторить
Equipment Required | Требуемое снаряжение
Key | Ключ
Thieves’ tools | Воровские инструменты
Axe | Топор
Crowbar (optional, +2) | Лом (необязателен, +2)
DISABLING TRAPS | Обезвреживание ловушек
HASTY TRAPBREAKING | Поспешное обезвреживание
METHODICAL TRAPBREAKING | Методичное обезвреживание
Using Trapbreaking | С Обезвреживанием ловушек
Trap disarmed or discharged | Ловушка обезврежена или разряжена
Trap not disarmed, cannot repeat | Не обезврежена; повторять нельзя
Trap not disarmed, try again | Не обезврежена; можно повторить
Botched Throw (2-3) | Грубая ошибка (2–3)
Trap triggered | Ловушка сработала
SPELUNKING | Преодоление пещерных препятствий
CLIMB (EASY) | Лазание (лёгкое препятствие)
CLIMB (SHEER SURFACE) | Лазание (отвесная поверхность)
RAPPEL | Спуск по верёвке
Movement Type | Вид движения
Ascend/descend | Подъём/спуск
Descend only | Только спуск
One throw per 100’ | Один бросок на 100 футов
Using Climbing/Mountaineering | С Лазанием/Альпинизмом
Climb @ 1/3 Combat Speed | Лазание с 1/3 боевой скорости
Rappel @ Run Speed | Спуск со скоростью бега
No progress for 1 round | Нет продвижения 1 раунд
Fall unless double proficient with<br>mountaineering gear | Падение, если нет обоих навыков<br>и альпинистского снаряжения
Rappel @ Combat Speed | Спуск с боевой скоростью
Fall | Падение
Vulnerable in Combat | Уязвимый в бою
No | Нет
Yes | Да
CRAWLING TRAVERSE | Прорывание ползком
BALANCING TRAVERSE<br>(NARROW) | Прорывание с балансированием<br>(узкий путь)
BALANCING TRAVERSE<br>(PRECARIOUS) | Прорывание с балансированием<br>(ненадёжный путь)
Horizontal only | Только по горизонтали
Traverse @ 1/3 Combat Speed | Прорывание с 1/3 боевой скорости
No progress 1 one round | Нет продвижения 1 раунд
Fall unless proficient in both<br>Climbing and Cat Burglary | Падение без обоих навыков:<br>Лазания и Кошачьей грации
Fall unless double proficient<br>(mountaineering gear implied) | Падение без обоих навыков<br>(подразумевается альпинистское снаряжение)
PROFICIENCY | Навык
EFFECT ON DEX | Влияние на ЛОВ
VERTICAL LEAP | Прыжок в высоту
HORIZONTAL JUMP | Прыжок в длину
Adventuring | Авантюризм
DEX Bonus + 1 | Бонус ЛОВ + 1
DEX + 1d6 – encumbrance | ЛОВ + 1d6 – нагрузка
Increase by class level, max 24 | Увеличить на уровень класса, максимум 24
SPEED MULTIPLIER | Множитель скорости
Grassland, scrubland | Поля, саванна
Barrens, desert, hills, forest | Степь, пустыня, холмы, лес
Jungle, mountain, swamp | Джунгли, горы, болото
Road | Дорога
×3/2 (×2 for drivers) | ×3/2 (×2 с Возничим)
Mud/Snow | Грязь/снег
EXPLORATION SPEED<br>(FEET PER TURN) | Скорость исследования<br>(футов за ход)
EXPEDITION SPEED<br>(MILES PER DAY) | Экспедиционная скорость<br>(миль в день)
EXPEDITION SPEED<br>(HEXES PER DAY) | Экспедиционная скорость<br>(гексов в день)
EXPEDITION SPEED<br>(MILES PER HOUR) | Экспедиционная скорость<br>(миль в час)
FEATURE PERCEIVED | Наблюдаемый объект
DAYLIGHT | Дневной свет
FULL MOONLIGHT | Полная луна
HALF MOONLIGHT | Половина луны
STARLIGHT | Свет звёзд
Terrain\* | Местность\*
Fire\* | Огонь\*
Humanoid (1 - 9) | Гуманоиды (1–9)
Party/Gang (10 - 30) | Группа/шайка (10–30)
Platoon (31 - 60) | Взвод (31–60)
Company (61 - 240) | Рота (61–240)
Battalion (241+) | Батальон (241+)
EXPEDITION MOVEMENT | Экспедиционное перемещение
11 miles or less | 11 миль или меньше
192 miles or more | 192 мили или больше
NAVIGATION | Навигация
Barrens (any) | Степь (любая)
Desert (any) | Пустыня (любая)
Forest (any) | Лес (любой)
Grassland (any) | Поля (любые)
Hills (any) | Холмы (любые)
Jungle (any) | Джунгли (любые)
Mountains (any) | Горы (любые)
Scrubland (low, sparse) | Саванна (низкая, редкая)
Scrubland (high, dense) | Саванна (высокая, густая)
Swamp (marshy, scrubby) | Болото (топкое, кустарниковое)
Swamp (forested) | Болото (лесистое)
DAILY FOOD | Пища в день
DAILY<br>WATER | Вода<br>в день
Dog, hunting | Собака, охотничья
Dog, war | Собака, боевая
TERRAIN TYPE | Тип местности
MAX (AVERAGE)<br>ENCOUNTER DISTANCE | Максимальная (средняя)<br>дистанция столкновения
Desert (rocky) | Пустыня (каменистая)
Desert (sandy) | Пустыня (песчаная)
Forest (deciduous) | Лес (лиственный)
Forest (taiga) | Лес (тайга)
Grassland (other) | Поля (прочие)
Grassland (steppe) | Поля (степные)
Hills (forested) | Холмы (лесистые)
Hills (rocky/terraced) | Холмы (каменистые/террасированные)
Mountains (forested) | Горы (лесистые)
Mountains (rocky/snowy/terraced) | Горы (каменистые/снежные/террасированные)
Swamp (marshy) | Болото (топкое)
Swamp (scrubby) | Болото (кустарниковое)
ADVENTURERS | Искатели приключений
MONSTERS | Монстры
FORE, LOS | ПС, ЛВ
FORE | ПС
LOS | ЛВ
NONE | Нет
Surprised | Ошарашен
Attentive | Внимателен
PARTY SIZE | Численность группы
Hills (rocky) | Холмы (каменистые)
Mountains (rocky) | Горы (каменистые)
Scrubland (sparse) | Саванна (редкая)
Scrubland (dense) | Саванна (густая)
Hostile, attacks | Враждебная, атакует
Unfriendly, may attack | Недружелюбная, может атаковать
Neutral, uncertain | Нейтральная, не определился
Indifferent, uninterested | Безразличная, не заинтересован
Friendly, helpful | Дружелюбная, помогает
NUMBER OF ATTEMPTS | Число попыток
TIME REQUIRED | Требуемое время
1st Attempt to Influence | 1-я попытка влияния
2nd Attempt to Influence | 2-я попытка влияния
3rd Attempt to Influence | 3-я попытка влияния
4th Attempt to Influence | 4-я попытка влияния
5th+ Attempts to Influence | 5-я и последующие попытки влияния
1 round (1 minute) | 1 раунд (1 минута)
1 turn (10 minutes) | 1 ход (10 минут)
6 turns (1 hour) | 6 ходов (1 час)
8 hours (1 work-day) | 8 часов (1 рабочий день)
5 work-days (1 week) | 5 рабочих дней (1 неделя)
REACTION<br>ROLL | Бросок<br>реакции
INITIAL INTERACTION | Первое взаимодействие
ATTEMPT TO INFLUENCE | Попытка влияния
Shift 2 attitudes towards Hostile | Сдвиг на 2 ступени к враждебной
Shift 1 attitude towards Hostile | Сдвиг на 1 ступень к враждебной
Shift 1 attitude towards Neutral | Сдвиг на 1 ступень к нейтральной
Shift 1 attitude towards Friendly | Сдвиг на 1 ступень к дружелюбной
Shift 2 attitudes towards Friendly | Сдвиг на 2 ступени к дружелюбной
CHARACTER<br>PROFICIENT? | Есть навык<br>у персонажа?
+1 BONUS | Бонус +1
+2 BONUS | Бонус +2
+3 BONUS | Бонус +3
Proficient | С навыком
Non-Proficient | Без навыка
1 day | 1 день
1 week | 1 неделя
1 month | 1 месяц
1 year | 1 год
ENGAGING CREATURE SIZE | Размер связывающего боем существа
SMALL<br>OPPONENT | Малый<br>противник
MAN-SIZED<br>OPPONENT | Противник<br>размером с человека
LARGE<br>OPPONENT | Большой<br>противник
HUGE<br>OPPONENT | Огромный<br>противник
GIGANTIC<br>OPPONENT | Гигантский<br>противник
COLOSSAL<br>OPPONENT | Колоссальный<br>противник
MONSTER HD | КЗ монстра
FIGHTER LEVEL | Уровень воина
CRUSADER/THIEF LEVEL | Уровень крестоносца/вора
MAGE LEVEL | Уровень мага
ATTACK THROW VALUE | Целевое значение броска атаки
1/2 or less | 1/2 или меньше
WEAPON | Оружие
SHORT<br/>RANGE | Ближняя<br>дистанция
MEDIUM<br/>RANGE | Средняя<br>дистанция
LONG<br/>RANGE | Дальняя<br>дистанция
Axe (thrown) | Топор (метательный)
Bow, Composite | Лук, составной
Bow, Long | Лук, длинный
Bow, Short | Лук, короткий
Dagger (thrown) | Кинжал (метательный)
Dart | Метательная стрелка
Holy water | Святая вода
Knife (thrown) | Нож (метательный)
Oil (thrown) | Масло (метаемое)
Sling-Staff | Праща-посох
Warhammer (thrown) | Боевой молот (метательный)
SPELLS | Заклинания
Frightened Retreat | Отступление в страхе
Morale Faltering | Боевой дух колеблется
Fight On | Продолжать бой
Advance and Pursue | Наступать и преследовать
Victory or Death | Победа или смерть
MOUNT MOVED | Животное двигалось
MOUNT STATIONARY | Животное неподвижно
MOUNT CHARGED | Животное совершило натиск
**Rider** | **Всадник**
Can attack if passenger<br>and mount don’t | Может атаковать, если пассажир<br>и животное не атакуют
Can attack if mount doesn’t | Может атаковать, если животное не атакует
Can attack | Может атаковать
**Passenger** | **Пассажир**
Can attack if rider and mount don’t | Может атаковать, если всадник и животное не атакуют
**Mount** | **Ездовое животное**
Can attack if rider and passenger don’t | Может атаковать, если всадник и пассажир не атакуют
Can attack if rider and passenger don’t;<br>Can move after rider’s missile attack | Может атаковать, если всадник и пассажир не атакуют;<br>может двигаться после дальнобойной атаки всадника
Can usually attack if war-trained | Обычно может атаковать, если обучено войне
VEHICLE DIDN’T CHARGE | Транспорт не совершал натиск
VEHICLE CHARGED | Транспорт совершил натиск
**Driver** | **Возница**
Cannot attack | Не может атаковать
Can melee attack | Может атаковать в ближнем бою
**Transporters** | **Носители**
Can attack if carrying vehicle on back | Может атаковать, если несёт транспорт на спине
Can melee attack if carrying on back or pulling vehicle | Может атаковать в ближнем бою, если несёт на спине или тянет транспорт
BASE XP | Базовый Опыт
BONUS XP/ABILITY | Бонус Опыта за способность
Less than 1 | Меньше 1
'''
def dictionary(s):return dict(line.split(' | ',1) for line in s.strip().splitlines())
labels=dictionary(HEADINGS);labels.update(dictionary(CELLS))
labels['Lead Glass Window (24” × 46” x.25” and 25lbs or less)']='Окно со свинцовым переплётом (24” × 46” × .25”, 25 фунтов или меньше)'
doors={'Iron-banded Stone Door':'Окованная железом каменная дверь','Solid Iron Door':'Цельная железная дверь','Iron Trap Door':'Железный люк','Iron-Banded Wooden Door':'Окованная железом деревянная дверь','Wooden Door,':'Деревянная дверь,','Lead Glass Window':'Окно со свинцовым переплётом'}
def tr(en):
    if en in labels:return labels[en]
    s=en
    for a,b in doors.items():s=s.replace(a,b)
    s=s.replace('lbs',' фунтов').replace('or less','или меньше').replace(' and ',' и ')
    s=re.sub(r'(?<![A-Za-z])st(?![A-Za-z])','ст.',s)
    s=re.sub(r'(\d+(?:\.\d+)?) miles?',lambda m:m[1]+(' миля' if m[1]=='1' else ' мили' if m[1] in ('1.5','3','4') else ' миль'),s)
    s=re.sub(r'^Up to (\d+’)$',r'До \1',s)
    s=re.sub(r'^…to (\d+’)$',r'…до \1',s)
    s=re.sub(r'^(\d+) to (\d+)$',r'\1–\2',s)
    s=re.sub(r'^(\d+) creatures?$',lambda m:m[1]+(' существо' if m[1]=='1' else ' существа'),s)
    s=s.replace('NA /','Не слышно /')
    if en.startswith(('Monsters ','Adventurers ')):
        s=en
        for a,b in [('Monsters not surprised','Монстры не Ошарашены'),('Adventurers not surprised','Искатели приключений не Ошарашены'),('Monsters roll surprise','Монстры бросают внезапность'),('Adventurers rolls surprise','Искатели приключений бросают внезапность'),('Adventurers roll surprise','Искатели приключений бросают внезапность'),('Adventurers cannot evade','Искатели приключений не могут избежать столкновения'),('Adventurers can always evade','Искатели приключений всегда могут избежать столкновения'),('Adventurers can evade','Искатели приключений могут избежать столкновения')]:s=s.replace(a,b)
    if en=='No encounter':s='Нет столкновения'
    # Remaining letters from HTML tags, dice, or units are not untranslated words.
    test=re.sub(r'<[^>]*>|\d+d\d+','',s)
    if re.search('[A-Za-z]',test):return None
    return s
values=read('automatic_labels.json');missing=[]
for u in read('source_units.json'):
    if not u['table_id'] and u['kind']!='heading':continue
    en=u['source_markup'];ru=tr(en)
    if ru is not None:values[u['id']]=ru
    if u['id'] not in values:missing.append(u['id']+' | '+en)
write('labels.json',values)
write('label_map.json',labels)
(HERE/'labels_remaining.txt').write_text('\n'.join(missing),'utf-8')
print('labels',len(values),'missing',len(missing));print('\n'.join(missing))
