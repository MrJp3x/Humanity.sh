import { cp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const dist = path.join(root,'dist');
await rm(dist,{recursive:true,force:true});
await mkdir(dist,{recursive:true});
for(const entry of ['index.html','src','public']) await cp(path.join(root,entry),path.join(dist,entry),{recursive:true});
await mkdir(path.join(dist,'humanity','data'),{recursive:true});
await cp(path.join(root,'humanity','data','catalog.json'),path.join(dist,'humanity','data','catalog.json'));
const pkg = JSON.parse(await readFile(path.join(root,'package.json'),'utf8'));
await writeFile(path.join(dist,'version.json'),JSON.stringify({name:pkg.name,version:pkg.version})+'\n');
console.log(`Built Humanity.sh ${pkg.version} → dist/ (no runtime dependencies)`);
