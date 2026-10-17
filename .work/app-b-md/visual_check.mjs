import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1800},deviceScaleFactor:1});
const samples={'510':['rr.p0510.b028','rr.p0510.b033'],'511':['rr.p0511.b023'],'515':['rr.p0515.b010','rr.p0515.b014','rr.p0515.b018'],'516':['rr.p0516.b028','rr.p0516.b033','rr.p0516.b042','rr.p0516.b043'],'517':['rr.p0517.b008']};
const metrics=[];
for(let p=508;p<518;p++){
 await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
 for(const uid of samples[p]||[]){
  const item=page.locator(`[data-unit="${uid}"]`);if(await item.count()!==1)throw new Error(`Missing paragraph ${uid}`);
  await item.screenshot({path:path.join(here,`visual-${uid}.png`)});
 }
 const metric={pdf_page:p,...await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,tagged_paragraphs:document.querySelectorAll('[data-unit]').length}))};
 metrics.push(metric);if(metric.width>metric.viewport)throw new Error(JSON.stringify(metric));
}
await browser.close();
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log('Ten pages without horizontal overflow; 11 paragraph screenshots');
