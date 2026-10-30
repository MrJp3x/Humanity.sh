import http from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const project = path.resolve(fileURLToPath(new URL('../',import.meta.url)));
const root = process.argv.includes('--dist') ? path.join(project,'dist') : project;
const port = Number(process.env.PORT || 4173);
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.woff2':'font/woff2','.png':'image/png'};
const server=http.createServer(async(req,res)=>{
  try{
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const relative=pathname==='/'?'index.html':pathname.replace(/^\/+/, '');
    const allowed=['index.html','src/','public/','version.json','humanity/data/catalog.json'].some(prefix=>relative===prefix||prefix.endsWith('/')&&relative.startsWith(prefix));
    if(!allowed||relative.split('/').some(p=>p.startsWith('.')||p==='..')){res.writeHead(404);res.end('Not found');return;}
    const target=path.resolve(root,relative);
    if(!target.startsWith(root+path.sep)){res.writeHead(403);res.end('Forbidden');return;}
    const info=await stat(target);if(!info.isFile())throw new Error('not a file');
    res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'"});
    if(req.method==='HEAD'){res.end();return;}
    createReadStream(target).pipe(res);
  }catch{res.writeHead(404);res.end('Not found');}
});
server.listen(port,'127.0.0.1',()=>console.log(`Humanity.sh · Local: http://127.0.0.1:${port}`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));
