import { useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { GraphResponse, Edge } from '@histree/shared-types';
import { GraphCanvas } from '../components/graph/GraphCanvas';
import { Evidence } from '../components/Reading';
import { useResource } from '../hooks/useResource';
import { entryPath, entryTitle } from '../lib/reading';
import { edgeTypeLabel, formatDisplayRange } from '../lib/content';
import { edgeKey, edgeSubject, neighborhood, type GraphSelection } from '../lib/graph';

export function GraphPage() {
 const {id}=useParams<{id:string}>();
 const result=useResource<GraphResponse>(`/graph/${id}`);
 return <GraphView key={id} data={result.data} loading={result.loading} error={result.error}/>;
}
export function GraphView({data,loading=false,error,overview=false}:{data?:GraphResponse;loading?:boolean;error?:string;overview?:boolean}) {
 if(loading)return <p role="status" className="py-16">正在加载图谱…</p>;
 if(error)return <p role="alert" className="py-16">图谱暂时无法加载，请刷新重试。</p>;
 if(!data?.nodes.length)return <p className="py-16">当前没有可展示的图谱内容。</p>;
 return <GraphExplorer data={data} overview={overview}/>;
}
function GraphExplorer({data,overview}:{data:GraphResponse;overview:boolean}) {
 const [mode,setMode]=useState<'timeline'|'network'>(overview?'timeline':'network');
 const [selection,setSelection]=useState<GraphSelection>(overview?null:{kind:'node',id:data.center.id});
 const [query,setQuery]=useState('');
 const [relation,setRelation]=useState('all');
 const [focus,setFocus]=useState('');
 const [depth,setDepth]=useState(1);
 const [from,setFrom]=useState('');
 const [to,setTo]=useState('');
 const [evidence,setEvidence]=useState(false);
 const invalidRange=from!==''&&to!==''&&Number(from)>Number(to);
 const selectedNode=selection?.kind==='node'?data.nodes.find(n=>n.id===selection.id):undefined;
 const selectedEdge=selection?.kind==='edge'?data.edges.find(e=>edgeKey(e)===selection.id):undefined;
 function select(next:GraphSelection){setSelection(next);setEvidence(false);}
 const filtered=useMemo(()=>{
   const scope=focus?neighborhood(data,focus,depth):null;
   const nodes=data.nodes.filter(n=>{
     if(invalidRange)return false;
     if(scope&&!scope.has(n.id))return false;
     if(n.type==='event'&&n.start_year!=null)return (from===''||(n.end_year??n.start_year)>=Number(from))&&(to===''||n.start_year<=Number(to));
     return true;
   });
   const ids=new Set(nodes.map(n=>n.id));
   let edges=data.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(relation==='all'||edgeSubject(e,data.nodes)===relation));
   if(relation!=='all') {
     const linked=new Set(edges.flatMap(e=>[e.source,e.target]));
     return {...data,nodes:nodes.filter(n=>linked.has(n.id)),edges};
   }
   if(mode==='timeline')edges=edges.filter(e=>edgeSubject(e,data.nodes)==='person_event');
   return {...data,nodes,edges};
 },[data,focus,depth,from,to,invalidRange,relation,mode]);
 const matches=data.nodes.filter(n=>entryTitle(n).includes(query.trim()) || (n.type==='person' && n.aliases?.some(a=>a.includes(query.trim()))));
 const selectedIds=selectedNode?neighborhood(data,selectedNode.id,1):selectedEdge?new Set([selectedEdge.source,selectedEdge.target]):null;
 const highlighted=query.trim()?new Set(matches.map(n=>n.id)):selectedIds;
 const title=(id:string)=>{const n=data.nodes.find(node=>node.id===id);return n?entryTitle(n):'未知条目';};
 const edgeTitle=(e:Edge)=>`${title(e.source)} → ${title(e.target)}：${edgeTypeLabel(e.type)}`;
 const visibleIds=new Set(filtered.nodes.map(n=>n.id));
 const selectedHidden=selectedNode&&!visibleIds.has(selectedNode.id)||selectedEdge&&!filtered.edges.some(e=>edgeKey(e)===edgeKey(selectedEdge));
 const adjacent=selectedNode?data.edges.filter(e=>e.source===selectedNode.id||e.target===selectedNode.id):[];
 const button='rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm';
 function switchMode(next:'timeline'|'network') {setMode(next);setRelation(next==='network'?'person_relationship':'all');if(selection?.kind==='edge')select(null);}
 return <section className="space-y-4" aria-label="历史图谱工作区">
   <div className="flex flex-wrap justify-between gap-3 items-center">
     <div className="inline-flex rounded-xl bg-[#e8ede6] p-1" aria-label="图谱视图">
       <button aria-pressed={mode==='timeline'} className={`graph-mode ${mode==='timeline'?'is-active':''}`} onClick={()=>switchMode('timeline')}>历史进程</button>
       <button aria-pressed={mode==='network'} className={`graph-mode ${mode==='network'?'is-active':''}`} onClick={()=>switchMode('network')}>关系探索</button>
     </div>
     <p className="text-xs text-stone-500">{filtered.nodes.length} 个条目 · {filtered.edges.length} 条{mode==='timeline'?'参与':'已记录'}关系</p>
   </div>
   <div className="flex flex-wrap gap-3 items-end">
     <label className="text-sm">查找人物／事件<input aria-label="查找图谱节点" className="block border rounded-lg px-3 py-2 mt-1 bg-white" value={query} onChange={e=>setQuery(e.target.value)} placeholder="输入姓名或事件关键词"/></label>
     <label className="text-sm">事件起始年<input aria-label="图谱起始年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={from} onChange={e=>setFrom(e.target.value)}/></label>
     <label className="text-sm">事件结束年<input aria-label="图谱结束年" className="block w-24 border rounded-lg p-2 mt-1" type="number" value={to} onChange={e=>setTo(e.target.value)}/></label>
     {mode==='network'&&<label className="text-sm">关系类型<select aria-label="关系类型" className="block border rounded-lg p-2 mt-1 bg-white" value={relation} onChange={e=>setRelation(e.target.value)}><option value="all">全部关系</option><option value="person_relationship">人物关系</option><option value="person_event">事件参与</option><option value="event_causality">事件因果</option></select></label>}
     <button className={button} onClick={()=>{setQuery('');setFrom('');setTo('');setFocus('');setRelation('all');select(null);}}>重置筛选</button>
   </div>
   {invalidRange&&<p role="alert" className="text-rose-700">起始年不能晚于结束年。</p>}
   {query.trim()&&<div className="flex flex-wrap gap-2" aria-label="图谱搜索结果">{matches.length?matches.slice(0,20).map(n=><button key={n.id} className={button} onClick={()=>{select({kind:'node',id:n.id});setQuery('');}}>{entryTitle(n)}</button>):<p className="text-sm text-stone-500">没有找到匹配的条目。</p>}{matches.length>20&&<span className="text-sm">仅显示前 20 项，请缩小关键词范围。</span>}</div>}
   {focus&&<div className="flex flex-wrap gap-2 items-center text-sm bg-teal-50 rounded-lg p-3"><span>聚焦：{title(focus)}</span><button className={button} onClick={()=>setDepth(depth===1?2:1)}>{depth===1?'展开到两层关系':'收起为直接关系'}</button><button className={button} onClick={()=>setFocus('')}>返回当前全图</button></div>}
   <p className="text-xs text-stone-500">{mode==='timeline'?'每位人物一行，角色标签表示其参与该事件。空白表示暂无参与记录；人物之间的关系可切换到“关系探索”。':'节点位置仅用于阅读，不表示年代或地理位置。'} 年份筛选作用于事件，时间不详的条目保留。</p>
   <div className="grid xl:grid-cols-[minmax(0,1fr)_330px] gap-4 items-start">
     <div className="min-w-0">
       {filtered.nodes.length?<GraphCanvas key={`${mode}:${focus}:${depth}:${relation}:${from}:${to}`} data={filtered} mode={mode} selection={selection} onSelect={select} highlighted={highlighted}/>:<p className="reading-card py-20 text-center">没有符合条件的关系或条目。可以重置筛选查看全部内容。</p>}
       {selection&&<a href="#graph-details" className="xl:hidden block text-center rounded-lg bg-teal-50 p-3 mt-3 text-sm text-teal-800">查看选中内容的详情 ↓</a>}
       <details className="mt-3 rounded-xl border border-stone-200 bg-white p-4"><summary className="text-sm">关系清单 · {filtered.edges.length} 条（也可在这里选择）</summary><div className="max-h-64 overflow-auto mt-3 space-y-2">{filtered.edges.map(e=><button key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})} className={`block w-full text-left rounded-lg p-3 text-sm ${selectedEdge&&edgeKey(selectedEdge)===edgeKey(e)?'bg-teal-100':'bg-stone-50'}`}>{edgeTitle(e)}</button>)}</div></details>
     </div>
     <aside id="graph-details" className="graph-detail" aria-label="图谱详情" aria-live="polite">
       <div className="flex justify-between items-center"><p className="eyebrow">{selectedEdge?'关系详情':selectedNode?.type==='person'?'人物详情':selectedNode?'事件详情':'阅读图谱'}</p>{selection&&<button className="text-sm text-stone-500" onClick={()=>select(null)}>取消选择</button>}</div>
       {selectedHidden&&<p className="text-xs text-amber-800 mt-3">当前筛选未展示此项，详情仍保留。重置筛选可回到全图。</p>}
       {selectedNode?<>
         <h2 className="font-serif text-2xl leading-9 mt-4">{entryTitle(selectedNode)}</h2>
         <p className="text-sm text-stone-500 mt-2">{selectedNode.type==='event'?formatDisplayRange(selectedNode.start_year,selectedNode.end_year):selectedNode.era||'时代待补充'}</p>
         <p className="text-sm leading-7 mt-4">{selectedNode.description||'条目说明尚待整理。'}</p>
         <div className="flex flex-wrap gap-2 mt-5"><button className={button} onClick={()=>{setFocus(selectedNode.id);setDepth(1);switchMode('network');setRelation('all');}}>聚焦其关系</button><Link className="rounded-lg bg-[#285747] px-3 py-2 text-sm text-white" to={entryPath(selectedNode)}>阅读全文与出处 →</Link></div>
         {selectedNode.type==='event'&&selectedNode.phases?.map((p,i)=><div key={i} className="border-l-2 border-stone-300 pl-3 mt-4 text-sm"><strong>{p.title}</strong><p className="leading-7 mt-1">{p.description}</p></div>)}
         <h3 className="text-sm font-semibold mt-6 mb-2">相关关系 · {adjacent.length}</h3>
         <div className="space-y-2">{adjacent.map(e=><button className="block w-full text-left text-sm p-3 bg-stone-50 rounded-lg hover:bg-teal-50" key={edgeKey(e)} onClick={()=>select({kind:'edge',id:edgeKey(e)})}>{edgeTitle(e)}</button>)}</div>
       </>:selectedEdge?<>
         <div className="mt-4 space-y-3"><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.source})}>{title(selectedEdge.source)}</button><p className="text-sm text-stone-500">↓ {edgeTypeLabel(selectedEdge.type)}</p><button className="text-left font-semibold text-teal-800" onClick={()=>select({kind:'node',id:selectedEdge.target})}>{title(selectedEdge.target)}</button></div>
         <p className="text-sm leading-7 mt-5">{selectedEdge.description || (edgeSubject(selectedEdge,data.nodes)==='person_event'?`当前记录的事件角色为“${edgeTypeLabel(selectedEdge.type)}”，具体依据见下方史料。`:'该关系已记录，进一步说明尚待整理。')}</p>
         <p className="text-xs leading-6 text-stone-500 mt-3">{edgeSubject(selectedEdge,data.nodes)==='person_event'?(()=>{const e=data.nodes.find(n=>(n.id===selectedEdge.source||n.id===selectedEdge.target)&&n.type==='event');return e?.type==='event'?`关联事件：${formatDisplayRange(e.start_year,e.end_year)}`:'';})():'关系有效起止时间尚未单独整理。'}</p>
       </>:<><h2 className="font-serif text-2xl mt-4">沿着人物读历史</h2><p className="text-sm leading-7 mt-4">单击人物或事件，在这里查看详情；单击角色标签或关系线，查看它连接了谁、是什么关系以及史料依据。</p><p className="text-sm leading-7 mt-3">选中人物后，其相关事件和人物会突出显示。切换关系探索，可以拖动节点，并聚焦一到两层关系。</p></>}
       {(selectedNode||selectedEdge)&&<div className="border-t border-stone-200 mt-6 pt-4"><button className="text-sm text-teal-800 underline" aria-expanded={evidence} onClick={()=>setEvidence(!evidence)}>{evidence?'收起史料依据':'查看史料依据'}</button>{evidence&&(selectedNode?<Evidence key={selectedNode.id} subject={selectedNode.type} id={selectedNode.id}/>:selectedEdge?.id?<Evidence key={edgeKey(selectedEdge)} subject={edgeSubject(selectedEdge,data.nodes)} id={selectedEdge.id}/>:<p className="text-sm mt-3">这条关系的独立出处尚待整理。</p>)}</div>}
       {!overview&&<Link to="/graph" className="block text-sm underline text-teal-700 mt-6">打开全部人物与事件图谱 →</Link>}
     </aside>
   </div>
 </section>;
}
