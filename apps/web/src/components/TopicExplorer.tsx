import { lazy, Suspense, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Event, Person, RelationshipBundle } from '@histree/shared-types';
import { useResource } from '../hooks/useResource';
import { formatDisplayRange } from '../lib/content';
const TopicMap = lazy(() => import('./TopicMap'));
const precisionLabels = { site: '已定位城址／遗址', approximate: '概略位置', region: '区域代表点', unknown: '定位精度待核对' };
export function TopicExplorer({ events, people }: { events: Event[]; people: Person[] }) {
  const relationships = useResource<RelationshipBundle>('/relationships');
  const [personId, setPersonId] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const invalidRange = from !== '' && to !== '' && Number(from) > Number(to);
  const linkedEvents = new Set(relationships.data?.person_events.filter(r => r.person_id === personId).map(r => r.event_id));
  const visible = events.filter(e => {
    if (invalidRange || (personId && !linkedEvents.has(e.id))) return false;
    // Undated events remain available and are explicitly labelled, never assigned a fabricated year.
    if (e.start_year == null) return true;
    return (from === '' || (e.end_year ?? e.start_year) >= Number(from)) && (to === '' || e.start_year <= Number(to));
  }).sort((a, b) => (a.start_year ?? Infinity) - (b.start_year ?? Infinity) || a.title.localeCompare(b.title, 'zh'));
  const selected = visible.find(e => e.id === selectedId) ?? visible[0];
  const participantIds = new Set(relationships.data?.person_events.filter(r => events.some(e => e.id === r.event_id)).map(r => r.person_id));
  if (!events.length) return <section className="reading-card"><h2 className="text-xl font-serif">时间与地点</h2><p className="mt-3 text-slate-500">关联事件整理后，将在这里展示时间线与地图。</p></section>;
  return <section className="space-y-5" aria-label="时间与地点">
    <h2 className="text-2xl font-serif">时间与地点</h2>
    <div className="flex flex-wrap items-end gap-3">
      <label className="text-sm">参与人物<select className="block border rounded-lg p-2 mt-1 max-w-full" aria-label="参与人物" value={personId} disabled={relationships.loading || !!relationships.error} onChange={e => setPersonId(e.target.value)}><option value="">全部人物</option>{people.filter(p => participantIds.has(p.id)).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      <label className="text-sm">起始年<input aria-label="筛选起始年" type="number" step="1" className="block w-28 border rounded-lg p-2 mt-1" placeholder="不限" value={from} onChange={e => setFrom(e.target.value)} /></label>
      <label className="text-sm">结束年<input aria-label="筛选结束年" type="number" step="1" className="block w-28 border rounded-lg p-2 mt-1" placeholder="不限" value={to} onChange={e => setTo(e.target.value)} /></label>
      <button className="text-sm underline p-2" onClick={() => { setPersonId(''); setFrom(''); setTo(''); setSelectedId(''); }}>重置筛选</button>
    </div>
    {relationships.error && <p className="text-sm text-slate-600">人物筛选暂不可用。<button className="underline ml-2" onClick={relationships.retry}>重试人物关系</button></p>}
    {invalidRange && <p role="alert" className="text-rose-700">起始年不能晚于结束年。</p>}
    <p className="text-sm text-slate-500">显示 {visible.length} 个事件。时间不详的事件保留在列表末尾；地点未定位的事件不落点。</p>
    <div className="grid lg:grid-cols-[minmax(0,280px)_minmax(0,1fr)] gap-6">
      <ol className="space-y-2 max-h-[460px] overflow-auto" aria-label="专题事件时间线">
        {visible.map(e => <li key={e.id}><button aria-pressed={selected?.id === e.id} className={`w-full text-left rounded-xl p-4 border ${selected?.id === e.id ? 'border-teal-700 bg-teal-50' : 'border-stone-200'}`} onClick={() => setSelectedId(e.id)}><span className="text-xs text-slate-500">{formatDisplayRange(e.start_year, e.end_year)}</span><span className="block font-semibold mt-1">{e.title}</span><span className="block text-sm text-slate-600 mt-1">{e.location_name || '地点待考'}</span></button></li>)}
        {!visible.length && <li className="p-4 text-slate-500">没有符合条件的事件。</li>}
      </ol>
      <div className="min-w-0 space-y-4">
        <Suspense fallback={<p role="status">正在加载地图…</p>}><TopicMap events={visible} selected={selected} onSelect={setSelectedId} /></Suspense>
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
