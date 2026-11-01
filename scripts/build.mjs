import {mkdir, cp, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {renderPage} from '../src/page.mjs';
export const root = fileURLToPath(new URL('../', import.meta.url));
export const base = (process.env.BASE_PATH ?? '/noema').replace(/\/$/, '');
if (base && !/^\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*$/.test(base)) throw new Error('BASE_PATH must be empty or an absolute URL path without a trailing slash.');
export async function build() {
  await mkdir(new URL('../dist/ja/', import.meta.url), {recursive:true});
  await cp(new URL('../public/', import.meta.url), new URL('../dist/', import.meta.url), {recursive:true});
  for (const locale of ['en','ja']) await writeFile(new URL(`../dist/${locale==='ja'?'ja/':''}index.html`, import.meta.url), renderPage(locale,base));
  await writeFile(new URL('../dist/.nojekyll', import.meta.url), '');
  await writeFile(new URL('../dist/sitemap.xml', import.meta.url), '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://sheetau.github.io/noema/</loc></url><url><loc>https://sheetau.github.io/noema/ja/</loc></url></urlset>\n');
  console.log(`Built English and Japanese pages in dist/ (base: ${base || '/'})`);
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await build();
