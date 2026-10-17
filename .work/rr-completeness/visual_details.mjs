import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const page=await browser.newPage({viewport:{width:1500,height:1800}});
for(const [p,text,name] of [[205,'В начале своей инициативы','correction-205'],[296,'Совершите одну или несколько атак','correction-296'],[320,'Подписи схемы:','legend-320']]){
  await page.goto(pathToFileURL(path.join(here,`sample-${p}.html`)).href);
  await page.locator('p').filter({hasText:text}).last().screenshot({path:path.join(here,name+'.png')});
}
await page.goto(pathToFileURL(path.join(here,'sample-480.html')).href);
await page.locator('[role="img"]').screenshot({path:path.join(here,'scheme-480.png')});
await page.goto(pathToFileURL(path.join(here,'sample-320.html')).href);
await page.locator('img').screenshot({path:path.join(here,'diagram-320.png')});
await browser.close();
