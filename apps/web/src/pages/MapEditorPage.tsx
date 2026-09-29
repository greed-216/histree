import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import atlasData from '../data/atlas-907.json';
import { AtlasCanvas } from '../components/atlas/AtlasCanvas';
import { cloneSnapshot, parseAtlas, type AtlasDocument, type AtlasPoint, type AtlasRegion, type AtlasSnapshot } from '../lib/atlas';

const storageKey = 'histree-basemap-v1';
function initial() {
  try {
    const raw = localStorage.getItem(storageKey);
    return { document: parseAtlas(raw ?? JSON.stringify(atlasData)), message: raw ? '已恢复本机底图。' : '已加载 907 年概略描绘稿，点击地块开始修订。' };
  } catch {
    return {document: parseAtlas(JSON.stringify(atlasData)), message: '本机文件无法读取，已加载内置稿。原存储保留到下一次编辑，请先备份。'};
  }
}
export function MapEditorPage() {
  const [boot] = useState(initial);
  const [document,setDocument] = useState(boot.document);
  const [year,setYear] = useState(boot.document.snapshots[0].year);
  const [nextYear,setNextYear] = useState(String(year+1));
  const [history,setHistory] = useState<AtlasDocument[]>([]);
  const [selected,setSelected] = useState('liang');
  const [tool,setTool] = useState<'select' | 'new' | 'redraw' | 'label'>('select');
  const [points,setPoints] = useState<AtlasPoint[]>([]);
  const [reference,setReference] = useState(0);
  const [references,setReferences] = useState<Record<string,string>>({});
  const referenceUrls = useRef<Record<string,string>>({});
  useEffect(() => () => {Object.values(referenceUrls.current).forEach(url=>URL.revokeObjectURL(url));},[]);
  const [preview,setPreview] = useState(false);
  const [message,setMessage] = useState(boot.message);
  const [unsaved,setUnsaved] = useState(false);
  const snapshot = document.snapshots.find(s=>s.year===year) ?? document.snapshots[0];
  const region = snapshot.regions.find(r=>r.id===selected);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {if (unsaved) {event.preventDefault();event.returnValue='';}};
    window.addEventListener('beforeunload',warn);
    return () => window.removeEventListener('beforeunload',warn);
  },[unsaved]);
  function persist(next: AtlasDocument) {
    try {localStorage.setItem(storageKey,JSON.stringify(next));setUnsaved(false);setMessage('已自动保存到本机。可导出整个图集备份。');}
    catch {setUnsaved(true);setMessage('本机存储失败，请立即导出备份，离开本页会丢失修改。');}
  }
  function change(next: AtlasDocument) {
    try {parseAtlas(JSON.stringify(next));} catch (error) {setMessage(String(error));return;}
    setHistory(h=>[...h.slice(-39),document]);setDocument(next);persist(next);
  }
  function update(next: AtlasSnapshot) {change({...document,snapshots:document.snapshots.map(s=>s.id===next.id?next:s)});}
  function updateRegion(next: AtlasRegion) {update({...snapshot,regions:snapshot.regions.map(r=>r.id===next.id?next:r)});}
  function select(id: string) {setSelected(id);setTool('select');setPoints([]);}
  function finish() {
    if (points.length < 3) {setMessage('闭合地块至少需要三个不同顶点。');return;}
    const nodes = {...snapshot.nodes};
    const refs = points.map(p=>{
      const existing = Object.entries(nodes).find(([,v])=>Math.hypot(v[0]-p[0],v[1]-p[1])<1.5);
      if (existing) return existing[0];
      const id=crypto.randomUUID();nodes[id]=p;return id;
    });
    if (new Set(refs).size!==refs.length) {setMessage('顶点重复或过近，请撤回重复点。闭合时无需再次点击起点。');return;}
    const shape: AtlasRegion = {
      id: tool==='redraw' && region ? region.id : crypto.randomUUID(),
      name: tool==='redraw' && region ? region.name : '新地块',
      color: tool==='redraw' && region ? region.color : '#ae9c72',
      nodes:refs,
      label:[points.reduce((sum,p)=>sum+p[0],0)/points.length,points.reduce((sum,p)=>sum+p[1],0)/points.length],
      note: tool==='redraw' && region ? region.note : '待补充疆域依据与归属说明。',
    };
    update({...snapshot,nodes,regions:tool==='redraw'?snapshot.regions.map(r=>r.id===selected?shape:r):[...snapshot.regions,shape]});
    setSelected(shape.id);setPoints([]);setTool('select');
  }
  const button='rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm disabled:opacity-40';
  return <div className="space-y-5">
    <header><Link to="/map" className="text-teal-700 underline">← 历史地图</Link><p className="eyebrow mt-5">疆域制作 · 独立底图</p><h1 className="font-serif text-3xl mt-2">历史底图工坊</h1><p className="text-stone-600 leading-7 mt-3">描绘可选中的疆域分块，按年份保存整张底图。事件地点与行军路线在其他图层维护。</p></header>
    <div className="atlas-panel flex flex-wrap gap-3 items-end">
      <label className="text-sm">当前版本<select className="block border rounded p-2 bg-white mt-1" aria-label="底图版本" value={snapshot.year} onChange={e=>{setYear(Number(e.target.value));setSelected('');setPoints([]);setTool('select');setReference(0);}}>{[...document.snapshots].sort((a,b)=>a.year-b.year).map(s=><option key={s.id} value={s.year}>{s.year} 年 · {s.title}</option>)}</select></label>
      <label className="text-sm">新版本年份<input aria-label="新版本年份" className="block border rounded p-2 w-28 bg-white mt-1" type="number" value={nextYear} onChange={e=>setNextYear(e.target.value)}/></label>
      <button className={button} onClick={()=>{
        const n=Number(nextYear);
        if (!Number.isSafeInteger(n)||n===0||document.snapshots.some(s=>s.year===n)||document.snapshots.length>=50) {setMessage('请输入未使用的有效年份，最多保存 50 个版本。');return;}
        const next=cloneSnapshot(snapshot,n);
        change({...document,snapshots:[...document.snapshots,next]});setYear(n);setNextYear(String(n+1));setPoints([]);setTool('select');setReference(0);setMessage(`已复制为 ${n} 年草稿。疆域尚未修订，请按新年份的史料调整。`);
      }}>复制为新年份</button>
      <button className={button} disabled={!history.length} onClick={()=>{const previous=history.at(-1)!;setHistory(h=>h.slice(0,-1));setDocument(previous);if(!previous.snapshots.some(s=>s.year===year))setYear(previous.snapshots[0].year);setPoints([]);setTool('select');persist(previous);}}>撤销修改</button>
      <button className={button} aria-pressed={preview} onClick={()=>{setPreview(!preview);setTool('select');setPoints([]);}}> {preview?'返回编辑':'预览底图'}</button>
      <button className={button} onClick={()=>{
        const url=URL.createObjectURL(new Blob([JSON.stringify(document,null,2)],{type:'application/json'}));
        const anchor=window.document.createElement('a');anchor.href=url;anchor.download='histree-basemaps.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      }}>导出底图 JSON</button>
      <label className="text-xs">导入底图图集<input aria-label="导入底图图集" className="block max-w-48 mt-1" type="file" accept=".json" onChange={async event=>{
        const input=event.currentTarget; const file=input.files?.[0];if(!file)return;
        try {if(file.size>5_000_000)throw Error('文件不能超过 5 MB。');const next=parseAtlas(await file.text());change(next);setYear(next.snapshots[0].year);setSelected('');setPoints([]);setTool('select');setReference(0);}
        catch(error) {setMessage(error instanceof Error?error.message:'导入失败。');}
        input.value='';
      }}/></label>
    </div>
    <p role="status" className="text-sm text-teal-800">{message}</p>
    {!preview && <div className="flex flex-wrap gap-2 items-center">
      <button className={button} aria-pressed={tool==='select'} onClick={()=>{setTool('select');setPoints([]);}}>选择／修边界</button>
      <button className={button} aria-pressed={tool==='new'} onClick={()=>{setTool('new');setPoints([]);setSelected('');}}>绘制新地块</button>
      <button className={button} disabled={!region} aria-pressed={tool==='redraw'} onClick={()=>{setTool('redraw');setPoints([]);}}>重绘选中地块</button>
      <button className={button} disabled={!region} aria-pressed={tool==='label'} onClick={()=>{setTool('label');setPoints([]);setMessage('点击底图，放置选中地块的名称。');}}>移动名称</button>
      {(tool==='new'||tool==='redraw') && <><button className={button} onClick={finish}>闭合地块（{points.length}）</button><button className={button} disabled={!points.length} onClick={()=>setPoints(p=>p.slice(0,-1))}>撤回顶点</button></>}
      <label className="text-sm flex gap-2 items-center">参考图透明度 <input aria-label="参考图透明度" type="range" min="0" max="1" step=".1" value={reference} onChange={e=>setReference(Number(e.target.value))}/></label>
    </div>}
    {!preview && <label className="block text-sm text-stone-600">本版本参考图片（仅本次打开有效）<input aria-label="版本参考图片" type="file" accept="image/png,image/jpeg,image/webp" className="ml-3 text-xs" onChange={event=>{
      const file=event.currentTarget.files?.[0];if(!file)return;
      if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>20_000_000){setMessage('请选择小于 20 MB 的 PNG、JPEG 或 WebP 图片。');return;}
      const previous=referenceUrls.current[snapshot.id];if(previous)URL.revokeObjectURL(previous);
      const url=URL.createObjectURL(file);referenceUrls.current[snapshot.id]=url;
      setReferences({...referenceUrls.current});setReference(1);setMessage('参考图已放入画布，请降低透明度开始描绘。图片仅本地对照，不随 JSON 导出。');
    }}/></label>}
    {reference>0 && !references[snapshot.id] && snapshot.year!==907 && <p className="text-sm text-amber-800">叠加的是 907 年参考图，不能作为 {snapshot.year} 年疆域依据。</p>}
    <div className="grid lg:grid-cols-[minmax(0,1fr)_280px] gap-4">
      <AtlasCanvas key={snapshot.id} snapshot={snapshot} selected={selected} onSelect={select} editing={!preview} drawing={!preview && tool!=='select'} draft={points} referenceOpacity={reference} referenceUrl={references[snapshot.id]}
        onPoint={p=>{if(tool==='label'&&region){updateRegion({...region,label:p});setTool('select');}else setPoints(previous=>[...previous,p]);}}
        onMoveNode={(id,p)=>update({...snapshot,nodes:{...snapshot.nodes,[id]:p}})}/>
      <aside className="atlas-panel space-y-4">
        <h2 className="font-serif text-xl">{preview?'底图预览':'地块与版本'}</h2>
        {region && !preview ? <>
          <label className="block text-sm">分块名称／归属<input aria-label="分块名称" maxLength={100} className="block border rounded p-2 w-full bg-white mt-1" value={region.name} onChange={e=>updateRegion({...region,name:e.target.value})}/></label>
          <label className="block text-sm">疆域颜色 <input type="color" aria-label="疆域颜色" value={region.color} onChange={e=>updateRegion({...region,color:e.target.value})}/></label>
          <label className="block text-sm">依据与说明<textarea aria-label="地块依据" maxLength={4000} className="block border rounded p-2 w-full bg-white mt-1" rows={4} value={region.note} onChange={e=>updateRegion({...region,note:e.target.value})}/></label>
          <p className="text-xs leading-6 text-stone-600">拖动白点修订边界；相邻地块共享的顶点会一起移动。重绘只替换当前地块，需同时核对邻区，避免重叠和空隙。</p>
          <button className={button} onClick={()=>{update({...snapshot,regions:snapshot.regions.filter(r=>r.id!==selected)});setSelected('');setTool('select');setPoints([]);}}>删除地块（可撤销）</button>
        </> : <p className="text-sm text-stone-600">{region?`${region.name} · ${snapshot.year} 年`:'点击疆域地块查看，或选择“绘制新地块”。'}</p>}
        {!preview && <label className="block text-sm">版本依据<textarea aria-label="版本依据" maxLength={4000} rows={3} value={snapshot.source} onChange={e=>update({...snapshot,source:e.target.value})} className="block border rounded bg-white w-full p-2 mt-1"/></label>}
        <div className="border-t border-stone-300 pt-3"><h3 className="text-sm mb-2">分块 · {snapshot.regions.length}</h3><div className="flex flex-wrap gap-2">{snapshot.regions.map(r=><button key={r.id} onClick={()=>select(r.id)} className={`text-xs border rounded px-2 py-1 ${selected===r.id?'border-stone-700 bg-white':'border-stone-300'}`}>{r.name}</button>)}</div></div>
      </aside>
    </div>
    <p className="text-xs leading-6 text-stone-500">本机草稿自动保存，导出可备份或迁移；编辑不会直接改变网站公开图集。参考图：史图馆，来自 <a href="https://www.sohu.com/a/545519368_120646375" target="_blank" rel="noreferrer" className="underline">907 年形势图转载页</a>。当前为主要势力的概略分块，非精确疆界；画布坐标不代表经纬度。此版本支持单环地块，尚无自动裁切、合并或拓扑检查。</p>
  </div>;
}
