"""Extract two existing PDF illustrations; no source or drawing edits."""
from pathlib import Path
from PIL import Image
import subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PDF=ROOT/'ACKSII/Source/ACKSII Revised Rulebook.pdf'
POPPLER='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
OUT=ROOT/'ACKSII/Перевод Markdown/assets'
OUT.mkdir(exist_ok=True)
for page in (491,506):
    temp=HERE/f'pdf-{page}.png'
    if not temp.exists():subprocess.run([POPPLER,'-f',str(page),'-l',str(page),'-singlefile','-r','170','-png',str(PDF),str(temp.with_suffix(''))],check=True)
    image=Image.open(temp)
    scale=image.width/612
    coords=(42,58,578,747) if page==491 else (30,38,583,759)
    image=image.crop(tuple(round(c*scale) for c in coords))
    if page==491:image=image.transpose(Image.Transpose.ROTATE_270)
    image.save(OUT/('appendix-a-map.png' if page==491 else 'appendix-a-siege.png'))
    print(page,image.size)
