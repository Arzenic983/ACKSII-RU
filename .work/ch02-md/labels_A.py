import pathlib,re,sqlite3
P=pathlib.Path(__file__).resolve().parent
d=sqlite3.connect(P.parents[1]/'ACKSII/База перевода/acksii_translation.sqlite')
names={'Footpad':'Разбойник','Hood':'Бандит','Robber':'Грабитель','Burglar':'Домушник','Rogue':'Плут','Scoundrel':'Прохвост','Pilferer':'Воришка','Master Thief':'Мастер воров','Prince of Thieves':'Князь воров','Arcanist':'Арканист','Seer':'Провидец','Theurgist':'Теург','Magician':'Кудесник','Thaumaturge':'Чудотворец','Enchanter':'Чародей','Sorcerer':'Волшебник','Wizard':'Волшебник','Archmage':'Архимаг','Catechist':'Огласитель','Acolyte':'Послушник','Priest':'Жрец','Curate':'Курат','Vicar':'Викарий','Rector':'Ректор','Prelate':'Прелат','Bishop':'Епископ','Patriarch':'Патриарх','Theocrat':'Теократ'}
out={}
for id,s in d.execute("select id,source_markup from units where chapter_id='02' and pdf_page<=41"):
 if s in names:out[id]=names[s]
 elif re.fullmatch(r'[RD]|\+\d+d',s):out[id]=s
 else:
  m=re.fullmatch(r'(.*), (\d+)(?:th|st|nd|rd) (lvl|level)',s)
  if m and m[1] in names:out[id]=f'{names[m[1]]}, {m[2]}-й '+('ур.' if m[3]=='lvl' else 'уровень')
(P/'labels_A.md').write_text('\n\n'.join(f'<!-- unit: {k} -->\n{v}' for k,v in out.items())+'\n','utf-8')
print('labels',len(out))
