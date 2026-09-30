import { useEffect, useId, useMemo, useRef, useState, type PointerEvent } from 'react';
import * as d3 from 'd3';
import type { Edge, GraphResponse } from '@histree/shared-types';
import { relationshipPresentation, fitGraph, focusGraph, isDoubleActivation, edgeCurve, edgeKey, edgeSubject, isDrag, sortedEvents, type GraphEntry, type GraphSelection, type Point } from '../../lib/graph';
import { entryTitle } from '../../lib/reading';
import { edgeTypeLabel, formatDisplayRange } from '../../lib/content';

type View = {x:number;y:number;k:number};
interface Props {
 data:GraphResponse; mode:'timeline'|'network'; selection:GraphSelection;
 onSelect:(selection:GraphSelection)=>void; onEnterSubgraph:(id:string)=>void; focusRequest:number; highlighted:Set<string> | null;
}
const W=900,H=760;
const eventLabel=(node:GraphEntry)=>node.type==='event'?formatDisplayRange(node.start_year,node.end_year):node.era || '人物';
function wrap(title:string) {const chars=Array.from(title);return [chars.slice(0,9).join(''),chars.slice(9,18).join(''),chars.length>18?chars.slice(18,26).join('')+(chars.length>26?'…':''):''].filter(Boolean);}
export function GraphCanvas({data,mode,selection,onSelect,onEnterSubgraph,focusRequest,highlighted}:Props) {
 const svg=useRef<SVGSVGElement>(null);
 const marker=useId().replace(/:/g,'');
 const [positions,setPositions]=useState<Record<string,Point>>({});
 const [moving,setMoving]=useState(false);
 const gesture=useRef<{id:number;start:Point;view:View;node?:string;target:GraphSelection;origin?:Point;dragged:boolean}|null>(null);
 const pendingClick=useRef<ReturnType<typeof setTimeout> | null>(null);
 const previousClick=useRef<{id:string;time:number;point:Point}|null>(null);
 const animation=useRef<number>(0);
 const camera=useRef<View>({x:0,y:0,k:1});
 function stopAnimation(){cancelAnimationFrame(animation.current);}
 function clearClick(){if(pendingClick.current)clearTimeout(pendingClick.current);pendingClick.current=null;previousClick.current=null;}
 useEffect(()=>()=>{clearClick();stopAnimation();},[]);
 const events=useMemo(()=>sortedEvents(data.nodes),[data.nodes]);
 const people=useMemo(()=>data.nodes.filter(n=>n.type==='person'),[data.nodes]);
 const layout=useMemo(()=>{
   if(mode==='timeline')return Object.fromEntries([
     ...people.map((p,i)=>[p.id,{x:100,y:245+i*94}]),
     ...events.map((e,i)=>[e.id,{x:325+i*220,y:112}]),
   ]);
   const nodes=data.nodes.map((n,i)=>({id:n.id,x:180+(i%4)*260,y:100+Math.floor(i/4)*160}));
   const simulation=d3.forceSimulation(nodes).stop()
     .force('charge',d3.forceManyBody().strength(data.nodes.length<=24?-600:-1400))
     .force('link',d3.forceLink(data.edges.map(e=>({source:e.source,target:e.target}))).id(n=>(n as {id:string}).id).distance(data.nodes.length<=24?190:265))
     .force('center',d3.forceCenter(W/2,H/2))
     .force('x',d3.forceX(W/2).strength(.12)).force('y',d3.forceY(H/2).strength(.14))
     .force('collide',d3.forceCollide(data.nodes.length<=24?90:105));
   simulation.tick(240);simulation.stop();
   return Object.fromEntries(nodes.map(n=>[n.id,{x:n.x,y:n.y}]));
 },[data,mode,people,events]);
 const [view,setView]=useState<View>(()=>mode==='timeline'?{x:20,y:10,k:1}:fitGraph(Object.values(layout)));
 useEffect(()=>{camera.current=view;},[view]);
 function animateTo(target:View) {
   stopAnimation();
   const initial=camera.current,start=performance.now();
   const duration=window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:360;
   const frame=(now:number)=>{
     const progress=duration?Math.min(1,(now-start)/duration):1, ease=1-Math.pow(1-progress,3);
     const next={x:initial.x+(target.x-initial.x)*ease,y:initial.y+(target.y-initial.y)*ease,k:initial.k+(target.k-initial.k)*ease};
     camera.current=next;setView(next);
     if(progress<1)animation.current=requestAnimationFrame(frame);
   };
   animation.current=requestAnimationFrame(frame);
 }
 // Selection changes move the camera; dragging positions does not retrigger this effect.
 useEffect(()=>{
   if(selection?.kind!=='node')return;
   const p=positions[selection.id]??layout[selection.id];if(!p)return;
   clearClick();animateTo(focusGraph(p,(svg.current?.getScreenCTM()?.a||1)*W));
   return stopAnimation;
   // Camera/positions are intentionally read only when a new focus is requested.
   // eslint-disable-next-line react-hooks/exhaustive-deps
 },[selection?.kind,selection?.id,focusRequest]);

 useEffect(()=>{
   const element=svg.current;if(!element)return;
   const wheel=(event:WheelEvent)=>{
     if(!event.ctrlKey&&!event.metaKey)return;
     event.preventDefault();stopAnimation();clearClick();const matrix=element.getScreenCTM();if(!matrix)return;
     const anchor=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());
     setView(v=>{const k=Math.max(.15,Math.min(3,v.k*Math.exp(-event.deltaY*.006)));return {x:anchor.x-(anchor.x-v.x)*k/v.k,y:anchor.y-(anchor.y-v.y)*k/v.k,k};});
   };
   element.addEventListener('wheel',wheel,{passive:false});
   return ()=>element.removeEventListener('wheel',wheel);
 },[]);
 const at=(id:string)=>positions[id] ?? layout[id];
 const point=(event:PointerEvent):Point=>({x:event.clientX,y:event.clientY});
 function ratio() {return 1/(svg.current?.getScreenCTM()?.a || 1);}
 function fit() {clearClick();animateTo(fitGraph(data.nodes.map(n=>at(n.id))));}
 function zoom(factor:number) {clearClick();stopAnimation();setView(v=>{const k=Math.max(.1,Math.min(3,v.k*factor));return {x:W/2-(W/2-v.x)*k/v.k,y:H/2-(H/2-v.y)*k/v.k,k};});}
 const graphHeight=Math.max(540,people.length*94+260);
 const graphWidth=Math.max(W,events.length*220+260);
 const nodeActive=(id:string)=>selection?.kind==='node'&&selection.id===id;
 const edgeActive=(edge:Edge)=>selection?.kind==='edge'&&selection.id===edgeKey(edge);
 const opacity=(id:string)=>!highlighted||highlighted.has(id)?1:.22;
 function start(event:PointerEvent<SVGSVGElement>) {
   if(event.button!==0 || gesture.current)return;
   stopAnimation();
   if(pendingClick.current){clearTimeout(pendingClick.current);pendingClick.current=null;}
   const el=event.target as Element;
   const node=el.closest('[data-node]')?.getAttribute('data-node') ?? undefined;
   const edge=el.closest('[data-edge]')?.getAttribute('data-edge');
   gesture.current={id:event.pointerId,start:point(event),view:{...view},node,target:node?{kind:'node',id:node}:edge?{kind:'edge',id:edge}:null,origin:node?at(node):undefined,dragged:false};
   event.currentTarget.setPointerCapture(event.pointerId);
 }
 function move(event:PointerEvent<SVGSVGElement>) {
   const g=gesture.current;if(!g||event.pointerId!==g.id)return;
   if(!g.dragged&&!isDrag(g.start,point(event)))return;
   g.dragged=true;clearClick();setMoving(true);
   const dx=(event.clientX-g.start.x)*ratio(),dy=(event.clientY-g.start.y)*ratio();
   if(g.node&&mode==='network'&&g.origin)setPositions(p=>({...p,[g.node!]:{x:g.origin!.x+dx/g.view.k,y:g.origin!.y+dy/g.view.k}}));
   else setView({...g.view,x:g.view.x+dx,y:g.view.y+dy});
 }
 function end(event:PointerEvent<SVGSVGElement>) {
   const g=gesture.current;if(!g||event.pointerId!==g.id)return;
   if(!g.dragged) {
     if(g.node) {
       const now=performance.now();
       if(isDoubleActivation(previousClick.current,g.node,now,point(event))) {clearClick();onEnterSubgraph(g.node);}
       else {
         clearClick();previousClick.current={id:g.node,time:now,point:point(event)};
         pendingClick.current=setTimeout(()=>{pendingClick.current=null;previousClick.current=null;onSelect(g.target);},320);
       }
     } else {clearClick();onSelect(g.target);}
   }
   gesture.current=null;setMoving(false);
   if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);
 }
 const keyboard=(event:React.KeyboardEvent,selection:GraphSelection)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();onSelect(selection);}};
 const validEdges=data.edges.filter(e=>at(e.source)&&at(e.target));
 return <div className="history-canvas">
   <div className="history-canvas-tools">
     <div className="flex gap-1"><button aria-label="放大图谱" onClick={()=>zoom(1.25)}>＋</button><button aria-label="缩小图谱" onClick={()=>zoom(.8)}>−</button><button onClick={fit}>适应全图</button><button onClick={()=>{clearClick();setPositions({});animateTo(fitGraph(Object.values(layout)));}}>恢复布局</button></div>
     <span className="text-xs text-stone-500">{mode==='timeline'?'事件依次排列，间距不代表时长':'单击聚焦 · 双击展开关系'} · {Math.round(view.k*100)}%</span>
   </div>
   <p className="text-xs text-stone-500 mb-2">人物关系箭头由 A 指向 B：A 是 B 的该关系；无箭头表示双方关系。选中连线可查看完整说明与出处。</p><div className="history-viewport"><svg ref={svg} viewBox={`0 0 ${W} ${H}`} aria-label={mode==='timeline'?'历史进程图谱':'人物与事件关系图谱'} data-scale={view.k.toFixed(3)} className={`history-graph ${moving?'is-moving':''}`} onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={()=>{gesture.current=null;clearClick();setMoving(false);}} onKeyDown={event=>{if(event.key==='Escape'){clearClick();onSelect(null);}}}>
     <defs><pattern id={`${marker}-grid`} width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#c7cdc7"/></pattern><marker id={marker} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="#7c8a85"/></marker></defs>
     <rect width={W} height={H} fill={`url(#${marker}-grid)`}/>
     <g transform={`translate(${view.x},${view.y}) scale(${view.k})`}>
       {mode==='timeline'&&<g pointerEvents="none" aria-hidden="true">
         <text x="18" y="28" className="graph-eyebrow">人物 / 参与记录</text>
         {events.map(e=><line key={e.id} x1={layout[e.id].x} x2={layout[e.id].x} y1="160" y2={graphHeight} stroke="#d9dfd7" strokeDasharray="3 6"/>)}
         {people.map((p,i)=><g key={p.id}><rect x="0" y={200+i*94} width={graphWidth} height="90" fill={i%2===0?'#e7ede73d':'transparent'}/><line x1="190" x2={graphWidth} y1={layout[p.id].y} y2={layout[p.id].y} stroke="#d5ded6"/></g>)}
       </g>}
       <g className="links">
       {validEdges.map((edge,index)=>{
         const active=edgeActive(edge),key=edgeKey(edge);
         const presentation=relationshipPresentation(edge,data.nodes,edgeTypeLabel(edge.type));
         const title=presentation.sentence;
         const dim=highlighted&&(!highlighted.has(edge.source)||!highlighted.has(edge.target));
         if(mode==='timeline') {
           if(edgeSubject(edge,data.nodes)!=='person_event')return null;
           const person=data.nodes.find(n=>n.id===edge.source)?.type==='person'?edge.source:edge.target;
           const event=person===edge.source?edge.target:edge.source;
           const siblings=validEdges.filter(e=>e.source===edge.source&&e.target===edge.target);
           const y=layout[person].y+(siblings.indexOf(edge)-(siblings.length-1)/2)*26;
           return <g key={key} data-edge={key} role="button" tabIndex={0} aria-label={`查看关系：${title}`} aria-pressed={active} opacity={dim ? .18 : 1} className="graph-relation-chip" transform={`translate(${layout[event].x},${y})`} onKeyDown={e=>keyboard(e,{kind:'edge',id:key})}>
             <title>{title}</title><rect x="-64" y="-17" width="128" height="34" rx="17" fill={active?'#276458':'#fffdf7'} stroke={active?'#163f35':'#afc2b7'} strokeWidth={active?2.5:1}/><text textAnchor="middle" y="5" fontSize="16" fill={active?'#fff':'#365f52'}>{edgeTypeLabel(edge.type).slice(0,7)}</text>
           </g>;
         }
         const siblings=validEdges.filter(e=>[e.source,e.target].sort().join('|')===[edge.source,edge.target].sort().join('|'));
         const bend=((siblings.indexOf(edge)-(siblings.length-1)/2)*65 + (index%2===0?18:-18)) * (edge.source < edge.target ? 1 : -1);
         const curve=edgeCurve(at(edge.source),at(edge.target),bend);
         return <g key={key} data-edge={key} role="button" tabIndex={0} aria-label={`查看关系：${title}`} aria-pressed={active} opacity={dim ? .18 : 1} className="graph-edge" onKeyDown={e=>keyboard(e,{kind:'edge',id:key})}>
           <title>{title}</title><path d={curve.path} className="edge-visible" stroke={active?'#ae7136':'#96a7a1'} strokeWidth={active?3.5:1.5} fill="none" markerEnd={presentation.symmetric ? undefined : `url(#${marker})`}/>
           <path d={curve.path} stroke="transparent" strokeWidth="20" fill="none" className="edge-hit"/>
           <rect x={curve.label.x-45} y={curve.label.y-12} width="90" height="24" rx="10" fill={active?'#ae7136':'#f8f7f0'}/><text x={curve.label.x} y={curve.label.y+4} textAnchor="middle" fontSize="14" fill={active?'white':'#5f7069'}>{edgeTypeLabel(edge.type).slice(0,8)}</text>
         </g>;
       })}</g>
       <g className="nodes">{data.nodes.map(node=>{
         const p=at(node.id);if(!p)return null;
         const active=nodeActive(node.id),person=node.type==='person',lines=wrap(entryTitle(node));
         return <g key={node.id} data-node={node.id} transform={`translate(${p.x},${p.y})`} role="button" tabIndex={0} aria-label={`查看${person?'人物':'事件'}：${entryTitle(node)}`} aria-pressed={active} opacity={opacity(node.id)} className="graph-node" onKeyDown={event=>{
           if(event.key==='Enter'&&event.shiftKey){event.preventDefault();clearClick();onEnterSubgraph(node.id);return;}
           clearClick();keyboard(event,{kind:'node',id:node.id});
           if(mode==='network'&&['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();setPositions(v=>({...v,[node.id]:{x:p.x+(event.key==='ArrowRight'?10:event.key==='ArrowLeft'?-10:0),y:p.y+(event.key==='ArrowDown'?10:event.key==='ArrowUp'?-10:0)}}));}
         }}>
           <title>{entryTitle(node)} · {eventLabel(node)}</title><rect x="-86" y="-38" width="172" height="76" rx={person?20:8} fill={active?'#e2eee5':'#fffdf7'} stroke={active?'#235b49':person?'#98b6a4':'#c7b08c'} strokeWidth={active?3:1.3}/>
           <rect x="-86" y="-16" width="4" height="32" rx="2" fill={person?'#59806e':'#b68a56'}/>
           <text x="-72" y="-22" className="graph-eyebrow">{person?'人物':eventLabel(node)}</text>
           {lines.map((line,i)=><text key={i} x="-72" y={-3+i*18} fontSize="16" fill="#263e34" fontWeight="600">{line}</text>)}
         </g>;
       })}</g>
     </g>
   </svg></div>
   <p className="px-4 py-2 text-xs text-stone-500 border-t border-stone-200">拖动空白处平移；＋ / − 或 Ctrl／⌘＋滚轮缩放。{mode==='timeline'?'时间布局固定；角色标签可点击查看关系。':'拖动节点在当前视图内保留位置；连线及其文字均可选中。'}双击节点进入子图；键盘 Enter 选择，Shift＋Enter 展开关系，Esc 取消。</p>
 </div>;
}
