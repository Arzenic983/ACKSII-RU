import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1600},deviceScaleFactor:1});
const metrics=[];
for(let p=532;p<=537;p++){
 await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
 const metric={pdf_page:p,...await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,tables:document.querySelectorAll('table').length,cells:document.querySelectorAll('td,th').length,empty_cells:[...document.querySelectorAll('td')].filter(e=>!e.textContent.trim()).length,overflowing_cells:[...document.querySelectorAll('td,th')].filter(e=>e.scrollWidth>e.clientWidth+1).length}))};
 if(metric.width>metric.viewport||metric.overflowing_cells)throw new Error(JSON.stringify(metric));
 for(const table of await page.locator('table').all()){
  const tid=await table.getAttribute('id');await table.screenshot({path:path.join(here,`visual-${tid}.png`)});
 }
 await page.screenshot({path:path.join(here,`visual-page-${p}.png`),fullPage:true});
 metrics.push(metric);
}
await browser.close();
if(metrics.reduce((n,m)=>n+m.tables,0)!==6||metrics.reduce((n,m)=>n+m.empty_cells,0)!==17)throw new Error('Missing tables or blanks');
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log('Six pages and tables, 17 blanks; no horizontal overflow');
