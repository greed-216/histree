import { useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { GraphResponse, Edge, Person, Event, RelationshipBundle } from '@histree/shared-types';
import { GraphCanvas } from '../components/graph/GraphCanvas';
import { Evidence } from '../components/Reading';
import { useResource } from '../hooks/useResource';
import { entryPath, entryTitle } from '../lib/reading';
import { edgeTypeLabel, formatDisplayRange } from '../lib/content';
import { enterSubgraph, edgeKey, edgeSubject, neighborhood, graphForView, type GraphViewMode, type GraphSelection } from '../lib/graph';

export function GraphPage() {
 const {id}=useParams<{id:string}>();
 const people=useResource<Person[]>('/people'),events=useResource<Event[]>('/event'),relationships=useResource<RelationshipBundle>('/relationships');
 const data=useMemo(()=>{
   if(!people.data||!events.data||!relationships.data)return undefined;
   const nodes=[...people.data,...events.data],center=nodes.find(n=>n.id===id);if(!center)return undefined;
   const r=relationships.data;
   return {center,nodes,edges:[
     ...r.person_relationships.map(e=>({id:e.id,subject_table:'person_relationship' as const,source:e.person_a,target:e.person_b,type:e.relation_type,description:e.description})),
     ...r.person_events.map(e=>({id:e.id,subject_table:'person_event' as const,source:e.person_id,target:e.event_id,type:e.role})),
   ]};
 },[people.data,events.data,relationships.data,id]);
 return <div className="space-y-6"><header className="explore-heading"><p className="eyebrow">关系探索</p><h1>沿着人物，走进历史</h1><p>从当前条目出发，双击相邻节点继续探索。</p></header><GraphView key={id} data={data} loading={people.loading||events.loading||relationships.loading} error={people.error||events.error||relationships.error}/></div>;
}
export function GraphView({data,loading=false,error,overview=false}:{data?:GraphResponse;loading?:boolean;error?:string;overview?:boolean}) {
 if(loading)return <p role="status" className="py-16">正在加载图谱…</p>;
 if(error)return <p role="alert" className="py-16">图谱暂时无法加载，请刷新重试。</p>;
 if(!data?.nodes.length)return <p className="py-16">当前没有可展示的图谱内容。</p>;
 return <GraphExplorer data={data} overview={overview}/>;
}
function GraphExplorer({data,overview}:{data:GraphResponse;overview:boolean}) {
 const [mode,setMode]=useState<GraphViewMode>(!overview&&data.center.type==='event'?'events':'people');
 const [selection,setSelection]=useState<GraphSelection>(overview?null:{kind:'node',id:data.center.id});
 const [query,setQuery]=useState('');
 const [history,setHistory]=useState<string[]>(overview?[]:[data.center.id]);
 const focus=history.at(-1)||'';
 const [focusRequest,setFocusRequest]=useState(0);
 const [depth,setDepth]=useState(1);
 const [from,setFrom]=useState('');
 const [to,setTo]=useState('');
 const [evidence,setEvidence]=useState(false);
 const base=useMemo(()=>graphForView(data,mode),[data,mode]);
 const invalidRange=mode==='events'&&from!==''&&to!==''&&Number(from)>Number(to);
 const selectedNode=selection?.kind==='node'?data.nodes.find(n=>n.id===selection.id):undefined;
 const selectedEdge=selection?.kind==='edge'?data.edges.find(e=>edgeKey(e)===selection.id):undefined;
 function select(next:GraphSelection){setSelection(next);setEvidence(false);setFocusRequest(v=>v+1);}
 function dive(id:string){setHistory(h=>enterSubgraph(h,id));setDepth(1);setQuery('');select({kind:'node',id});}
 function navigate(index:number){const next=history.slice(0,index+1);setHistory(next);setDepth(1);select(next.length?{kind:'node',id:next.at(-1)!}:null);}
 function reset(){setQuery('');setFrom('');setTo('');setHistory([]);setDepth(1);select(null);}
 const filtered=useMemo(()=>{
   const scope=focus?neighborhood(base,focus,depth):null;
   const nodes=base.nodes.filter(n=>{
     if(invalidRange)return false;
     if(scope&&!scope.has(n.id))return false;
     if(n.type==='event'&&n.start_year!=null)return (from===''||(n.end_year??n.start_year)>=Number(from))&&(to===''||n.start_year<=Number(to));
     return true;
   });
   const ids=new Set(nodes.map(n=>n.id));
   const edges=base.edges.filter(e=>ids.has(e.source)&&ids.has(e.target));
   return {...base,nodes,edges};
 },[base,focus,depth,from,to,invalidRange]);
 const matches=base.nodes.filter(n=>entryTitle(n).includes(query.trim()) || (n.type==='person' && n.aliases?.some(a=>a.includes(query.trim()))));
 const selectedIds=selectedNode?neighborhood(filtered,selectedNode.id,1):selectedEdge?new Set([selectedEdge.source,selectedEdge.target]):null;
 const highlighted=query.trim()?new Set(matches.map(n=>n.id)):selectedIds;
 const title=(id:string)=>{const n=data.nodes.find(node=>node.id===id);return n?entryTitle(n):'未知条目';};
 const edgeTitle=(e:Edge)=>`${title(e.source)} → ${title(e.target)}：${edgeTypeLabel(e.type)}`;
 const visibleIds=new Set(filtered.nodes.map(n=>n.id));
 const selectedHidden=selectedNode&&!visibleIds.has(selectedNode.id)||selectedEdge&&!filtered.edges.some(e=>edgeKey(e)===edgeKey(selectedEdge));
 const adjacent=selectedNode?base.edges.filter(e=>e.source===selectedNode.id||e.target===selectedNode.id):[];
 const button='rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm';
 function switchMode(next:GraphViewMode) {setMode(next);setHistory([]);setQuery('');select(null);}
 return <section className="graph-workspace space-y-3" aria-label="历史图谱工作区">
   <div className="graph-toolbar">
     <div className="inline-flex rounded-xl bg-[#e8ede6] p-1" aria-label="图谱视图">
       <button aria-pressed={mode==='people'} className={`graph-mode ${mode==='people'?'is-active':''}`} onClick={()=>switchMode('people')}>人物关系</button>
       <button aria-pressed={mode==='events'} className={`graph-mode ${mode==='events'?'is-active':''}`} onClick={()=>switchMode('events')}>人物与事件</button>
     </div>
     <p className="graph-count"><strong>{filtered.nodes.length}</strong> 个条目 · {filtered.edges.length} 条{mode==='people'?'人物':'参与'}关系</p>
   </div>
   <div className="graph-filters">
     <label className="text-sm"><span className="sr-only">查找人物／事件</span><input aria-label="查找图谱节点" className="block border rounded-lg px-3 py-2 mt-1 bg-white" value={query} onChange={e=>setQuery(e.target.value)} placeholder={mode==='people'?'搜索人物，跳转到他的关系…':'搜索人物或事件…'}/></label>
     {mode==='events'&&<><label className="text-sm">事件起始年<input aria-label="图谱起始年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={from} onChange={e=>setFrom(e.target.value)}/></label>
     <label className="text-sm">事件结束年<input aria-label="图谱结束年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={to} onChange={e=>setTo(e.target.value)}/></label></>}
     <button className={button} onClick={reset}>重置筛选</button>
   </div>
   {invalidRange&&<p role="alert" className="text-rose-700">起始年不能晚于结束年。</p>}
   {query.trim()&&<div className="flex flex-wrap gap-2" aria-label="图谱搜索结果">{matches.length?matches.slice(0,20).map(n=><button key={n.id} className={button} onClick={()=>{if(focus&&!visibleIds.has(n.id))setHistory([]);setFrom('');setTo('');select({kind:'node',id:n.id});setQuery('');}}>{entryTitle(n)}</button>):<p className="text-sm text-stone-500">没有找到匹配的条目。</p>}{matches.length>20&&<span className="text-sm">仅显示前 20 项，请缩小关键词范围。</span>}</div>}
   <div className="graph-context">
     <nav className="graph-breadcrumbs" aria-label="子图探索路径">
       <button onClick={()=>navigate(-1)} aria-current={!focus?'page':undefined}>全部{mode==='people'?'人物':'关系'}</button>
       {history.map((id,i)=><span key={`${id}-${i}`}><span aria-hidden="true"> / </span><button aria-current={i===history.length-1?'page':undefined} onClick={()=>navigate(i)}>{title(id)}</button></span>)}
     </nav>
     {focus?<div className="flex flex-wrap items-center gap-2"><button className={button} onClick={()=>navigate(history.length-2)}>← 返回上一级</button><button className={button} onClick={()=>setDepth(depth===1?2:1)}>{depth===1?'展开两层关系':'只看直接关系'}</button><button className={button} onClick={()=>navigate(-1)}>恢复全图</button></div>:<span className="text-xs text-stone-500">单击聚焦 · 双击进入子图 · 拖动自由布局</span>}
   </div>

   <div className="graph-columns">
     <div className="min-w-0">
       {filtered.nodes.length?<GraphCanvas key={`${mode}:${focus}:${depth}:${from}:${to}`} data={filtered} mode="network" selection={selection} onSelect={select} onEnterSubgraph={dive} focusRequest={focusRequest} highlighted={highlighted}/>:<p className="reading-card py-20 text-center">没有符合条件的关系或条目。可以重置筛选查看全部内容。</p>}
       {selection&&<a href="#graph-details" className="xl:hidden block text-center rounded-lg bg-teal-50 p-3 mt-3 text-sm text-teal-800">查看选中内容的详情 ↓</a>}
       <details className="mt-3 rounded-xl border border-stone-200 bg-white p-4"><summary className="text-sm">关系清单 · {filtered.edges.length} 条（也可在这里选择）</summary><div className="max-h-64 overflow-auto mt-3 space-y-2">{filtered.edges.map(e=><button key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})} className={`block w-full text-left rounded-lg p-3 text-sm ${selectedEdge&&edgeKey(selectedEdge)===edgeKey(e)?'bg-teal-100':'bg-stone-50'}`}>{edgeTitle(e)}</button>)}</div></details>
     </div>
     <aside id="graph-details" className="graph-detail" aria-label="图谱详情" aria-live="polite">
       <div className="flex justify-between items-center"><p className="eyebrow">{selectedEdge?'关系详情':selectedNode?.type==='person'?'人物详情':selectedNode?'事件详情':'阅读图谱'}</p>{selection&&<button className="text-sm text-stone-500" onClick={()=>select(null)}>取消选择</button>}</div>
       {selectedHidden&&<p className="text-xs text-amber-800 mt-3">当前筛选未展示此项，详情仍保留。重置筛选可回到全图。</p>}
       {selectedNode?<>
         <div className="detail-monogram" aria-hidden="true">{entryTitle(selectedNode).slice(0,1)}</div><h2 className="font-serif text-2xl leading-9 mt-4">{entryTitle(selectedNode)}</h2>
         <p className="text-sm text-stone-500 mt-2">{selectedNode.type==='event'?formatDisplayRange(selectedNode.start_year,selectedNode.end_year):selectedNode.era||'时代待补充'}</p>
         <p className="text-sm leading-7 mt-4">{selectedNode.description||'条目说明尚待整理。'}</p>
         <div className="flex flex-wrap gap-2 mt-5"><button className={button} onClick={()=>dive(selectedNode.id)}>进入关系子图</button><Link className="rounded-lg bg-[#285747] px-3 py-2 text-sm text-white" to={entryPath(selectedNode)}>阅读全文与出处 →</Link><Link className={button} to={`/ask?kind=${selectedNode.type}&id=${selectedNode.id}`}>问史料</Link></div>
         {selectedNode.type==='event'&&selectedNode.phases?.map((p,i)=><div key={i} className="border-l-2 border-stone-300 pl-3 mt-4 text-sm"><strong>{p.title}</strong><p className="leading-7 mt-1">{p.description}</p></div>)}
         <h3 className="text-sm font-semibold mt-6 mb-2">相关关系 · {adjacent.length}</h3>
         <div className="space-y-2">{adjacent.length===0&&<p className="text-sm text-stone-500 leading-7">当前视图尚未收录这位人物的关系。可切换另一视图继续查看。</p>}{adjacent.map(e=><button className="block w-full text-left text-sm p-3 bg-stone-50 rounded-lg hover:bg-teal-50" key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})}>{edgeTitle(e)}</button>)}</div>
       </>:selectedEdge?<>
         <div className="mt-4 space-y-3"><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.source})}>{title(selectedEdge.source)}</button><p className="text-sm text-stone-500">↓ {edgeTypeLabel(selectedEdge.type)}</p><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.target})}>{title(selectedEdge.target)}</button></div>
         <p className="text-sm leading-7 mt-5">{selectedEdge.description || (edgeSubject(selectedEdge,data.nodes)==='person_event'?`当前记录的事件角色为“${edgeTypeLabel(selectedEdge.type)}”，具体依据见下方史料。`:'该关系已记录，进一步说明尚待整理。')}</p>
         <p className="text-xs leading-6 text-stone-500 mt-3">{edgeSubject(selectedEdge,data.nodes)==='person_event'?(()=>{const e=data.nodes.find(n=>(n.id===selectedEdge.source||n.id===selectedEdge.target)&&n.type==='event');return e?.type==='event'?`关联事件：${formatDisplayRange(e.start_year,e.end_year)}`:'';})():'关系有效起止时间尚未单独整理。'}</p>
       </>:<><h2 className="font-serif text-2xl mt-4">从一位人物开始</h2><p className="text-sm leading-7 mt-4">选中人物，画布会自动移到他的位置，并放大到便于阅读的大小。关系线也可以点击，查看双方身份与史料依据。</p><p className="text-sm leading-7 mt-3">双击节点，只看他与相邻人物或事件的子图。可以继续双击探索，或通过上方路径返回。</p></>}
       {(selectedNode||selectedEdge)&&<div className="border-t border-stone-200 mt-6 pt-4"><button className="text-sm text-teal-800 underline" aria-expanded={evidence} onClick={()=>setEvidence(!evidence)}>{evidence?'收起史料依据':'查看史料依据'}</button>{evidence&&(selectedNode?<Evidence key={selectedNode.id} subject={selectedNode.type} id={selectedNode.id}/>:selectedEdge?.id?<Evidence key={edgeKey(selectedEdge)} subject={edgeSubject(selectedEdge,data.nodes)} id={selectedEdge.id}/>:<p className="text-sm mt-3">这条关系的独立出处尚待整理。</p>)}</div>}
       {!overview&&<Link to="/graph" className="block text-sm underline text-teal-700 mt-6">打开全部人物与事件图谱 →</Link>}
     </aside>
   </div>
 </section>;
}
