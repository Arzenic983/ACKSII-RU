import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {chromium} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1400, height: 1100}, deviceScaleFactor: 1});
await page.goto(pathToFileURL(path.join(here, 'preview.html')).href);
await page.locator('#pdf-page-0016').scrollIntoViewIfNeeded();
await page.locator('#pdf-page-0016').evaluate(el => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 12));
await page.screenshot({path: path.join(here, 'page16.png')});
const metrics = await page.locator('#pdf-page-0016').evaluate(el => {
  const heading = el.nextElementSibling;
  const subtitle = heading.nextElementSibling;
  return {pageText: el.innerText, alignment: getComputedStyle(el).textAlign,
    markerSize: getComputedStyle(el.querySelector('small')).fontSize,
    heading: heading.innerText, subtitle: subtitle.innerText,
    headingSize: getComputedStyle(heading).fontSize,
    subtitleSize: getComputedStyle(subtitle.querySelector('small')).fontSize};
});
await browser.close();
if (!metrics.alignment.endsWith('right') || parseFloat(metrics.subtitleSize) >= parseFloat(metrics.headingSize)) throw new Error('Layout failed');
fs.writeFileSync(path.join(here, 'visual_validation.json'), JSON.stringify(metrics, null, 2));
console.log(JSON.stringify(metrics));
