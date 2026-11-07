import {writeFile} from 'node:fs/promises';
import {base,site,route} from '../src/site/config.mjs';
const urls=site.locales.map(locale=>site.origin+route(locale));
await writeFile('out/sitemap.xml',`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map(url=>`<url><loc>${url}</loc></url>`).join('')}</urlset>\n`);
await writeFile('out/robots.txt',`User-agent: *\nAllow: /\nSitemap: ${site.origin}${base}/sitemap.xml\n`);
await writeFile('out/.nojekyll','');
console.log('Static export ready in out/. No deployment performed.');
