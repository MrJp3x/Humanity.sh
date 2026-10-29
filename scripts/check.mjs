import { readdir, readFile, access } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
let checked=0;
async function walk(dir){
  for(const entry of await readdir(dir,{withFileTypes:true})){
    const file=path.join(dir,entry.name);
    if(entry.isDirectory()){await walk(file);continue;}
    if(!/\.(js|mjs)$/.test(file))continue;
    const result=spawnSync(process.execPath,['--check',file],{encoding:'utf8'});
    if(result.status!==0)throw new Error(result.stderr);
    const source=await readFile(file,'utf8');
    for(const match of source.matchAll(/(?:from\s*|import\s*)['"](\.[^'"]+)['"]/g))await access(path.resolve(path.dirname(file),match[1]));
    checked++;
  }
}
for(const dir of ['src','scripts','tests'])await walk(path.join(root,dir));
for(const asset of ['index.html','public/favicon.svg','public/fonts/Vazirmatn.woff2','public/fonts/OFL.txt'])await access(path.join(root,asset));
console.log(`Checked ${checked} JavaScript modules, imports, and required assets.`);
