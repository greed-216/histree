import { MAPS_ENABLED } from '../lib/features';
import { lazy, Suspense, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Event, PageResult } from '@histree/shared-types';
import { RecordPicker } from './RecordPicker';
import { InfiniteScroll } from './InfiniteScroll';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { LoadState } from './Reading';
import { useDebounced } from '../hooks/useDebounced';
import { useResource } from '../hooks/useResource';
import { formatDisplayRange } from '../lib/content';
const TopicMap = lazy(() => import('./TopicMap'));
const precisionLabels = { site: '已定位城址／遗址', approximate: '概略位置', region: '区域代表点', unknown: '定位精度待核对' };
export function TopicExplorer({ topicSlug }: { topicSlug?: string }) {
  const [pickerOpen,setPickerOpen]=useState(false);
  const [personId, setPersonId] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const invalidRange = from !== '' && to !== '' && Number(from) > Number(to);
  const range=useDebounced(`${from}|${to}`);const [rangeFrom,rangeTo]=range.split('|');
  const invalidSettled=rangeFrom!==''&&rangeTo!==''&&Number(rangeFrom)>Number(rangeTo);
  const params=new URLSearchParams({from:rangeFrom,to:rangeTo});
  if(topicSlug)params.set('topic',topicSlug);if(personId)params.set('person',personId);
  const result=useInfiniteResource<PageResult<Event>>(invalidSettled?undefined:`/catalog/event?${params}`);
  const visible=invalidRange?[]:result.data?.items??[];
  const selectedSummary=visible.find(e=>e.id===selectedId)??visible[0];
  const detail=useResource<Event>(selectedSummary?`/entry/${selectedSummary.id}`:undefined);
  const selected=detail.data??selectedSummary;
  return <section className="space-y-5" aria-label="事件时间线">
    <h2 className="text-2xl font-serif">事件时间线</h2>
    <div className="flex flex-wrap items-end gap-3">
      <details className="max-w-md" onToggle={e=>setPickerOpen(e.currentTarget.open)}><summary className="text-sm cursor-pointer">筛选参与人物{personId?'（已选择）':''}</summary>{pickerOpen&&<RecordPicker table="person" value={personId} admin={false} label="参与人物" onChange={id=>{setPersonId(id);setSelectedId('');}}/>}</details>
      <label className="text-sm">起始年<input aria-label="筛选起始年" type="number" step="1" className="block w-28 border rounded-lg p-2 mt-1" placeholder="不限" value={from} onChange={e => setFrom(e.target.value)} /></label>
      <label className="text-sm">结束年<input aria-label="筛选结束年" type="number" step="1" className="block w-28 border rounded-lg p-2 mt-1" placeholder="不限" value={to} onChange={e => setTo(e.target.value)} /></label>
      <button className="text-sm underline p-2" onClick={() => { setPersonId(''); setFrom(''); setTo(''); setSelectedId(''); }}>重置筛选</button>
    </div>
    <LoadState {...result}/>
    {invalidRange && <p role="alert" className="text-rose-700">起始年不能晚于结束年。</p>}
    <p className="text-sm text-slate-500">已加载 {visible.length} 个事件。时间不详的事件保留在列表末尾。</p>
    <div className="grid lg:grid-cols-[minmax(0,280px)_minmax(0,1fr)] gap-6">
      <ol className="space-y-2 max-h-[460px] overflow-auto" aria-label="专题事件时间线">
        {visible.map(e => <li key={e.id}><button aria-pressed={selected?.id === e.id} className={`w-full text-left rounded-xl p-4 border ${selected?.id === e.id ? 'border-teal-700 bg-teal-50' : 'border-stone-200'}`} onClick={() => setSelectedId(e.id)}><span className="text-xs text-slate-500">{formatDisplayRange(e.start_year, e.end_year)}</span><span className="block font-semibold mt-1">{e.title}</span><span className="block text-sm text-slate-600 mt-1">{e.location_name || '地点待考'}</span></button></li>)}
        {!visible.length && <li className="p-4 text-slate-500">没有符合条件的事件。</li>}
        <li><InfiniteScroll {...result} count={visible.length} disabled={invalidRange || range !== `${from}|${to}`} label="时间线事件"/></li>
      </ol>
      <div className="min-w-0 space-y-4">
        {MAPS_ENABLED && <><p className="text-xs text-slate-500">事件地理层 · 现代底图用于地点定位，与历史疆域底图分别维护。</p>
        <Suspense fallback={<p role="status">正在加载地图…</p>}><TopicMap events={visible} selected={selected} onSelect={setSelectedId} /></Suspense></>}
        {selected && <article className="reading-card" aria-label="选中事件">
          <h3 className="text-xl font-semibold">{selected.title}</h3>
          <p className="text-sm text-slate-500 mt-2">{formatDisplayRange(selected.start_year, selected.end_year)}{selected.time_original ? ` · 原纪年：${selected.time_original}` : ''}</p>
          <p className="mt-3 leading-7">{selected.description || '事件说明正在整理。'}</p>
          <p className="mt-3 text-sm">{selected.location_name || '地点待考'}{selected.location_modern_name ? `（今 ${selected.location_modern_name}）` : ''} · {precisionLabels[selected.location_precision ?? 'unknown']}</p>
          {selected.location_note && <p className="text-sm text-slate-600 mt-2">定位说明：{selected.location_note}</p>}
          <Link to={`/events/${selected.id}`} className="inline-block mt-4 text-teal-700 underline">阅读全文与出处 →</Link>
        </article>}
      </div>
    </div>

  </section>;
}
