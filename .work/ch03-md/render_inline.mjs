import fs from 'node:fs';
import {marked} from 'marked';

const values = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const [id, text] of Object.entries(values)) {
  values[id] = marked.parseInline(text, {gfm: true});
}
process.stdout.write(JSON.stringify(values));
