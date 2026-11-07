import {forwardRef, useEffect, useRef, useState, useImperativeHandle} from 'react';
import Lenis from 'lenis';

const options = {autoRaf:true, lerp:0.1, smoothWheel:true, syncTouch:false, respectReducedMotion:true};

function Thumb({target, horizontal=false, page=false, controls}) {
  const [metrics, setMetrics] = useState(null);
  const drag = useRef(null);
  useEffect(() => {
    const el = page ? document.documentElement : target.current;
    if (!el) return;
    let raf;
    const measure = () => {
      const view = horizontal ? el.clientWidth : (page ? innerHeight : el.clientHeight);
      const total = horizontal ? el.scrollWidth : el.scrollHeight;
      const position = horizontal ? el.scrollLeft : (page ? scrollY : el.scrollTop);
      const max = Math.max(0,total-view), length = Math.max(24,view*view/Math.max(view,total));
      setMetrics({max,view,length,position,offset:max ? position/max*(view-length) : 0});
    };
    const update = () => {cancelAnimationFrame(raf);raf=requestAnimationFrame(measure);};
    const observer = new ResizeObserver(update);
    observer.observe(el);if(el.firstElementChild)observer.observe(el.firstElementChild);
    const mutations = new MutationObserver(update);mutations.observe(el,{childList:true,subtree:true});
    const source=page?window:el;source.addEventListener('scroll',update,{passive:true});
    window.addEventListener('resize',update);measure();
    return ()=>{cancelAnimationFrame(raf);observer.disconnect();mutations.disconnect();source.removeEventListener('scroll',update);window.removeEventListener('resize',update);};
  },[target,horizontal,page]);
  const move = value => {
    const el=page?document.documentElement:target.current;
    el.dispatchEvent(new CustomEvent('noema:scroll-drag',{detail:{value,horizontal}}));
  };
  if(!metrics?.max)return null;
  const {length,offset,max,view,position}=metrics;
  return <div className={`scroll-thumb ${horizontal?'horizontal':'vertical'} ${page?'page-thumb':''}`}
    role="scrollbar" tabIndex={0} aria-label={horizontal?'Horizontal scroll':'Vertical scroll'} aria-orientation={horizontal?'horizontal':'vertical'} aria-controls={controls}
    aria-valuemin={0} aria-valuemax={Math.round(max)} aria-valuenow={Math.round(position)}
    style={horizontal?{width:length,transform:`translateX(${offset}px)`}:{height:length,transform:`translateY(${offset}px)`}}
    onPointerDown={event=>{event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);drag.current={start:horizontal?event.clientX:event.clientY,position};}}
    onPointerMove={event=>{if(drag.current)move(Math.min(max,Math.max(0,drag.current.position+((horizontal?event.clientX:event.clientY)-drag.current.start)*max/(view-length))));}}
    onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}}
    onKeyDown={event=>{const keys={ArrowDown:40,ArrowRight:40,ArrowUp:-40,ArrowLeft:-40,PageDown:view,PageUp:-view};if(event.key in keys||['Home','End'].includes(event.key)){event.preventDefault();move(event.key==='Home'?0:event.key==='End'?max:Math.min(max,Math.max(0,position+keys[event.key])));}}}/>;
}

export function PageScroll({children}) {
  useEffect(()=>{
    const scroll = new Lenis({...options,anchors:true,stopInertiaOnNavigate:true,virtualScroll:({event})=>!event.shiftKey});
    const modal=event=>event.detail.open?scroll.stop():scroll.start();
    const drag=event=>scroll.scrollTo(event.detail.value,{immediate:true,force:true});
    document.addEventListener('noema:dialog',modal);document.documentElement.addEventListener('noema:scroll-drag',drag);
    if(document.querySelector('dialog[open]'))scroll.stop();
    return()=>{document.removeEventListener('noema:dialog',modal);document.documentElement.removeEventListener('noema:scroll-drag',drag);scroll.destroy();};
  },[]);
  return <>{children}<Thumb page controls="__next"/></>;
}

export const ScrollArea = forwardRef(function ScrollArea({children,className='',id,label,contain=false,both=false,resetKey}, forwardedRef) {
  const viewport=useRef(null), content=useRef(null), instances=useRef([]), previousReset=useRef(resetKey);
  useImperativeHandle(forwardedRef,()=>viewport.current);
  useEffect(()=>{
    const create=horizontal=>new Lenis({...options,wrapper:viewport.current,content:content.current,naiveDimensions:true,
      orientation:horizontal?'horizontal':'vertical',gestureOrientation:horizontal?'horizontal':'vertical',overscroll:!contain,
      virtualScroll:data=>{
        if(horizontal){if(data.event.shiftKey&&!data.deltaX)data.deltaX=data.deltaY;return Math.abs(data.deltaX)>Math.abs(data.event.shiftKey?0:data.deltaY);}
        return !data.event.shiftKey&&Math.abs(data.deltaY)>=Math.abs(data.deltaX);
      }});
    const scrolls=[create(false),...(both?[create(true)]:[])];instances.current=scrolls;
    const drag=event=>scrolls[event.detail.horizontal?1:0]?.scrollTo(event.detail.value,{immediate:true,force:true});
    const el=viewport.current;el.addEventListener('noema:scroll-drag',drag);
    return()=>{el.removeEventListener('noema:scroll-drag',drag);scrolls.forEach(s=>s.destroy());};
  },[contain,both]);
  useEffect(()=>{if(previousReset.current===resetKey)return;previousReset.current=resetKey;instances.current.forEach(s=>{s.resize();s.scrollTo(0,{immediate:true,force:true});});},[resetKey]);
  return <div className={`scroll-shell ${className}-shell`}><div ref={viewport} id={id} className={className} tabIndex={0} role={label?'region':undefined} aria-label={label}>
    <div ref={content} className="scroll-content">{children}</div>
  </div><Thumb target={viewport} controls={id}/>{both&&<Thumb target={viewport} horizontal controls={id}/>}</div>;
});
