import fs from 'node:fs';
import {marked} from 'file:///C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const [id, value] of Object.entries(data)) data[id] = marked.parseInline(value, {gfm:true});
process.stdout.write(JSON.stringify(data));
