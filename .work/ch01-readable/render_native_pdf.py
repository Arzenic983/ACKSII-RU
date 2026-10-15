"""Use packaged render_docx rasterization with a PDF exported by native Word.

Windows has no bundled LibreOffice here. The user explicitly allowed Word.
The original renderer remains unchanged; only its conversion hook is replaced
in memory after the normal renderer's failure has been diagnosed.
"""
import importlib.util
import os
import pathlib
import shutil
import sys

WORK=pathlib.Path(__file__).resolve().parent
SKILL=pathlib.Path('C:/Users/Arsik/.codex/plugins/cache/openai-primary-runtime/documents/26.1011.11113/skills/documents')
NATIVE=pathlib.Path('C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')
os.environ['PATH']=str(NATIVE)+os.pathsep+os.environ.get('PATH','')
spec=importlib.util.spec_from_file_location('render_docx',SKILL/'render_docx.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
docx=WORK.parents[1]/'ACKSII'/'Сборки для чтения'/'ACKSII Введение и глава 1 с пометками.docx'
kind=sys.argv[1] if len(sys.argv)>1 else 'body'
pdf=WORK/'native_render'/('body.pdf' if kind=='body' else 'with_comments.pdf')
assert pdf.is_file()
def native_conversion(doc_path,user_profile,convert_tmp_dir,stem,verbose):
    output=pathlib.Path(convert_tmp_dir)/(stem+'.pdf')
    shutil.copy2(pdf,output)
    return str(output),'Native Word ExportAsFixedFormat used on the separate reading copy.'
m.convert_to_pdf=native_conversion
sys.argv=[str(SKILL/'render_docx.py'),str(docx),'--output_dir',str(WORK/(kind+'_pages')),'--dpi','140']
m.main()
