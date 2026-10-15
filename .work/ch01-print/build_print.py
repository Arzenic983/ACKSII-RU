"""Russian Chapter 1 overlay on untouched original vector/raster artwork."""
import pathlib, sqlite3, json, re, html, io, collections, hashlib, sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, BooleanObject, DictionaryObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import CMYKColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import Paragraph

sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'ACKSII/Образцы для типографии'
OUT.mkdir(exist_ok=True)
FINAL=OUT/'ACKSII Глава 1 — образец вёрстки.pdf'
SOURCE=ROOT/'ACKSII/Source/ACKSII Revised Rulebook.pdf'
DB=ROOT/'ACKSII/База перевода/acksii_translation.sqlite'
BASELINE=WORK/'protected_hashes.json'
if not BASELINE.exists():
    protected=[p for p in (ROOT/'ACKSII').rglob('*') if p.is_file() and OUT not in p.parents]
    BASELINE.write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},ensure_ascii=False,indent=2),encoding='utf8')

font_paths={'TNR':'times.ttf','TNR-B':'timesbd.ttf','TNR-I':'timesi.ttf','TNR-BI':'timesbi.ttf'}
for name,file in font_paths.items():pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNR-B',italic='TNR-I',boldItalic='TNR-BI')
BLACK=CMYKColor(0,0,0,1)
WHITE=CMYKColor(0,0,0,0)
RED=CMYKColor(.4,1,.57,.49)
SHADE=CMYKColor(.02,.05,.029,.025)
db=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
units=[dict(r) for r in db.execute('select u.*,t.text_ru as russian from units u join translations t on t.unit_id=u.id where u.chapter_id="01" order by pdf_page,block_order,row_index,column_index')]
assert len(units)==358
by_id={u['id']:u for u in units}
geo=json.loads((WORK/'chapter_geometry.json').read_text(encoding='utf8'))
layout=json.loads((WORK/'unit_layout.json').read_text(encoding='utf8'))
tables=[t for t in json.loads((ROOT/'.work/revised-rulebook-extraction/tables.json').read_text(encoding='utf8')) if 14<=t['page']<=23]

backdrop=WORK/'original_art_without_english.pdf'
removed=0
strip_info=WORK/'stripping.json'
if not backdrop.exists() or json.loads(strip_info.read_text(encoding='utf8')).get('version')!=2:
    reader=PdfReader(SOURCE);writer=PdfWriter()
    for i in range(13,23):
        page=writer.add_page(reader.pages[i]);page.pop('/Annots',None)
    visited=set();underlines_removed=0
    def strip_stream(container,resource,form=False):
        global removed,underlines_removed
        identity=id(container)
        if identity in visited:return
        visited.add(identity)
        resource=resource.get_object() if resource else {}
        fonts=resource.get('/Font',{})
        current='';kept=[];stroke=None;line_width=1;stack=[];path=[]
        stream=ContentStream(container if form else container.get_contents(),writer)
        for args,op in stream.operations:
            if op==b'q':stack.append((stroke,line_width))
            elif op==b'Q' and stack:stroke,line_width=stack.pop()
            elif op in (b'K',b'G',b'RG'):stroke=tuple(float(a) for a in args)
            elif op==b'w':line_width=float(args[0])
            if op in (b'm',b'l',b'c',b're',b'h'):path.append((len(kept),op,list(args)))
            if op==b'S' and len(path)==2 and path[0][1]==b'm' and path[1][1]==b'l' and stroke in [(0,0,0,1),(0,),(0,0,0)] and line_width<.6:
                a,b=path[0][2],path[1][2]
                if abs(float(a[1])-float(b[1]))<.01 and 2<abs(float(a[0])-float(b[0]))<160:
                    for index,_,_ in reversed(path):kept.pop(index)
                    path=[];underlines_removed+=1;continue
            if op in (b'S',b's',b'f',b'f*',b'B',b'B*',b'n'):path=[]
            if op==b'Tf':
                f=fonts.get(args[0]);current=str(f.get_object().get('/BaseFont','')) if f else ''
            if op in (b'Tj',b'TJ',b"'",b'"') and not any(s in current for s in ['Constantine','FoundryJournal']):
                removed+=1
                continue
            kept.append((args,op))
        stream.operations=kept
        if form:container.set_data(stream.get_data())
        else:container[NameObject('/Contents')]=stream
        for ref in resource.get('/XObject',{}).values():
            ob=ref.get_object()
            if ob.get('/Subtype')=='/Form':strip_stream(ob,ob.get('/Resources',resource),True)
    for page in writer.pages:strip_stream(page,page.get('/Resources'))
    with backdrop.open('wb') as f:writer.write(f)
    strip_info.write_text(json.dumps({'version':2,'text_show_operations_removed':removed,'english_underlines_removed':underlines_removed}),encoding='utf8')

