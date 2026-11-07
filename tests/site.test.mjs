import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {dictionary} from '../src/page.mjs';
const renderPage = lang => readFileSync(new URL(`../out/${lang==='ja'?'ja/':''}index.html`,import.meta.url),'utf8');
const exampleOrder={en:['en-recommend','en-only','en-unless','ja-scope','zh-topic','fr-relative','es-notall','de-relative','math-fraction','math-commute'],ja:['ja-scope','ja-quote','ja-unread','en-recommend','zh-topic','fr-relative','es-notall','de-relative','math-fraction','math-commute']};
import {examples,introductory} from '../src/examples.mjs';
import {filterEntries, entryDetailHTML} from '../src/dictionary-data.mjs';
const publicUrl = path => new URL(`../public/${path}`,import.meta.url);
const hash = value => createHash('sha256').update(value).digest('hex');

test('Next static exports have valid local links, anchors and unique IDs',async()=>{
  for(const base of ['/noema']) for(const lang of ['ja','en']) {
    const html=renderPage(lang,base);
    assert.match(html,new RegExp(`<html lang="${lang}">`));
    assert.equal((html.match(/<h1\b/g)??[]).length,1);
    const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
    assert.equal(new Set(ids).size,ids.length,`${lang}: duplicate IDs`);
    for(const [,link] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
      if(link.startsWith('https://')) continue;
      if(link.startsWith('#')) {assert.ok(ids.includes(link.slice(1)),`Missing anchor ${link}`);continue;}
      assert.ok(link.startsWith(`${base}/`),`Incorrect base: ${link}`);
      const relative=link.slice(base.length+1);
      if(['','ja/','dictionary/','ja/dictionary/'].includes(relative))continue;
      await access(new URL(`../out/${relative}`,import.meta.url));
    }
    assert.equal((html.match(/class="example"/g)??[]).length,10);
    assert.deepEqual([...html.matchAll(/<article class="example" id="([^"]+)"/g)].map(m=>m[1]),exampleOrder[lang]);
  }
});

test('the rendered SVG and downloadable source match each pinned sample',async()=>{
  const manifest=JSON.parse(await readFile(publicUrl('glyphs/provenance.json'),'utf8'));
  assert.equal(manifest.renderer,'concept2-v7');
  for(const item of [...examples,introductory]) {
    const source=await readFile(publicUrl(`examples/${item.id}.noema`),'utf8');
    const svg=await readFile(publicUrl(`glyphs/${item.id}.svg`),'utf8');
    assert.equal(source,item.source,`${item.id}: stale source`);
    assert.equal(hash(source),manifest.samples[item.id].source_sha256);
    assert.equal(hash(svg),manifest.samples[item.id].svg_sha256);
    assert.match(svg,/<circle /);
    assert.ok(!/<(?:script|foreignObject)\b/.test(svg));
    const evidence=manifest.samples[item.id];
    assert.equal(evidence.visible_decode,true);
    assert.equal(hash(await readFile(publicUrl(`examples/${item.id}-visible.noema`))),evidence.visible_source_sha256);
    for(const declaration of evidence.declarations) assert.equal(hash(await readFile(publicUrl(declaration.svg))),declaration.svg_sha256);
  }
  for(const asset of manifest.alphabet) assert.equal(hash(await readFile(publicUrl(asset.svg))),asset.sha256);
  for(const asset of manifest.specimens) assert.equal(hash(await readFile(publicUrl(`glyphs/${asset.file}`))),asset.sha256);
});

test('the completed catalogue preserves categories and can search meanings, roles and spellings',()=>{
  assert.equal(dictionary.entries.length,1952);
  assert.equal(filterEntries(dictionary.entries,{kind:'definition'}).length,463);
  assert.equal(filterEntries(dictionary.entries,{kind:'primitive'}).length,1489);
  assert.equal(filterEntries(dictionary.entries,{scope:'source-selector'}).length,27);
  assert.ok(filterEntries(dictionary.entries,{query:'上下軸'}).some(e=>e.name==='above'));
  assert.ok(filterEntries(dictionary.entries,{query:'ABOVE'}).some(e=>e.name==='above'));
  assert.equal(filterEntries(dictionary.entries,{query:'give'})[0].name,'give');
  assert.equal(filterEntries(dictionary.entries,{query:'no-such-noema-word-12345'}).length,0);
  for(const lang of ['ja','en']) {
    const html=renderPage(lang,'/noema');
    assert.equal((html.match(/class="dictionary-entry"/g)??[]).length,60);
    assert.match(html,/id="dictionary-query"/);
    assert.ok(!/>undefined</.test(html));
    assert.ok(!html.includes('[object Object]'));
  }
  const unsafe={...dictionary.entries[0],name:'<script>',meaning:'<img onerror=alert(1)>'};
  assert.ok(!entryDetailHTML(unsafe,'en').includes('<img onerror'));
  assert.ok(entryDetailHTML(unsafe,'en').includes('&lt;img'));
});

test('edition pages link to current specifications and omit obsolete completion claims',()=>{
  for(const lang of ['ja','en']) {
    const html=renderPage(lang,'/noema');
    assert.match(html,/docs\/language-edition-v1\.md/);
    assert.match(html,/docs\/circle-writing-v2\.md/);
    assert.ok(!/WORK IN PROGRESS|読み戻しは未完成|recovery.*remains unfinished|docs\/kant-page-script/.test(html));
  }
});

test('panels replace plus buttons, native search clearing, and duplicate source controls',()=>{
  for(const lang of ['ja','en']) {
    const html=renderPage(lang);
    for(const id of ['about','structure','primitives','reading','dictionary','examples','resources']) assert.ok(html.includes(`id="${id}"`));
    assert.ok(!html.includes('<details'));
    assert.match(html,/<dialog[^>]+id="detail-dialog"/);
    assert.ok(!html.includes('/design/plus.svg'));
    assert.match(html,/<input[^>]+type="text"/);
    assert.match(html,/glyphs\/hero\.svg/);
    assert.equal((html.match(/class="root-track"/g)??[]).length,2);
    assert.equal((html.match(/<img[^>]+src="[^"]*glyphs\/roots\//g)??[]).length,60);
    assert.ok(html.includes('__NEXT_DATA__'));
    assert.ok(!html.includes('EventSource'));
  }
});

test('Figma assets are pinned locally and used by both page translations',async()=>{
  const manifest=JSON.parse(await readFile(publicUrl('design/provenance.json'),'utf8'));
  assert.equal(manifest.nodeId,'288:2');
  for(const asset of manifest.assets) {
    assert.equal(hash(await readFile(publicUrl(`design/${asset.file}`))),asset.sha256,asset.file);
    if(asset.usage!=='archive'&&asset.file!=='close.svg') assert.ok(['ja','en'].some(lang=>renderPage(lang).includes(`/design/${asset.file}`)),`Unused asset ${asset.file}`);
  }
  for(const lang of ['ja','en']) assert.ok(!renderPage(lang,'/noema').includes('figma.com/api'));
});

test('all roots share the same viewport, center, and scale',async()=>{
 const manifest=JSON.parse(await readFile(publicUrl('glyphs/provenance.json'),'utf8'));
 for(const root of manifest.alphabet){
  const svg=await readFile(publicUrl(`glyphs/roots/${root.name}.svg`),'utf8');
  assert.match(svg,/viewBox="0 0 140(?:\.0+)? 140(?:\.0+)?"/);
  assert.ok(!svg.includes('scale('));
 }
});
