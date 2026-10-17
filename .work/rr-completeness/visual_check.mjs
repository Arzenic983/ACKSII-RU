import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1800},deviceScaleFactor:1});
const metrics=[];
for(const p of [5,205,296,320,480,520,545,550]){
  await page.goto(pathToFileURL(path.join(here,`sample-${p}.html`)).href);
  await page.screenshot({path:path.join(here,`sample-${p}.png`)});
  if(p===520)await page.locator('table').first().screenshot({path:path.join(here,'sample-table-520.png')});
  if(p===480)await page.locator('[role="img"]').screenshot({path:path.join(here,'sample-scheme-480.png')});
  metrics.push({pdf_page:p,...await page.evaluate(()=>({scroll_width:document.documentElement.scrollWidth,viewport:innerWidth,unavailable_images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),tables:[...document.querySelectorAll('table')].map(t=>({width:t.getBoundingClientRect().width,scroll_width:t.scrollWidth})),clipped_cells:[...document.querySelectorAll('td,th')].filter(t=>t.scrollWidth>t.clientWidth+2).length}))});
}
await browser.close();
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log(JSON.stringify(metrics));