def xml_text(s):
    s=s.replace('<br>','\n')
    s=re.sub(r'</?(?:strong|em)>','',s)
    s=html.escape(s,quote=False)
    s=re.sub(r'\*\*\*(.+?)\*\*\*',r'<b><i>\1</i></b>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',s)
    s=s.replace('\n','<br/>').replace('\\*','*')
    # Bind a sign to its number and short Russian prepositions to the next word.
    s=re.sub(r'(?<=\s)-(?=\d)', '−',s)
    s=re.sub(r'\b([А-Яа-яЁё]{1,2})\s+(?=[А-Яа-яЁё])',r'\1&#160;',s)
    return s

special_heads={
 'rr.p0015.b002':'СОЗДАНИЕ<br/>ПЕРСОНАЖА',
 'rr.p0016.b001':'АТРИБУТЫ<br/>ПЕРСОНАЖА',
 'rr.p0017.b001':'БОЕВЫЕ<br/>ХАРАКТЕРИСТИКИ',
 'rr.p0019.b015':'СКОРОСТЬ И<br/>НАГРУЗКА',
 'rr.p0023.b001':'ГРУППЫ ИСКАТЕЛЕЙ<br/>ПРИКЛЮЧЕНИЙ',
 'rr.p0015.b015':'ОПЦИОНАЛЬНЫЕ ПРАВИЛА<br/>СОЗДАНИЯ ПЕРСОНАЖЕЙ',
 'rr.p0018.b005':'ОПЦИОНАЛЬНЫЕ ПРАВИЛА<br/>ОЧКОВ ЗДОРОВЬЯ',
}
stats=[]
def make_para(text,size,heading=False,align=TA_JUSTIFY,leading=None):
    sty=ParagraphStyle('s',fontName='TNR-B' if heading else 'TNR',fontSize=size,
        leading=leading or size*10/9,textColor=RED if heading else BLACK,
        alignment=align,allowWidows=1,allowOrphans=1,splitLongWords=0,
        embeddedHyphenation=0,hyphenationLang=None,spaceBefore=0,spaceAfter=0,
        uriWasteReduce=0,borderPadding=0)
    return Paragraph(text,sty)

buffer=io.BytesIO();cv=canvas.Canvas(buffer,pagesize=(612,792),pageCompression=1,pdfVersion=(1,7))
cv.setTitle('ACKS II — Персонажи — образец русской вёрстки')
cv.setAuthor('Русский перевод ACKS II')

def draw_fit(uid,text,boxes,base=9,heading=False,alignment=TA_JUSTIFY,hscale=1,leading=None):
    # boxes are original top-down coordinates; no text is clipped or dropped.
    for step in range(37):
        size=base-step*.1
        if size<6.5:raise RuntimeError(f'Cannot fit {uid}: {base}, {boxes}')
        para=make_para(text,size,heading,alignment,leading=(leading*size/base if leading else None))
        pending=[para];placed=[]
        for x0,y0,x1,y1 in boxes:
            if not pending:break
            p=pending.pop(0);w=(x1-x0)/hscale;available=y1-y0
            pw,ph=p.wrap(w,10000)
            if ph<=available+.01:placed.append((p,[x0,y0,x1,y1],ph));continue
            parts=p.split(w,available)
            if not parts:
                pending.insert(0,p)
                break
            first=parts[0];first.wrap(w,available)
            placed.append((first,[x0,y0,x1,y1],first.height));pending=parts[1:]+pending
        if pending or len(placed)==0:continue
        # splitLongWords is disabled; require every line to stay inside the box.
        for p,box,ph in placed:
            if p.minWidth()*hscale>box[2]-box[0]+.1:break
        else:break
    else:raise RuntimeError('No fit '+uid)
    for p,box,ph in placed:
        x0,y0,x1,y1=box;cv.saveState();cv.translate(x0,792-y0);cv.scale(hscale,1)
        p.drawOn(cv,0,-ph);cv.restoreState()
    stats.append({'unit_id':uid,'font_size':round(size,2),'horizontal_scale':hscale,'boxes':boxes,'height':sum(q[2] for q in placed),'parts':len(placed),'text':Paragraph(text,ParagraphStyle('plain')).getPlainText()})

