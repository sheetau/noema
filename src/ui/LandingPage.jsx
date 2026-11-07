import KantSpread from './KantSpread';
import HeaderLogo from './HeaderLogo';
import {ScrollArea} from './ScrollArea';
import Head from 'next/head';
import {useEffect,useRef,useState} from 'react';
import {getContent,languages} from '../content.mjs';
import {examples,introductory} from '../examples.mjs';
import {asset,base,repository,origin,route,docLink} from '../site/web.mjs';
import design from '../../public/design/provenance.json';
import Dictionary from './Dictionary';
import Details from './Details';
import RootMarquee from './RootMarquee';

const commonExamples=['zh-topic','fr-relative','es-notall','de-relative','math-fraction','math-commute'];
const exampleOrder={en:['en-recommend','en-only','en-unless','ja-scope'],ja:['ja-scope','ja-quote','ja-unread','en-recommend']};
const sections=[['about','ABOUT'],['structure','STRUCTURE'],['primitives','PRIMITIVES'],['reading','READING'],['dictionary','DICTIONARY'],['examples','EXAMPLES'],['resources','MORE']];
const worksPaths=['examples/v016/kant-reviewed-complete-v1.noema','examples/v014/einstein-reviewed-complete-v1.noema'];
function Image({file,alt='',className='',eager=false}) {
  const {width,height}=design.assets.find(a=>a.file===file);
  return <img src={asset('design/'+file)} width={width} height={height} alt={alt} className={className} loading={eager?undefined:'lazy'} fetchPriority={eager?'high':undefined} decoding="async"/>;
}
function Heading({n,label,title,intro}) {
  return <div className="section-heading"><p className="eyebrow"><span className="section-number">{String(n).padStart(2,'0')}</span>{label}</p><h2>{title}</h2><p className="section-intro">{intro}</p></div>;
}
function Columns({items,numbered=false}) {
  return <div className="feature-grid">{items.map(([title,text],i)=><article key={i}>{numbered&&<p className="index">0{i+1}</p>}<h3>{title}</h3><p>{text}</p></article>)}</div>;
}
function Languages({locale}) {
  return <nav className="language-switch" aria-label={getContent(locale).language}>{['ja','en'].map((lang,i)=><span className="language-option" key={lang}>{!!i&&<span aria-hidden="true">/</span>}<a href={route(lang)} lang={lang} hrefLang={lang} aria-current={locale===lang?'page':undefined} onClick={e=>{e.currentTarget.search=location.search;e.currentTarget.hash=location.hash;}}>{lang.toUpperCase()}</a></span>)}</nav>;
}

