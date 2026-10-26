import { useEffect, useMemo, useState } from "react";
import { visibleScrollTiles, type ScrollPanel } from "../lib/scrollTiles";
const decoded = new Set<string>();
const queued = new Set<string>();
let prefetching=0;
const waiting: Array<()=>void> = [];
const url = (file:string,retry=0) => `${import.meta.env.BASE_URL}timeline-scroll/${file}${retry?`?retry=${retry}`:''}`;
function prefetch(file:string,isCancelled:()=>boolean) {
  if(decoded.has(file)||queued.has(file))return;
  queued.add(file);
  const run=()=>{
    if(isCancelled()){queued.delete(file);waiting.shift()?.();return;}
    prefetching++;
    const image=new Image();image.fetchPriority='low';
    const done=(success:boolean)=>{if(success)decoded.add(file);queued.delete(file);prefetching--;waiting.shift()?.();};
    image.onload=()=>done(true);image.onerror=()=>done(false);image.src=url(file);
  };
  if(prefetching<2)run();else waiting.push(run);
}
export function ScrollPanelTiles({panel,next,from,to,scale,mask}: {
  panel:ScrollPanel;next?:ScrollPanel;from:number;to:number;scale:number;mask?:string;
}) {
  const {atlas,visible,adjacent}=useMemo(()=>visibleScrollTiles(panel,from,to,next),[panel,from,to,next]);
  const [ready,setReady]=useState<Set<string>>(()=>new Set());
  const [failed,setFailed]=useState<Set<string>>(()=>new Set());
  const [retry,setRetry]=useState(0);
  const [high,setHigh]=useState(false);
  const key=visible.map(tile=>tile.low.file).join('|');
  const lowReady=visible.every(tile=>ready.has(tile.low.file)||decoded.has(tile.low.file));
  const needsHigh=scale*Math.min(window.devicePixelRatio||1,2)>.5;
  useEffect(()=>{
    const timer=window.setTimeout(()=>setHigh(needsHigh),350);
    return()=>window.clearTimeout(timer);
  },[key,needsHigh]);
  useEffect(()=>{
    if(!lowReady||!visible.length)return;
    let cancelled=false;
    const timer=window.setTimeout(()=>adjacent.forEach(tile=>prefetch(tile.low.file,()=>cancelled)),400);
    return()=>{cancelled=true;window.clearTimeout(timer);};
  },[key,lowReady,adjacent,visible.length]);
  const loaded=(file:string)=>{
    decoded.add(file);
    setReady(previous=>previous.has(file)?previous:new Set([...previous,file]));
    setFailed(previous=>{if(!previous.has(file))return previous;const result=new Set(previous);result.delete(file);return result;});
  };
  const failure=(file:string)=>setFailed(previous=>previous.has(file)?previous:new Set([...previous,file]));
  if(!visible.length)return null;
  const retryFailed=()=>{setFailed(new Set());setRetry(value=>value+1);};
  return <g mask={mask} data-scroll-tile-panel={panel.id} data-visible-tiles={visible.length} data-low-ready={lowReady}>
    <image href={url(atlas.preview.file)} x={panel.crop.x} y={panel.crop.y} width={panel.crop.width} height={panel.crop.height} preserveAspectRatio="none" data-tile-level="preview"/>
    {visible.map(tile=><g key={tile.content_x}>
      <image href={url(tile.low.file,retry)} x={tile.x} y={tile.y} width={tile.width} height={tile.height} preserveAspectRatio="none"
        data-tile-level="low" data-loaded={ready.has(tile.low.file)||decoded.has(tile.low.file)} onLoad={()=>loaded(tile.low.file)} onError={()=>failure(tile.low.file)}/>
      {high&&needsHigh&&lowReady&&<image href={url(tile.high.file,retry)} x={tile.x} y={tile.y} width={tile.width} height={tile.height} preserveAspectRatio="none"
        opacity={ready.has(tile.high.file)||decoded.has(tile.high.file)?1:0} data-tile-level="high" data-loaded={ready.has(tile.high.file)||decoded.has(tile.high.file)}
        onLoad={()=>loaded(tile.high.file)} onError={()=>failure(tile.high.file)}/>}
    </g>)}
    {visible.some(tile=>failed.has(tile.low.file)||failed.has(tile.high.file))&&<g role="button" tabIndex={0} aria-label="重新加载画卷细节" style={{cursor:'pointer',pointerEvents:'all'}}
      onClick={event=>{event.stopPropagation();retryFailed();}} onKeyDown={event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();retryFailed();}}}>
      <rect x={panel.crop.x+12} y={panel.crop.y+12} width="290" height="34" rx="5" fill="#faf8ed"/>
      <text x={panel.crop.x+24} y={panel.crop.y+35} fill="#665b42" fontSize="17">画面细节未载入，点此重试</text>
    </g>}
  </g>;
}