def draw_flow(ids,boxes):
    # Paragraphs in a shared original text frame share the same point size.
    # Redistributing paragraph space avoids tiny individual blocks in Russian.
    for step in range(25):
        size=9-step*.05;leading=size*1.07;placed=[];bi=0;y=boxes[0][1];failed=False
        for uid in ids:
            u=by_id[uid];bullet=u['russian'].startswith('♦')
            text=xml_text(u['russian'][1:].strip() if bullet else u['russian'])
            st=ParagraphStyle('flow',fontName='TNR',fontSize=size,leading=leading,
                textColor=BLACK,alignment=TA_JUSTIFY,splitLongWords=0,
                allowWidows=1,allowOrphans=1,leftIndent=18 if bullet else 0,
                rightIndent=9 if bullet or u['kind']=='list_item' else 0,
                bulletFontName='TNR',bulletFontSize=8,bulletColor=RED,bulletIndent=0)
            pending=[Paragraph(text,st,bulletText='♦' if bullet else None)]
            pieces=[]
            while pending:
                if bi>=len(boxes):failed=True;break
                x0,_,x1,y1=boxes[bi];p=pending.pop(0);w=x1-x0
                _,ph=p.wrap(w,10000);available=y1-y
                if ph<=available+.01:
                    if p.minWidth()>w+.01:failed=True;break
                    pieces.append((p,[x0,y,x1,y+ph],ph));y+=ph
                else:
                    parts=p.split(w,available)
                    if parts:
                        first=parts[0];first.wrap(w,available)
                        pieces.append((first,[x0,y,x1,y+first.height],first.height));pending=parts[1:]+pending
                    else:pending.insert(0,p)
                    bi+=1
                    if bi<len(boxes):y=boxes[bi][1]
            if failed:break
            placed.append((uid,text,pieces));y+=2 if bullet else 5
        if not failed:break
    else:raise RuntimeError('Flow does not fit '+str(ids))
    for uid,text,pieces in placed:
        for p,box,ph in pieces:p.drawOn(cv,box[0],792-box[1]-ph)
        stats.append({'unit_id':uid,'font_size':round(size,2),'horizontal_scale':1,'boxes':[p[1] for p in pieces],'height':sum(p[2] for p in pieces),'parts':len(pieces),'text':Paragraph(text,ParagraphStyle('plain')).getPlainText()})

flow_groups={
 15:[([3,4,5,6,7,8,9,10,11],[[72,171.7,310.5,738]]),([12,13,14],[[328.5,127.7,567,393]])],
 16:[([2,3],[[45,120.7,283.5,235]]),([6,7,8,9],[[45,437.7,283.5,736]])],
 17:[([8,9,10,11,12,13],[[72,327.7,310.5,572]]),([15,16,17,18,19,20],[[72,587.7,310.5,741]])],
 18:[([2,3,4],[[301.5,100.7,540,384]])],
 19:[([5,6],[[72,317.7,310.5,474]]),([8,9,10,11,12,13],[[72,497.7,310.5,680]])],
 20:[([14,15],[[301.5,460.7,540,650]])],
 21:[([3,4,5],[[72,260.7,310.5,410],[328.5,77.7,567,115]])],
 22:[([6,7,8,9,10,11],[[301.5,180.7,540,729]])],
 23:[([4,5,6,7,8],[[72,300.7,310.5,741]]),([9,10,11,12],[[328.5,77.7,567,370]])],
}

