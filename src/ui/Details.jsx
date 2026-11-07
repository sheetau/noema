import {useEffect,useRef} from 'react';
import {ScrollArea} from './ScrollArea';
import {asset,docLink} from '../site/web.mjs';
import {getContent} from '../content.mjs';
import {entryDetailHTML} from '../dictionary-data.mjs';
import provenance from '../../public/glyphs/provenance.json';

function Source({item,locale}) {
  const c=getContent(locale),ja=locale==='ja';
  return <>{item.id!=='reading'&&<p className="modal-original" lang={item.lang==='math'?locale:item.lang}>{item.text}</p>}
    <img className="ink modal-glyph" src={asset(`glyphs/${item.id}.svg`)} alt={item.text}/><p>{item.note[locale]}</p>
    {item.formula&&<><h3>{c.formula}</h3><p className="formula" dir="ltr">{item.formula}</p></>}
    <h3>{c.glossary}</h3><p>{item.glossary[locale]}</p><h3>{c.sourceLabel}</h3>
    <ScrollArea className="source-viewport" both id={`source-code-${item.id}`}><pre dir="ltr"><code>{item.source}</code></pre></ScrollArea>
    <a className="text-link" href={asset(`examples/${item.id}.noema`)} download>{c.download} ↓</a>
    <h3>{c.visibleTitle}</h3><p>{c.visibleIntro}</p><div className="declaration-list">{provenance.samples[item.id].declarations.map(d=><figure key={d.svg}><figcaption><code>{d.label}</code><span>{d.roots.join(' · ')}</span></figcaption><a href={asset(d.svg)} target="_blank" rel="noopener"><img className="ink" src={asset(d.svg)} alt={`${d.label} — ${ja?'語の宣言':'word declaration'}`} loading="lazy"/></a></figure>)}</div>
  </>;
}

export default function Details({selection,locale,relation,examples,onClose,returnFocus}) {
  const c=getContent(locale),dialog=useRef(null);
  const item=selection?.id===relation.id?relation:examples.find(e=>e.id===selection?.id);
  const title=selection?.kind==='word'?selection.entry.name:selection?.kind==='kant'?c.specimenDialog:item?.title[locale]??'';
  useEffect(()=>{
    if(selection&&!dialog.current.open)dialog.current.showModal();
    else if(!selection&&dialog.current.open)dialog.current.close();
    document.body.classList.toggle('dialog-open',!!selection);
    document.dispatchEvent(new CustomEvent('noema:dialog',{detail:{open:!!selection}}));
  },[selection]);
  useEffect(()=>()=>{document.body.classList.remove('dialog-open');document.dispatchEvent(new CustomEvent('noema:dialog',{detail:{open:false}}));},[]);
  return <dialog ref={dialog} id="detail-dialog" className="detail-dialog" aria-labelledby="dialog-title" onClose={()=>{onClose();returnFocus.current?.focus({preventScroll:true});}}
    onClick={e=>{const b=e.currentTarget.getBoundingClientRect();if(e.target===e.currentTarget&&(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom))dialog.current.close();}}>
    <div className="dialog-header"><h2 id="dialog-title">{title}</h2><button type="button" className="plus-button dialog-close" aria-label={c.close} onClick={()=>dialog.current.close()}><img src={asset('design/close.svg')} width="14" height="14" alt=""/></button></div>
    {selection&&<ScrollArea className="dialog-body" id="dialog-body" contain resetKey={selection.kind+':'+(selection.id??selection.entry?.name)}><div className="dialog-content">
      {selection.kind==='word'?<div dangerouslySetInnerHTML={{__html:entryDetailHTML(selection.entry,locale)}}/>:selection.kind==='kant'?<><div className="specimen-pages">{provenance.specimens.map((p,i)=><figure key={p.file}><figcaption>{locale==='ja'?'段落':'Paragraph'} {i+1}</figcaption><img className="ink" src={asset('glyphs/'+p.file)} alt={`${c.specimen} ${i+1}`}/></figure>)}</div><a className="text-link" href={docLink('docs/circle-writing-v2.md')}>{c.primitivesLink} ↗</a></>:item&&<Source item={item} locale={locale}/>}
    </div></ScrollArea>}
  </dialog>;
}
