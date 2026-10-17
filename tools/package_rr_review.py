"""Package the reader Markdown and its existing images for sending to reviewers."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from urllib.parse import unquote
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Для ревью'

def main():
    report=json.loads((BASE/'RR_reading_validation.json').read_text('utf-8'))
    reader=next(r for r in report['outputs'].values() if r['role']=='translator_review')
    md=ROOT/reader['path'];assert hashlib.sha256(md.read_bytes()).hexdigest()==reader['sha256']
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'ACKS II RR — перевод для ревью.zip'
    info='ACKS II Revised Rulebook — перевод для ревью\n\nОткройте файл .md в просмотрщике Markdown. Папка assets с иллюстрациями должна оставаться рядом с ним.\n\nВключены все 12 глав и приложения A–E, 370 таблиц и 751 примечание. Спорные места отмечены звёздочками; английские подписи помогают сверять термины.\n\nВнутренние ссылки указателей работают в самом файле. Ссылки на страницы английского PDF рассчитаны на расположение оригинала в соседней папке Source проекта; сам английский PDF в архив не включён.\n'
    with ZipFile(target,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
        z.write(md,md.name)
        for asset in reader['assets']:
            path=md.parent/unquote(asset);assert path.is_file();z.write(path,unquote(asset))
        z.writestr('Читать сначала.txt',info)
    with ZipFile(target) as z:
        assert z.testzip() is None
        assert z.read(md.name)==md.read_bytes()
        for asset in reader['assets']:assert z.read(unquote(asset))==(md.parent/unquote(asset)).read_bytes()
    result={'date':'2026-10-18','archive':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'reader_sha256':reader['sha256'],'images':reader['assets'],'archive_contents_checked':True}
    (BASE/'RR_review_package.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
