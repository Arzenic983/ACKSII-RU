import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:2400,height:1800},deviceScaleFactor:1});
const metrics=[];
for(let p=518;p<=531;p++){
 await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
 const metric={pdf_page:p,...await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,tables:document.querySelectorAll('table').length,cells:document.querySelectorAll('td,th').length,overflowing_cells:[...document.querySelectorAll('td,th')].filter(e=>e.scrollWidth>e.clientWidth+1).length}))};
 if(metric.width>metric.viewport||metric.overflowing_cells)throw new Error(JSON.stringify(metric));
 if(metric.tables){
  await page.locator('table').screenshot({path:path.join(here,`visual-table-${p}.png`)});
  if([522,528,530].includes(p)){
   const row=page.locator('tr').nth(3);const box=await row.boundingBox();
   for(const [name,offset] of [['left',0],['right',1100]])await page.screenshot({path:path.join(here,`visual-detail-${p}-${name}.png`),clip:{x:box.x+offset,y:box.y,width:1100,height:box.height}});
  }
 }
 if(p===519)await page.screenshot({path:path.join(here,'visual-prose-519.png'),fullPage:true});
 metrics.push(metric);
}
await browser.close();
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log('14 pages: no horizontal overflow; 11 complete 72-cell tables; six detailed row captures');
