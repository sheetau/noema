import {content, languages, repository} from './content.mjs';
import {examples, introductory} from './examples.mjs';
import {readFileSync} from 'node:fs';

export const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const arrow = '<span aria-hidden="true">↗</span>';
const docLink = path => `${repository}/blob/main/${path}`;
const glyphSizes = new Map([...examples,introductory].map(({id}) => {
  const svg=readFileSync(new URL(`../public/glyphs/${id}.svg`,import.meta.url),'utf8');
  return [id, {width:svg.match(/ width="([\d.]+)"/)[1],height:svg.match(/ height="([\d.]+)"/)[1]}];
}));

function diagram(type) {
  const guides = '<path class="guide" d="M16 38H284M16 70H284M16 102H284"/>';
  const shapes = {
    sizes: '<circle cx="65" cy="70" r="35.8823"/><path d="M65 70H100.8823"/><circle cx="166" cy="70" r="22.6274"/><circle cx="248" cy="70" r="9.3726"/>',
    guides: '<circle cx="65" cy="70" r="35.8823"/><path d="M65 70H100.8823"/><circle cx="174" cy="38" r="22.6274"/><circle cx="174" cy="70" r="9.3726"/><circle cx="250" cy="102" r="22.6274"/>',
    contacts: '<circle cx="57" cy="70" r="22.6274"/><path d="M57 70H115L147 102H184.6274"/><circle cx="194" cy="102" r="9.3726"/><circle cx="250" cy="38" r="22.6274"/><path d="M234 54L210 78"/>',
  };
  return `<svg viewBox="0 0 300 140" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${type === 'guides' ? guides : ''}${shapes[type]}</svg>`;
}

function opening(index) {
  const shapes = [
    '<circle cx="60" cy="50" r="22.6274"/><path d="M60 50V27.3726"/>',
    '<circle cx="60" cy="50" r="22.6274"/><path d="M60 50L44 66"/>',
    '<circle cx="60" cy="50" r="35.8823"/><path d="M34.6274 24.6274L24.1177 14.1177"/>',
    '<circle cx="60" cy="50" r="22.6274"/>',
  ];
  return `<svg viewBox="0 0 120 100" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${shapes[index]}</svg>`;
}