def cell(u,t):
    r,c=u['row_index'],u['column_index'];xs,ys=t['xs'],t['ys']
    x0,x1=xs[c],xs[c+u['colspan']];y0,y1=ys[r],ys[r+u['rowspan']]
    if u['pdf_page']==22:
        ys=[89.92,115.72,131.22,156.0];y0,y1=ys[r],ys[r+u['rowspan']]
    chars=[ch for ch in next(p for p in geo if p['page']==u['pdf_page'])['chars']
      if x0-.3<=(ch['x0']+ch['x1'])/2<=x1+.3 and t['ys'][r]-.3<=(ch['top']+ch['bottom'])/2<=t['ys'][r+u['rowspan']]+.3]
    header_rows=2 if u['pdf_page']==16 else 1
    white=r<header_rows
    bold=white or (u['pdf_page']==22 and c==0)
    font='TNR-B' if bold else 'TNR'
    # Header and body are fitted at a fixed type size, using a modestly condensed
    # Times setting for the long Russian class names in the original narrow cells.
    text=u['russian'].replace('<br>',' ')
    text=re.sub(r'<[^>]*>','',text).replace('**','').replace('*','')
    text=text.replace('длину/высоту','длину / высоту')
    color=WHITE if white else BLACK
    is_age=u['table_id']=='rr.p0021.t01'
    align=TA_LEFT if (is_age and c%2==0) or (u['table_id'] in ['rr.p0020.t01','rr.p0020.t02'] and c==0) or (u['pdf_page']==22 and c==0) else TA_CENTER
    if u['colspan']>1 and white:align=TA_LEFT
    width=x1-x0-6;height=y1-y0-2
    for step in range(30):
        size=9-step*.1
        st=ParagraphStyle('cell',fontName=font,fontSize=size,leading=size*1.03,textColor=color,alignment=align,splitLongWords=0,allowWidows=1,allowOrphans=1)
        para=Paragraph(html.escape(text),st)
        # In single-line body rows use condensed text before reducing point size.
        scale=1
        full=pdfmetrics.stringWidth(text,font,size)
        if height<15 and full>width:scale=max(.8,width/full)
        pw,ph=para.wrap(width/scale,1000)
        if ph<=height+.01 and para.minWidth()*scale<=width+.01:break
    else:raise RuntimeError('Cell cannot fit '+u['id'])
    cv.saveState();cv.translate(x0+3,792-y0-(height-ph)/2-1);cv.scale(scale,1)
    para.drawOn(cv,0,-ph);cv.restoreState()
    stats.append({'unit_id':u['id'],'font_size':round(size,2),'horizontal_scale':round(scale,3),'boxes':[[x0,y0,x1,y1]],'height':ph,'text':text})

for n in range(14,24):
    current=[u for u in units if u['pdf_page']==n]
    if n==14:
        cv.setFillColor(WHITE);cv.setFont('TNR-B',38)
        tx=cv.beginText();tx.setFont('TNR-B',38);tx.setCharSpace(1.5)
        s='ПЕРСОНАЖИ';w=pdfmetrics.stringWidth(s,'TNR-B',38)+1.5*(len(s)-1)
        tx.setTextOrigin((612-w)/2,61);tx.textOut(s);cv.drawText(tx)
        stats.append({'unit_id':current[0]['id'],'text':'1 ПЕРСОНАЖИ','font_size':38,'boxes':[[145,702,467,739]]})
        cv.showPage();continue
    # Original running headers and vertical chapter tabs.
    cv.setFillColor(WHITE);cv.setFont('TNR-B',10)
    if n%2:cv.drawRightString(567,752,'ПЕРСОНАЖИ')
    else:cv.drawString(45,752,'ПЕРСОНАЖИ')
    cv.saveState();cv.translate(598 if n%2 else 11,792-126.3);cv.rotate(-90)
    cv.setFont('TNR-B',6);cv.drawString(0,0,'ПЕРСОНАЖИ');cv.restoreState()
    if n==22:
        # The longer Russian height descriptions need two lines. Use the blank
        # gap below the original table; illustration and main headings stay put.
        xs=[45.5,110.52,189.72,252.36,319.5,389.88,461.88,540.04]
        ys=[89.92,115.72,131.22,156.0]
        for r in range(3):
            cv.setFillColor(RED if r==0 else SHADE if r==2 else WHITE)
            cv.rect(xs[0],792-ys[r+1],xs[-1]-xs[0],ys[r+1]-ys[r],fill=1,stroke=0)
        cv.setStrokeColor(RED);cv.setLineWidth(.6)
        cv.rect(xs[0],792-ys[-1],xs[-1]-xs[0],ys[-1]-ys[0],fill=0,stroke=1)
    flowed=set()
    for numbers,boxes in flow_groups.get(n,[]):
        ids=[f'rr.p{n:04d}.b{k:03d}' for k in numbers]
        draw_flow(ids,boxes);flowed.update(ids)
    for u in current:
        if u['id'] in flowed:continue
        if u['table_id']:
            ti=int(u['table_id'][-2:]);t=next(t for t in tables if t['page']==n and t['table']==ti);cell(u,t);continue
        chunks=layout[u['id']]['chunks'];bb=chunks[0]['bbox'];heading=u['kind']=='heading'
        base=max(c['size'] for ch in chunks for c in ch['chars']) if heading else 9
        text=special_heads.get(u['id'],xml_text(u['russian']).upper() if heading else xml_text(u['russian']))
        boxes=[]
        for ch in chunks:
            box=ch['bbox'];side=ch['side'];x0=72 if n%2 else 45;x0+=256.5*side;x1=x0+238.5
            if u['id']=='rr.p0015.b001':x1=567
            y0=box[1]-(6.5 if heading else 2.5)
            # Respect all fixed headings and give prose its original paragraph
            # space plus a portion of the following inter-paragraph gap.
            following=[a['bbox'][1] for uid,l in layout.items() if uid!=u['id'] and uid.startswith(f'rr.p{n:04d}.') for a in l['chunks'] if a['side']==side and a['bbox'][1]>box[1]+1]
            nexttop=min(following) if following else box[3]+12
            y1=min(nexttop-5,box[3]+9)
            if heading:y1=max(box[3]+2,nexttop-1)
            if u['source_plain'].startswith('EXAMPLE:'):x0+=4.5;x1-=4.5;y1=box[3]+3
            if u['kind']=='list_item':
                if u['russian'].startswith('♦'):
                    cv.setFillColor(RED);cv.setFont('TNR',8);cv.drawString(x0,792-y0-8,'♦')
                    text=xml_text(u['russian'][1:].strip());x0+=18;x1-=9
                else:x1-=9
            boxes.append([x0,y0,x1,y1])
        if u['id']=='rr.p0016.b004':boxes=[[45,237.7,145.7,352.2],[45,357.7,283.5,434]]
        if u['id']=='rr.p0016.b014':boxes=[[301.5,357.7,402.2,432.5],[301.5,437.7,540,476]]
        if u['id']=='rr.p0021.b005':boxes=[[72,367.7,310.5,410],[328.5,77.7,567,115]]
        if heading and base==9:boxes[0][3]=chunks[0]['bbox'][3]+1
        if u['id']=='rr.p0022.b004':boxes[0][3]=242
        hs=.84 if u['id'] in ['rr.p0017.b022','rr.p0022.b005'] else .825 if u['id']=='rr.p0017.b027' else .8 if u['id']=='rr.p0018.b010' else 1
        if u['id'] in ['rr.p0021.b008','rr.p0021.b009','rr.p0021.b010']:
            boxes[0][3]=boxes[0][1]+10.2
            plain=u['russian'][1:].strip()
            hs=(boxes[0][2]-boxes[0][0]-1)/pdfmetrics.stringWidth(plain,'TNR',9)
        draw_fit(u['id'],text,boxes,base=base,heading=heading,alignment=TA_LEFT if heading else TA_JUSTIFY,hscale=hs)
    cv.showPage()
