import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1500},deviceScaleFactor:1});
const metrics=[];
for(let p=538;p<=550;p++){
 await page.goto(pathToFileURL(path.join(here,`preview-${p}.html`)).href);
 const m={pdf_page:p,...await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,index_entries:document.querySelectorAll('.index-block p:has(a)').length,index_links:document.querySelectorAll('.index-block a').length,overflowing_blocks:[...document.querySelectorAll('.index-block,.backer-list')].filter(e=>e.scrollWidth>e.clientWidth+1).length}))};
 if(m.width>m.viewport||m.overflowing_blocks)throw new Error(JSON.stringify(m));
 await page.screenshot({path:path.join(here,`visual-top-${p}.png`)});
 if(p===546){
  const el=page.locator('.index-block p').filter({hasText:'Magical Research, Major'}).first();
  const y=await el.evaluate(e=>e.getBoundingClientRect().top+scrollY);await page.evaluate(y=>scrollTo(0,y-50),y);
  await page.screenshot({path:path.join(here,'visual-research-546.png')});
 }
 if(p===548){
  const el=page.locator('h3').filter({hasText:'Указатель обратных заклинаний'});await el.scrollIntoViewIfNeeded();
  const y=await el.evaluate(e=>e.getBoundingClientRect().top+scrollY);await page.evaluate(y=>scrollTo(0,y-30),y);
  await page.screenshot({path:path.join(here,'visual-reversed-548.png')});
 }
 if(p===550){await page.evaluate(()=>scrollTo(0,document.body.scrollHeight));await page.screenshot({path:path.join(here,'visual-end-550.png')});}
 metrics.push(m);
}
await browser.close();
if(metrics.reduce((n,m)=>n+m.index_entries,0)!==862||metrics.reduce((n,m)=>n+m.index_links,0)!==975)throw new Error('Missing entries or links');
fs.writeFileSync(path.join(here,'visual_metrics.json'),JSON.stringify(metrics,null,2)+'\n');
console.log('13 pages; 862 entries; 975 links; no horizontal overflow');
