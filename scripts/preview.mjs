import {createServer} from 'node:http';
import {readFile, stat} from 'node:fs/promises';
import {resolve, sep, extname} from 'node:path';
import {build, root, base} from './build.mjs';
await build();
const directory = resolve(root,'dist');
const types = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.json':'application/json; charset=utf-8','.noema':'text/plain; charset=utf-8','.woff2':'font/woff2','.ttf':'font/ttf','.txt':'text/plain; charset=utf-8','.xml':'application/xml'};
const server = createServer(async (req,res)=>{
  try {
    let path = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if (path === '/' && base) { res.writeHead(302,{Location:`${base}/ja/`}); return res.end(); }
    if (path === base && base) {res.writeHead(301,{Location:`${base}/`}); return res.end();}
    if (base && !path.startsWith(`${base}/`)) {res.writeHead(404);return res.end('Not found');}
    let file = resolve(directory, `.${path.slice(base.length)}`);
    if (file!==directory && !file.startsWith(directory+sep)) {res.writeHead(403);return res.end('Forbidden');}
    if ((await stat(file)).isDirectory()) file=resolve(file,'index.html');
    const body=await readFile(file);
    res.writeHead(200,{'Content-Type':types[extname(file)]??'application/octet-stream','Cache-Control':'no-store'});
    res.end(body);
  } catch {res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('Not found');}
});
const port = Number(process.env.PORT ?? 4173);
server.listen(port,'127.0.0.1',()=>console.log(`Local: http://localhost:${port}${base}/ja/`));
