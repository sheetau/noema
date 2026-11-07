import {createServer} from 'node:http';
import {readFile, stat} from 'node:fs/promises';
import {resolve, sep, extname} from 'node:path';
import {base} from '../src/site/config.mjs';

const mime = {'.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.js':'text/javascript; charset=utf-8', '.mjs':'text/javascript; charset=utf-8', '.svg':'image/svg+xml', '.png':'image/png', '.ico':'image/x-icon',
  '.json':'application/json; charset=utf-8', '.noema':'text/plain; charset=utf-8',
  '.woff2':'font/woff2', '.ttf':'font/ttf', '.txt':'text/plain; charset=utf-8', '.xml':'application/xml'};

export function options() {
  const value = flag => {const i = process.argv.indexOf(flag); return i < 0 ? undefined : process.argv[i + 1];};
  const port = Number(value('--port') ?? process.env.PORT ?? 4173);
  const host = value('--host') ?? process.env.HOST ?? '127.0.0.1';
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid port');
  return {port, host};
}

export function createStaticServer(directory, {intercept, inject = ''} = {}) {
  const root = resolve(directory);
  return createServer(async (req, res) => {
    if (intercept?.(req, res)) return;
    if (!['GET', 'HEAD'].includes(req.method)) {
      res.writeHead(405, {Allow:'GET, HEAD'}); res.end(); return;
    }
    try {
      const path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      if (path === '/' && base) {res.writeHead(302, {Location:`${base}/ja/`}); res.end(); return;}
      if (path === base && base) {res.writeHead(301, {Location:`${base}/`}); res.end(); return;}
      if (base && !path.startsWith(`${base}/`)) throw new Error('Outside base path');
      let file = resolve(root, `.${path.slice(base.length)}`);
      if (file !== root && !file.startsWith(root + sep)) throw new Error('Outside output');
      if ((await stat(file)).isDirectory()) {
        if (!path.endsWith('/')) {res.writeHead(301, {Location:path + '/'}); res.end(); return;}
        file = resolve(file, 'index.html');
      }
      let body = await readFile(file);
      if (inject && extname(file) === '.html') body = Buffer.from(body.toString('utf8').replace('</body>', `${inject}</body>`));
      res.writeHead(200, {'Content-Type':mime[extname(file)] ?? 'application/octet-stream',
        'Content-Length':body.length, 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'});
      res.end(req.method === 'HEAD' ? undefined : body);
    } catch {
      const body = await readFile(resolve(root, '404.html')).catch(() => Buffer.from('Not found'));
      res.writeHead(404, {'Content-Type':'text/html; charset=utf-8', 'Cache-Control':'no-store'});
      res.end(req.method === 'HEAD' ? undefined : body);
    }
  });
}

export async function listen(server) {
  const {port, host} = options();
  await new Promise((ok, fail) => {server.once('error', fail); server.listen(port, host, ok);});
  console.log(`Local: http://${host === '127.0.0.1' ? 'localhost' : host}:${server.address().port}${base}/ja/`);
}