export default function LandingPage({locale,initialEntries,counts,source}) {
  const c=getContent(locale),ja=locale==='ja';
  const selected=[...exampleOrder[locale],...commonExamples].map(id=>examples.find(e=>e.id===id));
  const [selection,setSelection]=useState(null),[menu,setMenu]=useState(false),[active,setActive]=useState('');
  const returnFocus=useRef(null),progress=useRef(null),menuButton=useRef(null);
  const open=(value,trigger)=>{returnFocus.current=trigger;setSelection(value);};
  useEffect(()=>{
    let raf;const update=()=>{const available=document.documentElement.scrollHeight-innerHeight;progress.current.style.transform=`scaleX(${available>0?Math.min(1,Math.max(0,scrollY/available)):0})`;let id='';const threshold=(document.querySelector('.site-header')?.offsetHeight??60)+80;for(const [key] of sections)if(document.getElementById(key).getBoundingClientRect().top<=threshold)id=key;if(available>0&&scrollY>=available-4)id='resources';setActive(id);};
    const schedule=()=>{cancelAnimationFrame(raf);raf=requestAnimationFrame(update);};
    addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);const observer=new ResizeObserver(schedule);observer.observe(document.body);update();
    return()=>{cancelAnimationFrame(raf);removeEventListener('scroll',schedule);removeEventListener('resize',schedule);observer.disconnect();};
  },[]);
  useEffect(()=>{const close=e=>{if(e.type==='keydown'&&e.key==='Escape'){setMenu(false);menuButton.current?.focus();}else if(e.type==='pointerdown'&&!e.target.closest('.site-header'))setMenu(false);};if(menu){document.addEventListener('keydown',close);document.addEventListener('pointerdown',close);}return()=>{document.removeEventListener('keydown',close);document.removeEventListener('pointerdown',close);};},[menu]);
  const nav=sections.map(([id,label])=><a key={id} href={`#${id}`} data-section-link={id} aria-current={active===id?'location':undefined} onClick={()=>setMenu(false)}>{label}</a>);
  const relation={...introductory,lang:locale,text:c.simple,formula:'give(aki, book, nao)',title:{ja:c.simple,en:c.simple},note:{[locale]:c.simpleNote},glossary:{ja:'give(x,y,z)：xがyをzに渡す。aki：アキ。book：渡す本。nao：ナオ。三つの名前は個体型の対象を指します。',en:'give(x,y,z): x gives y to z. aki: Aki. book: the book being given. nao: Nao. Each name refers to an individual.'}};
  return <>
    <Head><title>{c.title}</title><meta name="description" content={c.description}/><link rel="canonical" href={origin+route(locale)}/>
      {['ja','en'].map(lang=><link key={lang} rel="alternate" hrefLang={lang} href={origin+route(lang)}/>)}<link rel="alternate" hrefLang="x-default" href={origin+route('en')}/>
      <meta property="og:type" content="website"/><meta property="og:site_name" content="Noema"/><meta property="og:title" content={c.title}/><meta property="og:description" content={c.description}/><meta property="og:url" content={origin+route(locale)}/><meta property="og:locale" content={ja?'ja_JP':'en_US'}/><meta property="og:image" content={origin+asset('og.png')}/><meta property="og:image:width" content="1200"/><meta property="og:image:height" content="630"/><meta name="twitter:card" content="summary_large_image"/>
      <script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify({'@context':'https://schema.org','@type':'WebSite',name:'Noema',url:origin+base+'/',inLanguage:['ja','en'],description:c.description})}}/>
    </Head>
    <a className="skip-link" href="#main">{c.skip}</a><header className="site-header"><div className="header-inner"><a className="header-wordmark" href={route(locale)} aria-label={`Noema — ${ja?'トップ':'Home'}`}><HeaderLogo/></a><nav className="main-nav" aria-label={ja?'セクション':'Sections'}>{nav}</nav><div className="header-actions"><Languages locale={locale}/><button ref={menuButton} className="menu-toggle" type="button" aria-expanded={menu} aria-controls="mobile-menu" onClick={()=>setMenu(!menu)}>{ja?'目次':'Menu'}</button></div></div><nav id="mobile-menu" className="mobile-menu" hidden={!menu}>{nav}</nav><div ref={progress} className="scroll-progress" aria-hidden="true"/></header>
    <main id="main" className="container">
      <section className="hero" aria-labelledby="hero-title"><h1 id="hero-title" aria-label="Noema"><Image file="logo.svg" alt="Noema" className="hero-logo" eager/></h1><p className="hero-subtitle">{c.hero}</p><a className="text-link" href={repository}>GitHub ↗</a><button className="hero-specimen" type="button" aria-label={c.specimenNote} aria-haspopup="dialog" onClick={e=>open({kind:'kant'},e.currentTarget)}><img src={asset('glyphs/hero.svg')} className="ink" alt={c.specimen} fetchPriority="high"/></button><p className="caption hero-caption">{c.specimen}</p></section>
      <section className="section" id="about"><Heading n={1} label="ABOUT" title={c.aboutTitle} intro={c.aboutIntro}/><Columns items={c.features}/><KantSpread locale={locale} onOpen={e=>open({kind:'kant'},e.currentTarget)}/></section>
      <section className="section" id="structure"><Heading n={2} label="STRUCTURE" title={c.structureTitle} intro={c.structureIntro}/><button type="button" className="relation-panel" aria-haspopup="dialog" onClick={e=>open({kind:'source',id:relation.id},e.currentTarget)}><span className="micro-label">A SINGLE RELATION</span><span className="relation-sentence">{c.simple}</span><span className="relation-illustration"><Image file="relation.png" alt={c.simple}/></span><span className="relation-caption"><span className="caption">{c.simpleNote}</span></span></button><Columns items={c.structureSteps} numbered/></section>
      <section className="section" id="primitives"><Heading n={3} label="PRIMITIVES" title={c.primitivesTitle} intro={c.primitivesIntro}/><ScrollArea className="primitive-board" id="primitive-board" both><Image file="primitives.svg" alt={ja?'円の寸法、基準線、接続と参照':'Circle scales, guides, connections, and references'}/></ScrollArea><Columns items={c.primitives}/><a className="text-link" href={docLink('docs/circle-writing-v2.md')}>{c.primitivesLink} ↗</a>
        <div className="alphabet"><div className="alphabet-heading"><div><h3>{c.alphabetTitle}</h3><p>{c.alphabetIntro}</p></div></div><RootMarquee locale={locale}/></div><div className="operations"><h3>{c.languagePrimitiveTitle}</h3><p>{c.languagePrimitiveIntro}</p><dl>{c.operations.map(([title,syntax,text])=><div key={title}><dt>{title}</dt><dd className="operation-syntax">{syntax}</dd><dd>{text}</dd></div>)}</dl></div>
      </section>
      <section className="section" id="reading"><Heading n={4} label="READING & WRITING" title={c.readingTitle} intro={c.readingIntro}/><div className="reading-grid">{c.readingSteps.map(([title,text],i)=><article key={i}><img className="reading-diagram" src={asset(`diagrams/${['spelling','branches','scope'][i]}.svg`)} width="360" height="166" alt={title} loading="lazy"/><p className="index">0{i+1}</p><h3>{title}</h3><p>{text}</p></article>)}</div><a className="text-link" href={docLink('docs/circle-writing-v2.md')}>{c.primitivesLink} ↗</a></section>
      <section className="section" id="dictionary"><Heading n={5} label="DICTIONARY" title={c.dictionaryTitle} intro={c.dictionaryIntro}/><Dictionary locale={locale} initialEntries={initialEntries} counts={counts} source={source} onOpen={open}/></section>
      <section className="section" id="examples"><Heading n={6} label="EXAMPLES" title={c.examplesTitle} intro={c.examplesIntro}/><div className="examples-grid">{selected.map((item,i)=><article className="example" id={item.id} key={item.id} data-language={item.lang}><p className="micro-label">{String(i+1).padStart(2,'0')} / <span lang={item.lang==='math'?locale:item.lang}>{languages[item.lang]}</span></p><h3 className="example-title">{item.title[locale]}</h3><p className={`original ${item.lang==='math'?'math-original':''}`} lang={item.lang==='math'?locale:item.lang}>{item.text}</p><button type="button" className="example-panel" aria-haspopup="dialog" aria-label={`${c.source}: ${item.text}`} onClick={e=>open({kind:'source',id:item.id},e.currentTarget)}>{['ja-quote','ja-unread'].includes(item.id)?<img className="ink" src={asset(`glyphs/${item.id}.svg`)} alt={item.text} loading="lazy"/>:<Image file={item.id+'.png'} alt={item.text}/>}</button><p className="example-note">{item.note[locale]}</p></article>)}</div></section>
      <section className="section resources" id="resources"><Heading n={7} label="MORE" title={c.resourcesTitle} intro={c.resourcesIntro}/><div className="works-grid">{c.works.map(([author,title,count,text],i)=><article key={author}><p className="micro-label">COMPLETE WORKS / {author}</p><h3>{title}</h3><p className="work-count">{count}</p><p>{text}</p><a className="text-link" href={docLink(worksPaths[i])}>{c.worksLink} ↗</a></article>)}</div><div className="resource-grid">{c.resources.map(([title,text,path])=><article key={path}><a className="resource-link" href={docLink(path)}><span><h3>{title}</h3><p>{text}</p></span><span className="resource-arrow" aria-hidden="true">↗</span></a></article>)}</div></section>
    </main><footer className="site-footer"><div className="container footer-inner"><span className="copyright">© 2026 sheeta.</span><nav className="footer-links" aria-label={ja?'関連リンク':'Related links'}><a href={repository}>GitHub</a></nav><Languages locale={locale}/></div></footer>
    <Details selection={selection} locale={locale} relation={relation} examples={selected} onClose={()=>setSelection(null)} returnFocus={returnFocus}/>
  </>;
}
