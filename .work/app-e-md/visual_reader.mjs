import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1500},deviceScaleFactor:1});
await page.goto(pathToFileURL(path.join(here,'../reading-md/preview.html')).href);
const metrics=await page.evaluate(()=>({content_width:document.body.clientWidth-parseFloat(getComputedStyle(document.body).paddingLeft)-parseFloat(getComputedStyle(document.body).paddingRight),index_entries:document.querySelectorAll('.index-block p:has(a)').length,index_links:document.querySelectorAll('.index-block a').length,overflowing_blocks:[...document.querySelectorAll('.index-block,.backer-list')].filter(e=>e.scrollWidth>e.clientWidth+1).length}));
if(metrics.content_width!==1080||metrics.index_entries!==862||metrics.index_links!==975||metrics.overflowing_blocks)throw new Error(JSON.stringify(metrics));
const first=page.locator('.index-block a').first();
const target=await first.getAttribute('href');
if(!target.endsWith('#pdf-page-0044'))throw new Error('Incorrect first index target');
// Validate the fragment in the current rendered document without leaving it.
await page.evaluate(()=>document.querySelector('#pdf-page-0044').scrollIntoView());
await page.screenshot({path:path.join(here,'visual-reader-target-44.png')});
for(const [name,text] of [['research','Magical Research, Major'],['end','Zaharan Ruinguard Level Progression']]){
 const el=page.locator('.index-block p').filter({hasText:text}).first();await el.scrollIntoViewIfNeeded();
 const y=await el.evaluate(e=>e.getBoundingClientRect().top+scrollY);await page.evaluate(y=>scrollTo(0,y-40),y);
 await page.screenshot({path:path.join(here,`visual-reader-${name}.png`)});
}
await browser.close();
fs.writeFileSync(path.join(here,'reader_visual_metrics.json'),JSON.stringify({...metrics,first_link_target:target},null,2)+'\n');
console.log(JSON.stringify(metrics));
