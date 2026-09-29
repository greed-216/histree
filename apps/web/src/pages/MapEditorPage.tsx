import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Polyline, Polygon, Marker, Tooltip, useMapEvents } from 'react-leaflet';
import { divIcon } from 'leaflet';
import { emptyMap, geometry, parseMap, vertices, type MapDocument, type MapFeature, type Position, type Geometry } from '../lib/mapDocument';
import 'leaflet/dist/leaflet.css';

const storageKey = 'histree-map-draft-v1';
const vertexIcon = divIcon({className:'',html:'<span style="display:block;width:14px;height:14px;background:white;border:3px solid #0f766e;border-radius:50%"></span>',iconSize:[14,14],iconAnchor:[7,7]});
const latlng = (p: Position): [number, number] => [p[1],p[0]];
type Tool = 'select' | Geometry['type'];
function Clicks({tool, onPoint}:{tool:Tool; onPoint:(p:Position)=>void}) {
 useMapEvents({click: e => {if(tool !== 'select') onPoint([e.latlng.wrap().lng,e.latlng.lat]);}});
 return null;
}
function initial() { try { const raw=localStorage.getItem(storageKey); return {doc:raw?parseMap(raw):emptyMap(),message:raw?'已恢复本机草稿。':'先选择画点、画线或画区域，再点击地图。'}; } catch { return {doc:emptyMap(),message:'本机草稿无法读取，原存储未覆盖。可先导入备份文件。'}; } }
export function MapEditorPage() {
 const [boot] = useState(initial);
 const [doc,setDoc] = useState<MapDocument>(boot.doc);
 const [history,setHistory] = useState<MapDocument[]>([]);
 const [tool,setTool] = useState<Tool>('select');
 const [points,setPoints] = useState<Position[]>([]);
 const [selected,setSelected] = useState('');
 const [year,setYear] = useState(907);
 const [all,setAll] = useState(true);
 const [message,setMessage] = useState(boot.message);
 const [dirty,setDirty] = useState(false);
 const [reference,setReference] = useState('');
 const [tileError,setTileError] = useState(false);
 const feature=doc.features.find(f=>f.id===selected);
 useEffect(()=>()=>{if(reference) URL.revokeObjectURL(reference);},[reference]);
 useEffect(()=>{const guard=(e:BeforeUnloadEvent)=>{if(dirty){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',guard);return()=>window.removeEventListener('beforeunload',guard);},[dirty]);
 function change(next:MapDocument) {setHistory(h=>[...h.slice(-39),doc]);setDoc(next);setDirty(true);}
 function update(next:MapFeature) {change({...doc,features:doc.features.map(f=>f.id===next.id?next:f)});}
 function choose(next:Tool) {setTool(next);setPoints([]);setSelected('');setMessage(next==='select'?'点击已有要素，拖动白色顶点修改位置。':'依次点击地图添加顶点；完成后点击“完成绘制”。');}
 function finish(coords=points) {
  if(tool==='select')return;
  if(coords.length<(tool==='Point'?1:tool==='LineString'?2:3)){setMessage('点需要 1 个顶点，线至少 2 个，区域至少 3 个。');return;}
  const f:MapFeature={type:'Feature',id:crypto.randomUUID(),geometry:geometry(tool,coords),properties:{name:tool==='Point'?'未命名地点':tool==='LineString'?'未命名路线':'未命名区域',color:'#0f766e',start_year:year,end_year:year,source:'',note:'',status:'draft'}};
  change({...doc,features:[...doc.features,f]});setSelected(f.id);setTool('select');setPoints([]);setMessage('已生成草稿，请填写名称、适用年份和依据。');
 }
 function exportFile() {try {parseMap(JSON.stringify(doc));} catch(e) {setMessage(e instanceof Error?e.message:'请先修正草稿再导出。');return;}const blob=new Blob([JSON.stringify(doc,null,2)],{type:'application/geo+json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='histree-map.geojson';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 const visible=doc.features.filter(f=>all||(f.properties.start_year<=year&&f.properties.end_year>=year));
 const button='rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm disabled:opacity-40';
 return <div className="space-y-5">
  <header><Link to="/map" className="text-teal-700 underline">← 地图浏览</Link><h1 className="font-serif text-3xl mt-3">历史地图绘图工作台</h1><p className="text-slate-600 mt-3">在现代地理底图上绘制地点、路线和区域。每个要素记录适用年份和依据，逐步整理各时期的地图。</p><p className="text-sm text-amber-900 mt-2">当前为个人草稿工具：只保存到本机浏览器，不会发布到网站。离开本页前请保存，并导出文件备份；手绘边界需核对后才能作为历史内容发布。</p></header>
  <div className="flex flex-wrap items-center gap-2">
   <label>地图名称 <input aria-label="地图名称" className="border rounded p-2" maxLength={200} value={doc.title} onChange={e=>change({...doc,title:e.target.value})}/></label>
   <button className={button} onClick={()=>{try {parseMap(JSON.stringify(doc));localStorage.setItem(storageKey,JSON.stringify(doc));setDirty(false);setMessage('已保存到本机浏览器。');}catch(e){setMessage(e instanceof Error?e.message:'保存失败，请导出备份。');}}}>保存到本机{dirty?' *':''}</button>
   <button className={button} onClick={exportFile}>导出 GeoJSON</button>
   <label className={button}>导入草稿<input aria-label="导入草稿" type="file" accept=".json,.geojson" className="block text-xs max-w-48 mt-1" onChange={async e=>{const f=e.target.files?.[0];if(!f)return;try {if(f.size>2_000_000)throw Error('文件不能超过 2 MB。');const next=parseMap(await f.text());change(next);setPoints([]);setTool('select');setSelected('');setMessage('已导入，可撤销恢复导入前草稿。');}catch(err){setMessage(err instanceof Error?err.message:'导入失败。');}e.target.value='';}}/></label>
   <button className={button} disabled={!history.length} onClick={()=>{setDoc(history.at(-1)!);setHistory(h=>h.slice(0,-1));setDirty(true);setPoints([]);setSelected('');setTool('select');}}>撤销修改</button>
  </div>
  <div className="flex flex-wrap gap-2 items-center">
   {([['select','选择／编辑'],['Point','画地点'],['LineString','画路线'],['Polygon','画区域']] as [Tool,string][]).map(([t,label])=><button key={t} aria-pressed={tool===t} className={`${button} ${tool===t?'ring-2 ring-teal-700':''}`} onClick={()=>choose(t)}>{label}</button>)}
   {tool!=='select'&&<><button className={button} onClick={()=>finish()}>完成绘制（{points.length}）</button><button className={button} disabled={!points.length} onClick={()=>setPoints(p=>p.slice(0,-1))}>撤回顶点</button><button className={button} onClick={()=>choose('select')}>取消绘制</button></>}
   <label className="text-sm">查看年份 <input aria-label="查看年份" type="number" className="w-24 border rounded p-2" value={year} onChange={e=>{const n=Number(e.target.value);if(Number.isInteger(n)&&n!==0)setYear(n);}}/></label>
   <label className="text-sm"><input type="checkbox" checked={all} onChange={e=>{setAll(e.target.checked);setSelected('');}}/> 显示全部年份</label>
  </div>
  <p role="status" className="text-sm text-teal-800">{message} · {visible.length} / {doc.features.length} 个要素</p>
  <div className="grid lg:grid-cols-[minmax(0,1fr)_300px] gap-5">
   <div className="min-w-0 relative z-0 rounded-xl overflow-hidden border" aria-label="绘图地图">
    <MapContainer center={[35,112]} zoom={5} style={{height:600,width:'100%'}} doubleClickZoom={false}>
     <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' eventHandlers={{tileerror:()=>setTileError(true)}}/>
     <Clicks tool={tool} onPoint={p=>{if(Math.abs(p[1])>90)return;if(tool==='Point')finish([p]);else setPoints(v=>[...v,p]);}}/>
     {visible.map(f=>{const opts={color:f.properties.color,weight:f.id===selected?4:2};const handlers={click:()=>{if(tool==='select')setSelected(f.id);}};const tip=<Tooltip>{f.properties.name}（{f.properties.start_year}—{f.properties.end_year}）</Tooltip>;return f.geometry.type==='Point'?<CircleMarker key={`${f.id}-${tool}`} center={latlng(f.geometry.coordinates)} radius={8} pathOptions={opts} interactive={tool==='select'} bubblingMouseEvents={false} eventHandlers={handlers}>{tip}</CircleMarker>:f.geometry.type==='LineString'?<Polyline key={`${f.id}-${tool}`} positions={f.geometry.coordinates.map(latlng)} pathOptions={opts} interactive={tool==='select'} bubblingMouseEvents={false} eventHandlers={handlers}>{tip}</Polyline>:<Polygon key={`${f.id}-${tool}`} positions={f.geometry.coordinates[0].map(latlng)} pathOptions={{...opts,fillOpacity:.2}} interactive={tool==='select'} bubblingMouseEvents={false} eventHandlers={handlers}>{tip}</Polygon>;})}
     {points.length>0&&<Polyline positions={points.map(latlng)} pathOptions={{color:'#b45309',dashArray:'5 5'}} interactive={false}/>}
     {points.map((p,i)=><CircleMarker key={i} center={latlng(p)} radius={4} interactive={false}/>)}
     {feature&&visible.includes(feature)&&vertices(feature).map((p,i)=><Marker key={`${feature.id}-${i}`} position={latlng(p)} icon={vertexIcon} draggable eventHandlers={{dragend:e=>{const ll=e.target.getLatLng();const ps=vertices(feature);ps[i]=[ll.wrap().lng,Math.max(-90,Math.min(90,ll.lat))];update({...feature,geometry:geometry(feature.geometry.type,ps)});}}}/>)}
    </MapContainer>
    {tileError&&<p className="bg-amber-50 p-3 text-sm">部分底图加载失败。绘图仍保留，可导出备份后刷新。</p>}
   </div>
   <aside className="space-y-4 min-w-0">
    {feature?<div className="reading-card space-y-3"><h2 className="font-semibold">编辑要素</h2>
     <label className="block text-sm">名称<input aria-label="要素名称" maxLength={200} className="block border rounded p-2 w-full" value={feature.properties.name} onChange={e=>update({...feature,properties:{...feature.properties,name:e.target.value}})}/></label>
     <label className="block text-sm">颜色 <input aria-label="要素颜色" type="color" value={feature.properties.color} onChange={e=>update({...feature,properties:{...feature.properties,color:e.target.value}})}/></label>
     {(['start_year','end_year'] as const).map(k=><label className="block text-sm" key={k}>{k==='start_year'?'开始年':'结束年'}<input aria-label={k==='start_year'?'要素开始年':'要素结束年'} type="number" className="block border rounded p-2 w-full" value={feature.properties[k]} onChange={e=>{const n=Number(e.target.value);if(Number.isInteger(n)&&n!==0)update({...feature,properties:{...feature.properties,[k]:n}});}}/></label>)}
     {feature.properties.start_year>feature.properties.end_year&&<p role="alert" className="text-red-700 text-sm">开始年不能晚于结束年，请修正后保存。</p>}
     <label className="block text-sm">依据／出处<textarea aria-label="要素出处" className="block border rounded p-2 w-full" value={feature.properties.source} onChange={e=>update({...feature,properties:{...feature.properties,source:e.target.value}})}/></label>
     <label className="block text-sm">定位说明／争议<textarea aria-label="要素说明" className="block border rounded p-2 w-full" value={feature.properties.note} onChange={e=>update({...feature,properties:{...feature.properties,note:e.target.value}})}/></label>
     <p className="text-xs text-slate-500">拖动白色顶点修改形状。复杂边界可先粗绘，再导出到 GIS 工具细修。所有要素均为草稿。</p>
     <button className={button} onClick={()=>{change({...doc,features:doc.features.filter(f=>f.id!==selected)});setSelected('');setMessage('要素已移除，可用“撤销修改”恢复。');}}>删除要素</button>
    </div>:<p className="reading-card text-sm">选择一种绘图工具开始，或点击已有要素编辑。</p>}
    <details className="reading-card" open><summary>图层要素（{doc.features.length}）</summary><ul className="max-h-48 overflow-auto mt-3 space-y-2">{doc.features.map(f=><li key={f.id}><button className="text-left text-sm underline" onClick={()=>{setAll(true);setTool('select');setPoints([]);setSelected(f.id);}}>{f.properties.name} · {f.properties.start_year}—{f.properties.end_year}</button></li>)}</ul></details>
    <details className="reading-card"><summary>参考图对照</summary><p className="text-xs mt-2">上传图片在旁边对照，不会上传到服务器，也不会自动对齐经纬度。刷新后需重新选择图片。</p><input aria-label="参考图片" type="file" accept="image/png,image/jpeg,image/webp" className="w-full text-xs mt-2" onChange={e=>{const f=e.target.files?.[0];if(f&&f.size<20_000_000)setReference(URL.createObjectURL(f));else setMessage('参考图片须小于 20 MB。');}}/>{reference&&<a href={reference} target="_blank" rel="noreferrer"><img src={reference} alt="绘图参考，未地理配准" className="w-full mt-3"/></a>}</details>
   </aside>
  </div>
 </div>;
}
