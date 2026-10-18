from pathlib import Path
import importlib.util,re,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reader',ROOT/'tools/build_rr_reader.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
md=b.HUMAN.read_text('utf-8')
css=(HERE/'reader_preview.html').read_text('utf-8').split('<style>',1)[1].split('</style>',1)[0]
for p in (5,205,296,320,480,520,545,550):
    body=md.split(f'<p align="right" id="pdf-page-{p:04}">',1)[1]
    body=body.split('<p align="right" id="pdf-page-',1)[0]
    (HERE/f'sample-{p}.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><base href="../../ACKSII/Перевод%20Markdown/"><style>'+css+'</style><body><h1>PDF '+str(p)+'</h1><p align="right" id="pdf-page-'+f'{p:04}'+ '">'+b.render(body)+'</body></html>','utf-8')
