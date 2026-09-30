import { useCallback, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { GraphResponse, Edge, Person, Event } from '@histree/shared-types';
import { GraphCanvas } from '../components/graph/GraphCanvas';
import { GraphSearch } from '../components/graph/GraphSearch';
import { useDebounced } from '../hooks/useDebounced';
import { Evidence, LoadState } from '../components/Reading';
import { useResource } from '../hooks/useResource';
import { entryPath, entryTitle } from '../lib/reading';
import { edgeTypeLabel, formatDisplayRange } from '../lib/content';
import { relationshipPresentation, enterSubgraph, edgeKey, edgeSubject, neighborhood, type GraphViewMode, type GraphSelection } from '../lib/graph';

const EMPTY_GRAPH: GraphResponse = { center: { id: '', name: '', type: 'person' }, nodes: [], edges: [] };
export function GraphPage() {
 const {id}=useParams<{id:string}>();
 const entry=useResource<Person|Event>(id?`/entry/${id}`:undefined);
 return <div className="space-y-6"><header className="explore-heading"><p className="eyebrow">关系探索</p><h1>沿着人物，走进历史</h1><p>从当前条目出发，双击相邻节点继续探索。</p></header>{entry.loading||entry.error?<LoadState {...entry}/>:<GraphView key={id} initialId={id} initialMode={entry.data?.type==='event'?'events':'people'}/>}</div>;
}
export function GraphView({initialId,initialMode='people'}:{initialId?:string;initialMode?:GraphViewMode}) {
 return <GraphExplorer initialId={initialId} initialMode={initialMode}/>;
}
function GraphExplorer({initialId,initialMode}:{initialId?:string;initialMode:GraphViewMode}) {
 const [mode,setMode]=useState<GraphViewMode>(initialMode);
 const [selection,setSelection]=useState<GraphSelection>(initialId?{kind:'node',id:initialId}:null);
 const [history,setHistory]=useState<string[]>(initialId?[initialId]:[]);
 const [labels,setLabels]=useState<Record<string,string>>({});
 const focus=history.at(-1)||'';
 const [focusRequest,setFocusRequest]=useState(0);
 const [depth,setDepth]=useState(1);
 const [from,setFrom]=useState('');
 const [to,setTo]=useState('');
 const [evidence,setEvidence]=useState(false);
 const [listOpen,setListOpen]=useState(false);
 const [listLimit,setListLimit]=useState(50);
 const settledRange=useDebounced(`${from}|${to}`);
 const [rangeFrom,rangeTo]=settledRange.split('|');
 const invalidRange=mode==='events'&&from!==''&&to!==''&&Number(from)>Number(to);
 const invalidSettledRange=mode==='events'&&rangeFrom!==''&&rangeTo!==''&&Number(rangeFrom)>Number(rangeTo);
 const params=new URLSearchParams({mode,depth:String(depth)});
 if(mode==='events'&&rangeFrom!=='')params.set('from',rangeFrom);
 if(mode==='events'&&rangeTo!=='')params.set('to',rangeTo);
 const result=useResource<GraphResponse>(focus&&!invalidSettledRange?`/graph-slice/${focus}?${params}`:undefined);
 const data=result.data??EMPTY_GRAPH;
 const detail=useResource<Person|Event>(selection?.kind==='node'?`/entry/${selection.id}`:undefined);
 const base=data;
 const filtered=invalidRange?EMPTY_GRAPH:data;
 const nodeIndex=useMemo(()=>new Map(data.nodes.map(n=>[n.id,n])),[data.nodes]);
 const selectedNode=selection?.kind==='node'?(detail.data??nodeIndex.get(selection.id)):undefined;
 const selectedEdge=selection?.kind==='edge'?data.edges.find(e=>edgeKey(e)===selection.id):undefined;
 const select=useCallback((next:GraphSelection)=>{setSelection(next);setEvidence(false);setFocusRequest(v=>v+1);},[]);
 const dive=useCallback((id:string)=>{setHistory(h=>enterSubgraph(h,id));setDepth(1);select({kind:'node',id});setLabels(l=>({...l,[focus]:nodeIndex.has(focus)?entryTitle(nodeIndex.get(focus)!):l[focus]??'条目',[id]:nodeIndex.has(id)?entryTitle(nodeIndex.get(id)!):l[id]??'条目'}));},[nodeIndex,focus,select]);
 function navigate(index:number){const next=history.slice(0,index+1);setHistory(next);setDepth(1);select(next.length?{kind:'node',id:next.at(-1)!}:null);}
 function reset(){setFrom('');setTo('');setHistory([]);setDepth(1);select(null);}
 const highlighted=useMemo(()=>selectedNode?neighborhood(filtered,selectedNode.id,1):selectedEdge?new Set([selectedEdge.source,selectedEdge.target]):null,[filtered,selectedNode,selectedEdge]);
 const title=(id:string)=>{const n=nodeIndex.get(id);return n?entryTitle(n):labels[id]??'条目';};
 const edgeTitle=(e:Edge)=>relationshipPresentation(e,data.nodes,edgeTypeLabel(e.type),selectedNode?.id).sentence;
 const visibleIds=new Set(filtered.nodes.map(n=>n.id));
 const selectedHidden=!result.loading&&(selectedNode&&!visibleIds.has(selectedNode.id)||selectedEdge&&!filtered.edges.some(e=>edgeKey(e)===edgeKey(selectedEdge)));
 const adjacent=selectedNode?base.edges.filter(e=>e.source===selectedNode.id||e.target===selectedNode.id):[];
 const button='rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm';
 function switchMode(next:GraphViewMode) {setMode(next);setDepth(1);select(focus?{kind:'node',id:focus}:null);}
 return <section className="graph-workspace space-y-3" aria-label="历史图谱工作区">
   <div className="graph-toolbar">
     <div className="inline-flex rounded-xl bg-[#e8ede6] p-1" aria-label="图谱视图">
       <button aria-pressed={mode==='people'} className={`graph-mode ${mode==='people'?'is-active':''}`} onClick={()=>switchMode('people')}>人物关系</button>
       <button aria-pressed={mode==='events'} className={`graph-mode ${mode==='events'?'is-active':''}`} onClick={()=>switchMode('events')}>人物与事件</button>
     </div>
     <p className="graph-count"><strong>{filtered.nodes.length}</strong> 个条目 · {filtered.edges.length} 条{mode==='people'?'人物':'参与'}关系</p>
   </div>
   <GraphSearch peopleOnly={mode==='people'} browse={!focus} onOpen={n=>{setMode(n.type==='event'?'events':mode);setHistory([n.id]);setLabels(l=>({...l,[n.id]:entryTitle(n)}));setDepth(1);setFrom('');setTo('');select({kind:'node',id:n.id});}}/>
   <div className="graph-filters">
     {mode==='events'&&<><label className="text-sm">事件起始年<input aria-label="图谱起始年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={from} onChange={e=>setFrom(e.target.value)}/></label>
     <label className="text-sm">事件结束年<input aria-label="图谱结束年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={to} onChange={e=>setTo(e.target.value)}/></label></>}
     <button className={button} onClick={reset}>重置筛选</button>
   </div>
   {invalidRange&&<p role="alert" className="text-rose-700">起始年不能晚于结束年。</p>}
   <div className="graph-context">
     <nav className="graph-breadcrumbs" aria-label="子图探索路径">
       <button onClick={()=>navigate(-1)} aria-current={!focus?'page':undefined}>查找条目</button>
       {history.map((id,i)=><span key={`${id}-${i}`}><span aria-hidden="true"> / </span><button aria-current={i===history.length-1?'page':undefined} onClick={()=>navigate(i)}>{title(id)}</button></span>)}
     </nav>
     {focus?<div className="flex flex-wrap items-center gap-2"><button className={button} onClick={()=>navigate(history.length-2)}>← 返回上一级</button><button className={button} onClick={()=>setDepth(depth===1?2:1)}>{depth===1?'展开两层关系':'只看直接关系'}</button><button className={button} onClick={()=>navigate(-1)}>返回查找</button></div>:<span className="text-xs text-stone-500">单击聚焦 · 双击进入子图 · 拖动自由布局</span>}
   </div>

   <LoadState {...result}/>
   {data.truncated&&<p role="status" className="text-sm text-amber-800">当前子图最多展示 {data.node_limit} 个条目、{data.edge_limit} 条关系，尚有关系未展开。可搜索其他条目或双击节点继续探索。</p>}
   {!focus&&<p className="reading-card">搜索或选择上方条目，查看它的直接关系；再逐层展开。</p>}
   <div className="graph-columns">
     <div className="min-w-0">
       {mode==='people'&&<p className="mb-3 text-xs leading-6 text-stone-500">关系读法：甲 —父亲→ 乙，表示甲是乙的父亲。兄弟、姻亲等对称关系使用无箭头连线；点击关系可查看说明与出处。</p>}
       {filtered.nodes.length?<GraphCanvas key={`${mode}:${focus}:${depth}:${settledRange}`} data={filtered} mode="network" selection={selection} onSelect={select} onEnterSubgraph={dive} focusRequest={focusRequest} highlighted={highlighted}/>:<p className="reading-card py-20 text-center">当前没有可展示的关系或条目。请选择条目或调整筛选。</p>}
       {selection&&<a href="#graph-details" className="xl:hidden block text-center rounded-lg bg-teal-50 p-3 mt-3 text-sm text-teal-800">查看选中内容的详情 ↓</a>}
       <details onToggle={e=>setListOpen(e.currentTarget.open)} className="mt-3 rounded-xl border border-stone-200 bg-white p-4"><summary className="text-sm">关系清单 · {filtered.edges.length} 条（也可在这里选择）</summary><div className="max-h-64 overflow-auto mt-3 space-y-2">{listOpen&&filtered.edges.slice(0,listLimit).map(e=><button key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})} className={`block w-full text-left rounded-lg p-3 text-sm ${selectedEdge&&edgeKey(selectedEdge)===edgeKey(e)?'bg-teal-100':'bg-stone-50'}`}>{edgeTitle(e)}</button>)}{listOpen&&filtered.edges.length>listLimit&&<button className={button} onClick={()=>setListLimit(v=>v+50)}>再显示 50 条</button>}</div></details>
     </div>
     <aside id="graph-details" className="graph-detail" aria-label="图谱详情" aria-live="polite">
       <div className="flex justify-between items-center"><p className="eyebrow">{selectedEdge?'关系详情':selectedNode?.type==='person'?'人物详情':selectedNode?'事件详情':'阅读图谱'}</p>{selection&&<button className="text-sm text-stone-500" onClick={()=>select(null)}>取消选择</button>}</div>
       {selectedHidden&&<p className="text-xs text-amber-800 mt-3">当前筛选未展示此项，详情仍保留。调整筛选或重新展开可查看此项。</p>}
       {selection?.kind==='node'&&<LoadState {...detail}/>}
       {selectedNode?<>
         <div className="detail-monogram" aria-hidden="true">{entryTitle(selectedNode).slice(0,1)}</div><h2 className="font-serif text-2xl leading-9 mt-4">{entryTitle(selectedNode)}</h2>
         <p className="text-sm text-stone-500 mt-2">{selectedNode.type==='event'?formatDisplayRange(selectedNode.start_year,selectedNode.end_year):selectedNode.era||'时代待补充'}</p>
         <p className="text-sm leading-7 mt-4">{selectedNode.description||'条目说明尚待整理。'}</p>
         <div className="flex flex-wrap gap-2 mt-5"><button className={button} onClick={()=>dive(selectedNode.id)}>进入关系子图</button><Link className="rounded-lg bg-[#285747] px-3 py-2 text-sm text-white" to={entryPath(selectedNode)}>阅读全文与出处 →</Link><Link className={button} to={`/ask?kind=${selectedNode.type}&id=${selectedNode.id}`}>问史料</Link></div>
         {selectedNode.type==='event'&&selectedNode.phases?.map((p,i)=><div key={i} className="border-l-2 border-stone-300 pl-3 mt-4 text-sm"><strong>{p.title}</strong><p className="leading-7 mt-1">{p.description}</p></div>)}
         <h3 className="text-sm font-semibold mt-6 mb-2">当前子图关系 · {adjacent.length}</h3>
         <div className="space-y-2">{adjacent.length===0&&<p className="text-sm text-stone-500 leading-7">当前子图没有展示此条目的关系。可进入它的关系子图或切换视图继续查看。</p>}{adjacent.map(e=><button className="block w-full text-left text-sm p-3 bg-stone-50 rounded-lg hover:bg-teal-50" key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})}>{edgeTitle(e)}</button>)}</div>
       </>:selectedEdge?<>
         <div className="mt-4 space-y-3"><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.source})}>{title(selectedEdge.source)}</button><p className="text-sm text-stone-500">{relationshipPresentation(selectedEdge,data.nodes,edgeTypeLabel(selectedEdge.type)).symmetric ? "—" : "↓"} {edgeTypeLabel(selectedEdge.type)}</p><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.target})}>{title(selectedEdge.target)}</button></div>
         <p className="mt-4 font-medium">{relationshipPresentation(selectedEdge,data.nodes,edgeTypeLabel(selectedEdge.type)).sentence}</p><p className="text-sm leading-7 mt-5">{selectedEdge.description || (edgeSubject(selectedEdge,data.nodes)==='person_event'?`当前记录的事件角色为“${edgeTypeLabel(selectedEdge.type)}”，具体依据见下方史料。`:'该关系已记录，进一步说明尚待整理。')}</p>
         <p className="text-xs leading-6 text-stone-500 mt-3">{edgeSubject(selectedEdge,data.nodes)==='person_event'?(()=>{const e=data.nodes.find(n=>(n.id===selectedEdge.source||n.id===selectedEdge.target)&&n.type==='event');return e?.type==='event'?`关联事件：${formatDisplayRange(e.start_year,e.end_year)}`:'';})():'关系有效起止时间尚未单独整理。'}</p>
       </>:<><h2 className="font-serif text-2xl mt-4">从一位人物开始</h2><p className="text-sm leading-7 mt-4">选中人物，画布会自动移到他的位置，并放大到便于阅读的大小。关系线也可以点击，查看双方身份与史料依据。</p><p className="text-sm leading-7 mt-3">双击节点，只看他与相邻人物或事件的子图。可以继续双击探索，或通过上方路径返回。</p></>}
       {(selectedNode||selectedEdge)&&<div className="border-t border-stone-200 mt-6 pt-4"><button className="text-sm text-teal-800 underline" aria-expanded={evidence} onClick={()=>setEvidence(!evidence)}>{evidence?'收起史料依据':'查看史料依据'}</button>{evidence&&(selectedNode?<Evidence key={selectedNode.id} subject={selectedNode.type} id={selectedNode.id}/>:selectedEdge?.id?<Evidence key={edgeKey(selectedEdge)} subject={edgeSubject(selectedEdge,data.nodes)} id={selectedEdge.id}/>:<p className="text-sm mt-3">这条关系的独立出处尚待整理。</p>)}</div>}
       {initialId&&<Link to="/graph" className="block text-sm underline text-teal-700 mt-6">查找其他人物与事件 →</Link>}
     </aside>
   </div>
 </section>;
}
