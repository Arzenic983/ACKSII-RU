import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1800},deviceScaleFactor:1});
const metrics=[];
for(const p of [491,492,496,498,505,506,507]){
 await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
 await page.screenshot({path:path.join(here,`visual-${p}.png`),fullPage:true});
 for(const [i,t] of (await page.locator('table').all()).entries())await t.screenshot({path:path.join(here,`visual-table-${p}-${i+1}.png`)});
 if(p===507)for(const [i,t] of (await page.locator('.language-tree').all()).entries())await t.screenshot({path:path.join(here,`visual-tree-${i+1}.png`)});
 const metric={pdf_page:p,...await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,broken_images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,trees:[...document.querySelectorAll('.language-tree')].map(t=>[...t.children].map(n=>Number(n.dataset.depth)))}))};
 metrics.push(metric);
 if(metric.width>metric.viewport||metric.broken_images)throw new Error(JSON.stringify(metric));
}
await browser.close();
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log('Seven samples: no horizontal overflow or broken images');