export function renderPage(locale, base) {
  const c = content[locale];
  const local = locale === 'ja';
  const href = p => `${base}/${p}`;
  const localeHref = lang => href(lang === 'en' ? '' : 'ja/');
  const canonical = `https://sheetau.github.io/noema/${local ? 'ja/' : ''}`;
  const heading = (n, label, title, text) => `<div class="section-heading"><p class="eyebrow"><span class="section-number">${n}</span>${label}</p><h2>${title}</h2>${text ? `<p class="section-intro">${text}</p>` : ''}</div>`;
  const glyph = (id, alt, cls='') => `<img class="glyph ${cls}" src="${href(`glyphs/${id}.svg`)}" width="${glyphSizes.get(id).width}" height="${glyphSizes.get(id).height}" alt="${escape(alt)}" loading="lazy" decoding="async">`;
  const sourceDetails = (item) => `<details class="source-details"><summary>${c.source}<span aria-hidden="true" class="details-plus">+</span></summary><div class="source-body">
      ${item.formula ? `<p class="micro-label">${c.formula}</p><p class="formula" dir="ltr">${escape(item.formula)}</p>` : ''}
      <p class="micro-label">${c.sourceLabel}</p><pre dir="ltr"><code>${escape(item.source)}</code></pre>
      <p class="micro-label">${c.glossary}</p><p>${escape(item.glossary[locale])}</p>
      <a class="text-link" href="${href(`examples/${item.id}.noema`)}" download>${c.download}<span aria-hidden="true">↓</span></a>
    </div></details>`;
  const exampleCard = (item, index, compact=false) => `<article class="example ${compact ? 'example-compact' : ''}" id="${item.id}" data-language="${item.lang}">
    <div class="example-heading"><span class="micro-label">${String(index+1).padStart(2,'0')} / ${languages[item.lang]}</span><h3>${escape(item.title[locale])}</h3></div>
    <p class="original" lang="${item.lang === 'math' ? locale : item.lang}" dir="${item.lang === 'ar' ? 'rtl' : 'ltr'}">${escape(item.text)}</p>
    <div class="glyph-surface">${glyph(item.id, local ? `「${item.text}」のNoema記述` : `Noema rendering of “${item.text}”`)}</div>
    <p class="example-note">${escape(item.note[locale])}</p>${sourceDetails(item)}</article>`;
  const world = [...examples.filter(x=>x.lang===(local?'en':'ja')).slice(0,1),...examples.filter(x=>['zh','fr','es','de','ar'].includes(x.lang))];
  const nav = ['structure','primitives','reading','examples'].map((id,i)=>`<a href="#${id}">${c.nav[i]}</a>`).join('');
  const localeSwitch = `<nav class="language-switch" aria-label="${c.language}"><a href="${localeHref('ja')}" lang="ja" hreflang="ja" ${local?'aria-current="page"':''}>JA</a><span aria-hidden="true">/</span><a href="${localeHref('en')}" lang="en" hreflang="en" ${!local?'aria-current="page"':''}>EN</a></nav>`;
  return `<!doctype html>
<html lang="${locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<title>${c.title}</title><meta name="description" content="${escape(c.description)}"><link rel="canonical" href="${canonical}">
<link rel="alternate" hreflang="ja" href="https://sheetau.github.io/noema/ja/"><link rel="alternate" hreflang="en" href="https://sheetau.github.io/noema/"><link rel="alternate" hreflang="x-default" href="https://sheetau.github.io/noema/">
<meta property="og:type" content="website"><meta property="og:site_name" content="Noema"><meta property="og:title" content="${c.title}"><meta property="og:description" content="${escape(c.description)}"><meta property="og:url" content="${canonical}"><meta property="og:locale" content="${local?'ja_JP':'en_US'}">
<meta name="theme-color" content="#000000"><link rel="icon" href="${href('favicon.svg')}" type="image/svg+xml"><link rel="preload" href="${href('fonts/helvetica-now-text.ttf')}" as="font" type="font/ttf" crossorigin><link rel="stylesheet" href="${href('style.css')}"><script src="${href('site.js')}" defer></script></head>
<body id="top"><a class="skip-link" href="#main">${c.skip}</a>
<header class="site-header"><div class="header-inner container"><a class="wordmark" href="${localeHref(locale)}" aria-label="Noema — ${local?'トップ':'Home'}">noema</a><nav class="main-nav" aria-label="${local?'セクション':'Sections'}">${nav}</nav>${localeSwitch}</div><div class="scroll-progress" aria-hidden="true"></div></header>
<main id="main" class="container">
<section class="hero" aria-labelledby="hero-title"><div class="hero-top"><div><p class="eyebrow">${c.eyebrow}</p><h1 id="hero-title">noema<span class="hero-subtitle">${c.hero}</span></h1></div><div class="hero-description"><p>${c.intro}</p><div class="hero-links"><a class="text-link" href="#structure">${c.explore}<span aria-hidden="true">↓</span></a><a class="text-link muted" href="${repository}">GitHub ${arrow}</a></div></div></div>
<a class="hero-specimen" href="${href('glyphs/kant-page.svg')}" data-specimen aria-label="${c.specimenNote}"><img src="${href('glyphs/kant-opening.svg')}" width="1440" height="340" alt="${c.specimen}" fetchpriority="high"><span class="specimen-expand" aria-hidden="true">↗</span></a>
<div class="hero-caption"><span>${c.specimen}</span><span class="status-label"><span aria-hidden="true"></span>${c.draft}</span></div></section>

<section class="section overview" aria-labelledby="overview-title"><div class="overview-heading"><h2 id="overview-title">${c.overviewTitle}</h2><p>${c.overviewIntro}</p></div><div class="feature-grid">${c.features.map(([title,text],i)=>`<article><span class="index">0${i+1}</span><h3>${title}</h3><p>${text}</p></article>`).join('')}</div></section>

<section class="section" id="structure">${heading('01','STRUCTURE',c.structureTitle,c.structureIntro)}<div class="structure-display"><p class="micro-label">${local?'ひとつの関係':'A SINGLE RELATION'}</p><p class="structure-sentence">${c.simple}</p>${glyph('reading', local?'アキ・本・ナオをgiveの引数に持つ円文字':'Circle notation for give(aki, book, nao)')}<p class="caption">${c.simpleNote}</p></div>
<div class="feature-grid structure-steps">${c.structureSteps.map(([title,text],i)=>`<article><span class="index">0${i+1}</span><h3>${title}</h3><p>${text}</p></article>`).join('')}</div>
${sourceDetails({...introductory, formula:'give(aki, book, nao)', glossary:{ja:'give(x,y,z)：xがyをzに渡す。aki：アキ。book：この例で渡す本。nao：ナオ。三つの名前は型aの対象を指す。',en:'give(x,y,z): x gives y to z. aki: Aki. book: the book given in this example. nao: Nao. The three names refer to objects of sort a.'}})}</section>

<section class="section" id="primitives">${heading('02','PRIMITIVES',c.primitivesTitle,c.primitivesIntro)}<div class="primitive-grid">${c.primitives.map(([title,text],i)=>`<article>${diagram(['sizes','guides','contacts'][i])}<h3>${title}</h3><p>${text}</p></article>`).join('')}</div><a class="text-link section-link" href="${docLink('docs/writing-system.md')}">${c.primitivesLink}${arrow}</a>
<div class="operations"><div><h3>${c.languagePrimitiveTitle}</h3><p>${c.languagePrimitiveIntro}</p></div><dl>${c.operations.map(([title,syntax,text])=>`<div class="operation"><dt>${title}<code>${syntax}</code></dt><dd>${text}</dd></div>`).join('')}</dl></div></section>

<section class="section" id="reading">${heading('03','READING & WRITING',c.readingTitle,c.readingIntro)}<ol class="reading-steps">${c.readingSteps.map(([title,text],i)=>`<li><span class="index">0${i+1}</span><div><h3>${title}</h3><p>${text}</p></div></li>`).join('')}</ol>
<div class="opening-intro"><h3>${c.openingTitle}</h3><p>${c.openingIntro}</p></div><div class="opening-grid">${c.openings.map(([title,text],i)=>`<figure>${opening(i)}<figcaption><h4>${title}</h4><p>${text}</p></figcaption></figure>`).join('')}</div><p class="reading-note">${c.readingLimit}</p><a class="text-link" href="${docLink('docs/kant-page-script-v3.md')}">${local?'文頭と配置の詳しい規則':'Opening and layout rules'}${arrow}</a></section>

<section class="section" id="examples">${heading('04',local?'JAPANESE → NOEMA':'ENGLISH → NOEMA',c.examplesTitle,c.examplesIntro)}<p class="caption example-preface">${c.examplesNote}</p><div class="local-examples">${examples.filter(x=>x.lang===locale).map((item,i)=>exampleCard(item,i)).join('')}</div></section>

<section class="section" id="languages">${heading('05','ACROSS LANGUAGES',c.worldTitle,c.worldIntro)}<div class="language-filters" role="group" aria-label="${c.filterLabel}" hidden><button type="button" data-filter="all" aria-pressed="true">${c.worldAll}</button>${world.map(x=>`<button type="button" data-filter="${x.lang}" aria-pressed="false" lang="${x.lang}">${languages[x.lang]}</button>`).join('')}</div><div class="world-examples">${world.map((item,i)=>exampleCard(item,i,true)).join('')}</div><p class="sr-only" id="filter-status" role="status" aria-live="polite"></p></section>

<section class="section" id="mathematics">${heading('06','MATHEMATICS',c.mathTitle,c.mathIntro)}<div class="math-examples">${examples.filter(x=>x.lang==='math').map((item,i)=>exampleCard(item,i,true)).join('')}</div></section>

<section class="section" id="status">${heading('07','WORK IN PROGRESS',c.statusTitle,c.statusIntro)}<div class="status-grid">${c.statusItems.map(([title,text])=>`<article><h3>${title}</h3><p>${text}</p></article>`).join('')}</div></section>
<section class="section resources" id="resources">${heading('08','FURTHER READING',c.resourcesTitle,c.resourcesIntro)}<div class="resource-links">${c.resources.map(([title,text,path])=>`<a href="${docLink(path)}"><span><h3>${title}</h3><p>${text}</p></span>${arrow}</a>`).join('')}</div></section>
</main><footer class="site-footer container"><div class="footer-top"><a class="footer-wordmark" href="#top">noema</a><p>${c.footer}</p><a class="text-link" href="#top">${c.top}<span aria-hidden="true">↑</span></a></div><div class="footer-bottom"><span>© 2026 sheeta</span><a href="${repository}">GitHub ${arrow}</a>${localeSwitch}</div></footer>
<dialog class="specimen-dialog" aria-labelledby="specimen-dialog-title"><div class="dialog-header"><h2 id="specimen-dialog-title">${c.specimenDialog}</h2><button type="button" data-close-dialog>${c.close}<span aria-hidden="true">×</span></button></div><div class="dialog-content"><img src="${href('glyphs/kant-page.svg')}" width="1600" height="2263" alt="${c.fullPage}" loading="lazy"><a class="text-link" href="${href('glyphs/kant-page.svg')}" target="_blank" rel="noopener">${c.fullPage}${arrow}</a></div></dialog>
</body></html>`;
}
