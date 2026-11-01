import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {renderPage} from '../src/page.mjs';
import {examples,introductory} from '../src/examples.mjs';
const publicUrl = path => new URL(`../public/${path}`,import.meta.url);
const hash = value => createHash('sha256').update(value).digest('hex');

test('both locales and base-path variants have valid local links, anchors and unique IDs',async()=>{
  for(const base of ['', '/noema']) for(const lang of ['ja','en']) {
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
      if(['','ja/'].includes(relative))continue;
      await access(publicUrl(relative));
    }
    assert.equal((html.match(/class="example /g)??[]).length,12);
    assert.match(html,/lang="ar" dir="rtl"/);
  }
});

test('the rendered SVG and downloadable source match each pinned sample',async()=>{
  const manifest=JSON.parse(await readFile(publicUrl('glyphs/provenance.json'),'utf8'));
  assert.equal(manifest.renderer,'contextual-opening-10-draft');
  for(const item of [...examples,introductory]) {
    const source=await readFile(publicUrl(`examples/${item.id}.noema`),'utf8');
    const svg=await readFile(publicUrl(`glyphs/${item.id}.svg`),'utf8');
    assert.equal(source,item.source,`${item.id}: stale source`);
    assert.equal(hash(source),manifest.samples[item.id].source_sha256);
    assert.equal(hash(svg),manifest.samples[item.id].svg_sha256);
    assert.match(svg,/<circle /);
    assert.ok(!/<(?:script|foreignObject)\b/.test(svg));
    assert.equal(manifest.samples[item.id].geometry,true);
    assert.equal(manifest.samples[item.id].syntax_roundtrip,true);
  }
});

test('each locale leads with its own examples and reuses one across languages',()=>{
  for(const lang of ['ja','en']) {
    const html=renderPage(lang,'/noema');
    const local=html.split('<div class="local-examples">')[1].split('<section')[0];
    const other=lang==='ja'?'en':'ja';
    assert.equal((local.match(new RegExp(`data-language="${lang}"`,'g'))??[]).length,3);
    assert.ok(html.includes(`id="${examples.find(e=>e.lang===other).id}"`));
  }
});