cv.save();buffer.seek(0)
overlay=PdfReader(buffer);base=PdfReader(backdrop);writer=PdfWriter()
writer.pdf_header='%PDF-1.7'
for i,p in enumerate(base.pages):
    p.merge_page(overlay.pages[i],over=True)
    p.pop('/Annots',None)
    # ReportLab emits an unused Helvetica default in its empty text preamble.
    # Remove it so the final file has no unembedded font resources.
    fonts=p['/Resources'].get('/Font',{})
    unused=[k for k,f in fonts.items() if f.get_object().get('/BaseFont')=='/Helvetica']
    if unused:
        content=ContentStream(p.get_contents(),writer)
        content.operations=[(a,o) for a,o in content.operations if not (o==b'Tf' and a[0] in unused)]
        p[NameObject('/Contents')]=content
        for k in unused:del fonts[k]
    writer.add_page(p)
writer.add_metadata({'/Title':'ACKS II — Глава 1: Персонажи — русский образец вёрстки','/Author':'Русский перевод ACKS II','/Subject':'Чистая вёрстка главы 1 с иллюстрациями оригинала. Times New Roman.','/Creator':'ReportLab / pypdf','/Producer':'ACKS II Russian chapter layout'})
writer._root_object[NameObject('/Lang')]=__import__('pypdf').generic.TextStringObject('ru-RU')
writer._root_object[NameObject('/ViewerPreferences')]=DictionaryObject({NameObject('/PrintScaling'):NameObject('/None')})
with FINAL.open('wb') as f:writer.write(f)
manifest={'output':str(FINAL),'pages':10,'physical_source_pages':[14,23],'units':len(units),'fonts':font_paths,'elements':stats,'original_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
(WORK/'layout_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
sizes=collections.Counter(round(s['font_size'],1) for s in stats)
print(json.dumps({'output':str(FINAL),'pages':10,'placed_units':len(stats),'font_sizes':dict(sizes),'size_mb':round(FINAL.stat().st_size/1024**2,2)},ensure_ascii=False))
