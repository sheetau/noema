import {useEffect,useRef} from 'react';
import {asset} from '../site/web.mjs';
import provenance from '../../public/glyphs/provenance.json';

export default function RootMarquee({locale}) {
  const viewport=useRef(null),belt=useRef(null),track=useRef(null),offset=useRef(0),drag=useRef(null),width=useRef(1);
  const paint=()=>{offset.current=((offset.current%width.current)+width.current)%width.current;belt.current.style.transform=`translate3d(${-offset.current}px,0,0)`;};
  useEffect(()=>{
    let frame,previous=0;const reduced=matchMedia('(prefers-reduced-motion: reduce)');
    const measure=()=>{width.current=track.current.offsetWidth||1;paint();};
    const observer=new ResizeObserver(measure);observer.observe(track.current);measure();
    const tick=time=>{if(previous&&!drag.current&&!reduced.matches&&!document.hidden){offset.current+=30*Math.min(time-previous,64)/1000;paint();}previous=time;frame=requestAnimationFrame(tick);};
    frame=requestAnimationFrame(tick);return()=>{cancelAnimationFrame(frame);observer.disconnect();};
  },[]);
  const release=()=>{drag.current=null;viewport.current.classList.remove('is-dragging');};
  return <div ref={viewport} className="root-marquee" tabIndex={0} role="region" aria-label={locale==='ja'?'30の語根。ドラッグまたは左右キーで移動できます。':'Thirty roots. Drag or use the arrow keys to move.'}
    onPointerDown={e=>{if(!e.isPrimary||e.button!==0)return;drag.current={id:e.pointerId,x:e.clientX};e.currentTarget.setPointerCapture(e.pointerId);e.currentTarget.classList.add('is-dragging');}}
    onPointerMove={e=>{if(drag.current?.id===e.pointerId){offset.current+=drag.current.x-e.clientX;drag.current.x=e.clientX;paint();}}}
    onPointerUp={release} onPointerCancel={release} onLostPointerCapture={release} onDragStart={e=>e.preventDefault()}
    onKeyDown={e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();offset.current+=e.key==='ArrowRight'?148:-148;paint();}}}>
    <div className="root-belt" ref={belt}>{[false,true].map(copy=><div key={String(copy)} ref={copy?null:track} className="root-track" aria-hidden={copy||undefined}>{provenance.alphabet.map(root=><figure key={root.name}><img className="ink" src={asset(`glyphs/roots/${root.name}.svg`)} width="140" height="140" alt={copy?'':root.name} draggable="false"/><figcaption>{root.name}</figcaption></figure>)}</div>)}</div>
  </div>;
}
