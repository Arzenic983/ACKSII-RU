"""Render all ten appendix pages and tag paragraphs for visual inspection."""
from pathlib import Path
import re,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NODE='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
md=(ROOT/'ACKSII/Перевод Markdown/B Состояния.md').read_text('utf-8')
css='body{font:17px Georgia,serif;max-width:1080px;margin:32px auto;padding:0 24px;line-height:1.5}h1,h2,h3,h4{line-height:1.2;margin-bottom:.25em}blockquote{border-left:3px solid #bbb;margin-left:0;padding-left:12px;color:#555;font-size:15px}small{font-size:.75em}'
for p in range(508,518):
    part=md.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
    body=subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=part,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    body=re.sub(r'<p><a id="(rr\.[^"]+)"></a></p>\s*<p>',lambda m:'<p><a id="'+m[1]+'"></a></p>\n<p data-unit="'+m[1]+'">',body)
    (HERE/f'preview-{p}.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><style>'+css+'</style><body>'+body+'</body></html>','utf-8')
print('Rendered 10 page samples')
