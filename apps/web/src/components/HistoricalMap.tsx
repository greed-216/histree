import { useState } from 'react';
import { Link } from 'react-router-dom';
import atlasData from '../data/atlas-907.json';
import { parseAtlas, snapshotAt } from '../lib/atlas';
import { AtlasCanvas } from './atlas/AtlasCanvas';

const atlas = parseAtlas(JSON.stringify(atlasData));
export default function HistoricalMap() {
  const [year,setYear] = useState(907);
  const [selected,setSelected] = useState('liang');
  const [reference,setReference] = useState(false);
  const snapshot = snapshotAt(atlas,year);
  const region = snapshot?.regions.find(r=>r.id===selected);
  return <section className="space-y-4" aria-label="历史分块底图">
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[#303d35] p-5 text-[#eee6d1]">
      <div><p className="text-xs tracking-widest opacity-70">五代十国 · 疆域图集</p><h2 className="font-serif text-2xl mt-1">{year} 年 · 分块底图</h2></div>
      <label className="text-sm">底图年份 <input aria-label="底图年份" type="number" min="1" className="w-24 rounded border border-white/30 p-2" value={year} onChange={e=>{const n=Number(e.target.value);if(Number.isSafeInteger(n)&&n!==0){setYear(n);setSelected('');}}}/></label>
    </div>
    <div className="flex flex-wrap gap-2" aria-label="底图时间线">{[907,908,913,923].map(y=><button key={y} aria-pressed={year===y} className={`rounded-full border px-4 py-2 text-sm ${year===y?'bg-[#303d35] text-white':'bg-white'}`} onClick={()=>{setYear(y);setSelected('');}}>{y}{snapshotAt(atlas,y)?' · 描绘稿':' · 待绘'}</button>)}</div>
    {snapshot ? <div className="grid lg:grid-cols-[minmax(0,1fr)_250px] gap-4">
      <AtlasCanvas snapshot={snapshot} selected={selected} onSelect={setSelected} referenceOpacity={reference ? .8 : 0}/>
      <aside className="atlas-panel space-y-4">
        <div><p className="text-xs text-stone-500">选中地块</p><h3 className="font-serif text-3xl mt-2">{region?.name ?? '点击疆域地块'}</h3></div>
        <p className="text-sm leading-7 text-stone-600">{region?.note ?? '可以直接点击分块，或使用下方的地块列表。'}</p>
        <div className="flex flex-wrap gap-2" aria-label="底图地块列表">{snapshot.regions.map(r=><button key={r.id} aria-pressed={selected===r.id} onClick={()=>setSelected(r.id)} className={`border rounded px-2 py-1 text-sm ${selected===r.id?'border-stone-700 bg-white':'border-stone-300'}`}><span style={{background:r.color}} className="inline-block w-2 h-2 rounded-full mr-1"/>{r.name}</button>)}</div>
        <label className="block text-sm"><input type="checkbox" checked={reference} onChange={e=>setReference(e.target.checked)}/> 叠加 907 年参考原图</label>
        <Link to="/map/edit" className="block rounded-lg bg-[#303d35] text-center text-white py-3 text-sm">编辑疆域底图 →</Link>
      </aside>
    </div> : <div className="atlas-panel py-16 text-center"><h3 className="font-serif text-xl">{year} 年底图尚未绘制</h3><p className="text-sm text-stone-600 mt-3">当前仅有 907 年概略稿。新年份需要单独核对疆域，不能沿用旧边界当作当年的地图。</p><button onClick={()=>setYear(907)} className="underline mt-4 mr-6">查看 907 年</button><Link to="/map/edit" className="underline">复制底图并绘制新版本 →</Link></div>}
    <p className="text-xs leading-6 text-stone-500">底图参考：史图馆，获取自 <a href="https://www.sohu.com/a/545519368_120646375" target="_blank" rel="noreferrer" className="underline">《图说五代十国》907 年图</a>。Histree 概略重绘，仅覆盖主要分块，空白区域待补绘；边界未经逐段考订。分块不等同于独立国家，当前也不是州县级行政区划。事件、人物与行军路线属于另行叠加的内容。</p>
  </section>;
}
