import {useEffect,useRef,useState} from 'react';
import {filterEntries,labels} from '../dictionary-data.mjs';
import {asset,docLink} from '../site/web.mjs';
import {ScrollArea} from './ScrollArea';

function Select({name,label,choices,value,onChange}) {
  const [open,setOpen]=useState(false),root=useRef(null),button=useRef(null),menu=useRef(null);
  const selected=choices.find(c=>c[0]===value)?.[1]??choices[0][1];
  useEffect(()=>{const outside=e=>{if(!root.current?.contains(e.target))setOpen(false);};document.addEventListener('pointerdown',outside);return()=>document.removeEventListener('pointerdown',outside);},[]);
  const focus=index=>requestAnimationFrame(()=>menu.current?.children[index]?.focus());
  const show=index=>{setOpen(true);focus(index);};
  return <div className="custom-select" ref={root} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(false);}}
    onKeyDown={e=>{
      if(e.key==='Escape'){e.preventDefault();setOpen(false);button.current.focus();}
      else if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
        e.preventDefault();let i=[...menu.current.children].indexOf(document.activeElement);
        i=e.key==='Home'?0:e.key==='End'?choices.length-1:!open?(e.key==='ArrowUp'?choices.length-1:0):(i+(e.key==='ArrowDown'?1:-1)+choices.length)%choices.length;show(i);
      }
    }}>
    <label id={`${name}-label`}>{label}</label><button ref={button} type="button" className="select-trigger" aria-labelledby={`${name}-label ${name}-value`} aria-haspopup="listbox" aria-expanded={open} aria-controls={`${name}-options`}
      onClick={()=>open?setOpen(false):show(Math.max(0,choices.findIndex(c=>c[0]===value)))}><span id={`${name}-value`} data-select-label>{selected}</span><img src={asset('design/chevron-down.svg')} width="11" height="6" alt="" style={open?{transform:'none'}:undefined}/></button>
    <div ref={menu} className="select-menu" role="listbox" id={`${name}-options`} aria-labelledby={`${name}-label`} hidden={!open}>
      {choices.map(([key,text])=><button type="button" key={key} role="option" data-value={key} aria-selected={key===value} tabIndex={-1} onClick={()=>{onChange(key);setOpen(false);button.current.focus();}}><span>{text}</span><span className="select-check" aria-hidden="true">✓</span></button>)}
    </div>
  </div>;
}

