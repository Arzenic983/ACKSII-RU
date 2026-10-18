"""Record the completed AI review, its evidence, and visual limits."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
reports={}
for folder in ('p355_360','p361_385','p386_407','p408_427'):
    reports[folder]=json.loads((HERE/'parts'/folder/'review.json').read_text('utf-8'))
independent=[HERE/'parts/p361_385/root_review_339_348.json',HERE/'parts/p386_407/root_review_349_354.json',HERE/'parts/p386_407/independent_review_334_338.json',HERE/'parts/p361_385/independent_review_408_427.json']
assert all(p.exists() for p in independent)
assert not json.loads((HERE/'render_differences.json').read_text('utf-8'))
assert not json.loads((HERE/'mechanics_differences.json').read_text('utf-8'))
texts=json.loads((HERE/'styled.json').read_text('utf-8'))
notes=json.loads((HERE/'notes.json').read_text('utf-8'))
assert len(texts)==4906 and len(notes)==76
root_report={'date':'2026-10-17','pdf_pages':[339,354],'units_translated':1398,'kinds':{'heading':47,'paragraph':170,'list_item':18,'table_cell':1163},'meaning_review':'Английские и русские абзацы, условия и словесные ячейки сопоставлены при переводе; числовые ячейки перенесены без пересчёта и проверены. Неполный DOCX использовался только как черновик; ошибочное автоматическое выравнивание не принималось как готовый перевод.','independent_review':['../p361_385/root_review_339_348.json','../p386_407/root_review_349_354.json'],'applied_findings':['кавалерийское копьё; Зал вождей; Арбитр; Ауранская; Укрытие; Торговый дом; Убежище; Оплот; Порядочный; Коммерческая деятельность; НИП/ПИ','Мор как имя ритуала; штраф -1 вместо снижения на -1','Исходные переносы длинных ячеек348 восстановлены; лишняя фраза цитаты353 удалена','Примечания к 30 000/32 000, перекрытию16 384, двойному maintains и per peasant/family'],'numeric_and_emphasis_differences':0,'source_pdf_images_viewed':[340,341,345,346,353],'human_approved':False}
(HERE/'parts/p339_360/review.json').write_text(json.dumps(root_report,ensure_ascii=False,indent=2)+'\n','utf-8')
visual=sorted({336,338,340,341,345,346,348,349,351,353,358,359,360,370,373,376,377,381,385,386,393,395,403,404,407,412,422,425,426})
review={'date':'2026-10-17','chapter':'08','pdf_pages':[334,427],'units':4906,'complete_semantic_review_by_Codex':True,'human_approved':False,'method':'Первичная сверка всех переводимых текстов и словесных ячеек с английским источником авторами диапазонов; отдельный перенос и машинная сверка числовых таблиц. Условия, ограничения, сроки, ссылки, числа, кости, проценты и знаки модификаторов сохранены.','primary_ranges':[[334,338],[339,354],[355,360],[361,385],[386,407],[408,427]],'independent_review_reports':[str(p.relative_to(HERE)) for p in independent],'independent_scope':'PDF334–338; PDF339–354; все558 словесных единиц PDF408–427. Во втором проходе408–427 172 чисто числовые/кодовые ячейки не пересверялись: их охватывает общий технический контроль. Независимая полная вычитка человеком не выполнялась.','review_findings_resolved':True,'editor_notes':76,'new_terms':'Рабочие, без изменения утверждённого глоссария.','pdf_images_viewed':visual,'pdf_visual_review_scope':'Точечный просмотр перечисленных физических страниц оригинала, таблиц и спорных формул. Все94страницы визуально не вычитывались.','markdown_review':'Независимый HTML-разбор всех4906 отображённых единиц и79таблиц; полная визуальная вычитка русского Markdown не выполнялась.','source_issues':'76 примечаний в notes.json, возле соответствующих мест и в пакете. Значения и формулировки оригинала не заменялись предполагаемыми исправлениями.'}
(HERE/'semantic_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'visual_review.json').write_text(json.dumps({'source_pdf_pages_inspected':visual,'scope':review['pdf_visual_review_scope'],'markdown_visual_review':False},ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'fragment_tools.py').write_text('"""Compatibility entry point for the completed chapter08 builder."""\nfrom build_chapter import rebuild, plain, numbers\n\nif __name__ == "__main__":\n    rebuild()\n','utf-8')
print('Complete AI review recorded; no human approval assigned.')
