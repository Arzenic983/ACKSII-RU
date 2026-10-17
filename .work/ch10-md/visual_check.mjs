import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1800},deviceScaleFactor:1});
const metrics=[];
for(const p of [450,455,457,458,461]) {
  await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
  await page.screenshot({path:path.join(here,`visual-${p}.png`)});
  if([455,457,458].includes(p)) await page.locator('table').last().screenshot({path:path.join(here,`visual-table-${p}.png`)});
  metrics.push({pdf_page:p,...await page.evaluate(()=>({scroll_width:document.documentElement.scrollWidth,viewport:innerWidth,tables:[...document.querySelectorAll('table')].map(t=>({id:t.id,width:t.getBoundingClientRect().width,scroll_width:t.scrollWidth}))}))});
}
await browser.close();
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log(JSON.stringify(metrics));