export default function Dictionary({locale,initialEntries,counts,source,onOpen}) {
  const ja=locale==='ja',l=labels[locale],pageSize=60;
  const [entries,setEntries]=useState(initialEntries),[query,setQuery]=useState(''),[kind,setKind]=useState(''),[scope,setScope]=useState(''),[page,setPage]=useState(1),[ready,setReady]=useState(false),[error,setError]=useState(false);
  useEffect(()=>{
    const params=new URLSearchParams(location.search);setQuery(params.get('q')??'');setKind(params.get('kind')??'');setScope(params.get('scope')??'');setPage(Math.max(1,parseInt(params.get('page')??'1')||1));setReady(true);
  },[]);
  useEffect(()=>{const abort=new AbortController();fetch(asset('data/dictionary.json'),{signal:abort.signal}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json();}).then(d=>{setEntries(d.entries.sort((a,b)=>a.name.localeCompare(b.name,'en')));setError(false);}).catch(e=>{if(e.name!=='AbortError')setError(true);});return()=>abort.abort();},[]);
  useEffect(()=>{if(!ready)return;const p=new URLSearchParams(location.search);for(const [key,value] of [['q',query.trim()],['kind',kind],['scope',scope],['page',page>1?String(page):'']])value?p.set(key,value):p.delete(key);history.replaceState(null,'',`${location.pathname}${p.size?'?'+p:''}${location.hash}`);},[query,kind,scope,page,ready]);
  const filtered=filterEntries(entries,{query,kind,scope}),pages=Math.max(1,Math.ceil(filtered.length/pageSize)),current=Math.min(page,pages),start=(current-1)*pageSize;
  const numbers=[...new Set([1,2,current-1,current,current+1,pages-1,pages])].filter(n=>n>=1&&n<=pages).sort((a,b)=>a-b);
  const reset=()=>{setQuery('');setKind('');setScope('');setPage(1);};
  return <div className="dictionary-panel" data-dictionary={asset('data/dictionary.json')}>
    <div className="catalog-breakdown"><span><strong>1,489</strong> {l.primitive}</span><span><strong>463</strong> {l.definition}</span><span><strong>27</strong> {l['source-selector']} {ja?'を含む':'included'}</span></div>
    <form className="dictionary-controls" role="search" onSubmit={e=>e.preventDefault()}>
      <div className="search-field"><label htmlFor="dictionary-query">{ja?'語名・語義・綴りで検索':'Search name, Japanese meaning, or spelling'}</label><input id="dictionary-query" name="q" type="text" inputMode="search" autoComplete="off" value={query} placeholder={ja?'例：above、信念、年齢':'e.g. above, belief, 信念'} onChange={e=>{setQuery(e.target.value);setPage(1);}}/></div>
      <Select name="dictionary-kind" label={ja?'構成':'Kind'} choices={[[ '',ja?'すべて':'All'],...['primitive','definition'].map(k=>[k,l[k]])]} value={kind} onChange={value=>{setKind(value);setPage(1);}}/>
      <Select name="dictionary-scope" label={ja?'利用範囲':'Scope'} choices={[[ '',ja?'すべて':'All'],...Object.keys(counts.portability).map(k=>[k,l[k]])]} value={scope} onChange={value=>{setScope(value);setPage(1);}}/>
    </form>
    <div className="dictionary-status-row"><p className="caption" data-dictionary-status role="status" aria-live="polite">{error?(ja?'辞書を読み込めませんでした。原典をご覧ください。':'Could not load the dictionary. See the source below.'):filtered.length?(ja?`${filtered.length.toLocaleString()}件中 ${start+1}–${Math.min(start+pageSize,filtered.length)}件`:`${start+1}–${Math.min(start+pageSize,filtered.length)} of ${filtered.length.toLocaleString()} entries`):(ja?'0件':'0 entries')}</p><button type="button" className="reset-search" onClick={reset}>{ja?'クリア':'Clear'}</button></div>
    <ScrollArea className="dictionary-viewport" id="dictionary-results" label={ja?'辞書の検索結果':'Dictionary results'} resetKey={`${query}|${kind}|${scope}|${current}`}>
      <div className="dictionary-results">{filtered.slice(start,start+pageSize).map(entry=><button type="button" className="dictionary-entry" id={`word-${entry.name}`} data-word={entry.name} key={entry.name} aria-haspopup="dialog" onClick={e=>onOpen({kind:'word',entry},e.currentTarget)}>
        <span className="word-name">{entry.name}</span><span className="word-spelling">{entry.spelling.join(' · ')}</span><span className="word-meaning" lang="ja">{entry.meaning}</span>
      </button>)}</div>{!filtered.length&&<p className="dictionary-empty">{ja?'該当する項目はありません。語句や条件を変えて検索してください。':'No matching entries. Try another term or filter.'}</p>}
    </ScrollArea>
    {filtered.length>pageSize&&<nav className="dictionary-pagination" aria-label={ja?'辞書のページ切替':'Dictionary pages'}><button data-page="previous" disabled={current===1} onClick={()=>setPage(current-1)}>← {ja?'前へ':'Previous'}</button><div data-page-numbers>{numbers.map((n,i)=><span key={n}>{i>0&&n-numbers[i-1]>1&&<span aria-hidden="true">… </span>}<button data-page={n} aria-current={n===current?'page':undefined} onClick={()=>setPage(n)}>{n}</button></span>)}</div><button data-page="next" disabled={current===pages} onClick={()=>setPage(current+1)}>{ja?'次へ':'Next'} →</button></nav>}
    <a className="text-link dictionary-source" href={docLink(source)}>{ja?'定義の本文を含む原典':'Source catalogue with full definitions'} ↗</a>
  </div>;
}
