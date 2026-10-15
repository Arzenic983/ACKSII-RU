import fs from 'node:fs';
import {marked} from 'marked';
const input=fs.readFileSync(0,'utf8');
process.stdout.write(marked.parse(input,{gfm:true}));
