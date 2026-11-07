import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {root} from '../src/site/config.mjs';

const source = resolve(process.env.NOEMA_SOURCE ?? resolve(root, '../noema'));
const read = async path => JSON.parse(await readFile(resolve(source, path), 'utf8'));
const release = await read('data/language-release-v1.json');
const catalog = await read('data/general-language-catalog-v2.json');
if (release.status !== 'complete_under_stated_scope' || catalog.counts.entries !== 1952) throw new Error('Review the selected release before exporting.');
const entries = Object.values(catalog.entries).map(entry => ({
  name:entry.name, symbol:entry.symbol, spelling:entry.spelling, meaning:entry.meaning,
  roles:entry.roles ?? [], context:entry.context ?? [], contrast:entry.contrast ?? [],
  kind:entry.declaration.kind, parameters:entry.declaration.parameters,
  result:entry.declaration.result, portability:entry.portability, sources:entry.sources,
}));
await mkdir(resolve(root, 'public/data'), {recursive:true});
const path = 'data/general-language-catalog-v2.json';
const hash = createHash('sha256').update(await readFile(resolve(source, path))).digest('hex');
await writeFile(resolve(root, 'public/data/dictionary.json'), JSON.stringify({edition:'1.0', source:path, sha256:hash, counts:catalog.counts, entries}) + '\n');
console.log(`Exported ${entries.length} dictionary entries with source hash ${hash.slice(0, 12)}.`);
