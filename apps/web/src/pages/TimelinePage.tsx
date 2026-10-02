import { useMemo, useState, type PointerEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { Event, PageResult, TimelineOverview } from '@histree/shared-types';
import { timelineYear } from '@histree/shared-types';
import { useDebounced } from '../hooks/useDebounced';
import { useResource } from '../hooks/useResource';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { LoadState } from '../components/Reading';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { formatDisplayYear, formatDisplayRange } from '../lib/content';

// A continuous axis skips year zero, which does not exist in historical dating.
const ordinal = (year: number) => year < 0 ? year : year - 1;
const calendar = (value: number) => value < 0 ? value : value + 1;
export function TimelinePage() {
  const overview = useResource<TimelineOverview>('/timeline/overview');
  return <div className="space-y-6"><header className="explore-heading"><p className="eyebrow">HISTREE · 时间探索</p><h1>让历史，沿时间展开</h1><p>循着年代，看看同一年发生了什么。</p></header><LoadState {...overview}/>{overview.data && (overview.data.from !== null && overview.data.to !== null ? <TimelineRiver data={overview.data}/> : <p className="reading-card">还没有已发布且有年份的事件。时间待补充：{overview.data.undated} 条。</p>)}</div>;
}
function TimelineRiver({ data }: { data: TimelineOverview }) {
  const [params, setParams] = useSearchParams();
  let requested: number | undefined;
  try { requested = timelineYear(params.get('year')); } catch { /* Default to the latest recorded starting year. */ }
  const first = ordinal(data.from!), last = ordinal(data.to!);
  const selected = calendar(Math.max(first, Math.min(last, ordinal(requested ?? data.years.at(-1)!.year))));
  const [zoomCenter, setZoomCenter] = useState<number | null>(null);
  const zoom = zoomCenter !== null;
  const settledYear = useDebounced(selected, 200);
  const [draft, setDraft] = useState('');
  const [invalid, setInvalid] = useState(false);
  const focus = ordinal(selected);
  const from = zoom ? Math.max(first, zoomCenter! - 25) : first;
  const to = zoom ? Math.min(last, zoomCenter! + 25) : last;
  const span = Math.max(1, to - from);
  const x = (year: number) => 40 + (ordinal(year) - from) / span * 920;
  const bins = useMemo(() => {
    const size = Math.max(1, Math.ceil((to - from + 1) / 100));
    const values = Array.from({ length: Math.ceil((to - from + 1) / size) }, (_, i) => ({ at: from + i * size, count: 0 }));
    for (const row of data.years) {
      const index = Math.floor((ordinal(row.year) - from) / size);
      if (ordinal(row.year) >= from && ordinal(row.year) <= to) values[index].count += row.count;
    }
    return values;
  }, [data.years, from, to]);
  const peak = Math.max(1, ...bins.map(b => b.count));
  const half = (count: number) => count ? 12 + 100 * Math.sqrt(count / peak) : 0;
  const bx = (at: number) => 40 + (at - from) / span * 920;
  const top = bins.map(b => `${bx(b.at)},${180 - half(b.count)}`).join(' L ');
  const bottom = [...bins].reverse().map(b => `${bx(b.at)},${180 + half(b.count)}`).join(' L ');
  const ticks = [...new Set(Array.from({ length: 7 }, (_, i) => calendar(Math.round(from + span * i / 6))))].filter(y => ordinal(y) <= to);
  function choose(year: number, replace = false) {
    if (year === selected) return;
    const next = new URLSearchParams(params); next.set('year', String(year)); setParams(next, { replace });
  }
  function pointYear(e: Pick<PointerEvent<SVGSVGElement>, 'currentTarget' | 'clientX' | 'clientY'>) {
    const matrix = e.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrix.inverse());
    const ratio = Math.max(0, Math.min(1, (point.x - 40) / 920));
    choose(calendar(Math.round(from + ratio * span)), true);
  }
  function jump(e: React.FormEvent) {
    e.preventDefault();
    try { const year = timelineYear(draft); if (ordinal(year) < first || ordinal(year) > last) throw new Error(); choose(year); setInvalid(false); }
    catch { setInvalid(true); }
  }
  return <>
    <section className="timeline-river" aria-label="历史时间图">
      <div className="timeline-topline"><div><p className="eyebrow">历史长河 · 已发布资料</p><p className="font-serif text-xl mt-2">{formatDisplayYear(data.from)} — {formatDisplayYear(data.to)}</p></div><p className="text-sm text-stone-500">{data.total - data.undated} 条有年事件 · {data.years.length} 个起始年份{data.undated > 0 && ` · ${data.undated} 条时间待补充`}</p></div>
      <div className="timeline-controls"><button className="timeline-button" aria-pressed={zoom} onClick={() => setZoomCenter(zoom ? null : focus)}>{zoom ? '查看全部年代' : '放大当前年代'}</button><form onSubmit={jump} className="flex gap-2 items-center"><label className="text-sm" htmlFor="timeline-jump">跳至</label><input id="timeline-jump" aria-label="跳至年份" type="number" placeholder="如 900 或 -403" value={draft} onChange={e => setDraft(e.target.value)} className="timeline-year-input"/><button className="timeline-button">前往</button></form></div>
      {invalid && <p role="alert" className="text-sm text-rose-700">请输入资料范围内的整数年份；公元前用负数，没有公元 0 年。</p>}
      <svg viewBox="0 0 1000 360" className="timeline-chart" role="img" aria-label="事件起始年份密度图，移动光标或使用下方滑块选择年份" onPointerMove={e => { if (e.pointerType === 'mouse' || e.pointerType === 'pen') pointYear(e); }} onClick={e => pointYear(e)}>
        <defs><linearGradient id="river-colour" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#72968c"/><stop offset="45%" stopColor="#d99a53"/><stop offset="75%" stopColor="#c8783e"/><stop offset="100%" stopColor="#72968c"/></linearGradient></defs>
        <line x1="40" x2="960" y1="180" y2="180" stroke="#d9d2bf" strokeDasharray="3 7"/>
        <path d={`M ${top} L ${bottom} Z`} fill="url(#river-colour)" fillOpacity=".8" stroke="#8daba1" strokeWidth="1.5"/>
        {bins.filter(b => b.count).map(b => <g key={b.at}><circle cx={bx(b.at)} cy={180 - half(b.count) - 14} r={3 + Math.sqrt(b.count / peak) * 6} fill="#bd9149" fillOpacity=".8"/><circle cx={bx(b.at)} cy={180 - half(b.count) - 14} r={9 + Math.sqrt(b.count / peak) * 11} fill="none" stroke="#cfb476" strokeOpacity=".35"/><title>{formatDisplayYear(calendar(b.at))}起的分段：{b.count} 条事件开始</title></g>)}
        <line x1={x(selected)} x2={x(selected)} y1="35" y2="312" stroke="#285c60" strokeWidth="1.5"/><path d={`M ${x(selected)-5} 35 L ${x(selected)+5} 35 L ${x(selected)} 43 Z`} fill="#285c60"/>
        {ticks.map(year => <g key={year}><line x1={x(year)} x2={x(year)} y1="310" y2="316" stroke="#a29b8b"/><text x={x(year)} y="337" textAnchor="middle" fill="#7a786f" fontSize="13">{year < 0 ? `前${-year}` : year}</text></g>)}
      </svg>
      <div className="timeline-selected"><span className="eyebrow">此刻，历史走到</span><h2>{formatDisplayYear(selected)}</h2></div>
      <div className="timeline-slider"><button className="timeline-button" disabled={focus <= first} aria-label="上一年" onClick={() => choose(calendar(focus - 1))}>←</button><input type="range" aria-label="选择历史年份" min={first} max={last} value={focus} onChange={e => choose(calendar(Number(e.target.value)), true)}/><button className="timeline-button" disabled={focus >= last} aria-label="下一年" onClick={() => choose(calendar(focus + 1))}>→</button></div>
      <p className="timeline-note">河流厚度与金色圆点表示该时间段开始的已录入事件数量。空白表示暂无记录；跨年事件见下方清单。{bins.length < to - from + 1 && '全景按时间段聚合，放大可查看更多细节。'}</p>
    </section>
    <YearEvents key={settledYear} year={settledYear} pending={settledYear !== selected}/>
  </>;
}
function YearEvents({ year, pending }: { year: number; pending: boolean }) {
  const result = useInfiniteResource<PageResult<Event>>(`/timeline?year=${year}`);
  const events = result.data?.items ?? [];
  return <section aria-label="当年历史事件" className="min-h-[420px]" aria-busy={pending || result.loading}><div className="flex flex-wrap justify-between gap-3 mb-4"><h2 className="reading-heading mb-0">这一年发生了什么</h2><span className="text-sm text-stone-500">{pending ? '正在切换年份…' : `${formatDisplayYear(year)} · 包含持续的跨年事件`}</span></div><LoadState {...result}/>{!result.loading && !result.error && !events.length && <p className="reading-card">{formatDisplayYear(year)}暂无已录入事件。可以拖动时间轴，探索相邻年份。</p>}<div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{events.map(event => <Link key={event.id} to={`/events/${event.id}`} className="reading-card timeline-event"><p className="eyebrow">{event.dynasty || '历史事件'} · {formatDisplayRange(event.start_year, event.end_year)}</p><h3 className="font-serif text-xl mt-3 mb-2">{event.title}</h3>{event.time_original && <p className="text-xs text-amber-800 mb-2">{event.time_original}</p>}<p className="text-sm leading-7 text-stone-600 line-clamp-3">{event.description}</p><span className="block mt-4 text-sm text-teal-800">阅读全文与出处 →</span></Link>)}</div><InfiniteScroll {...result} count={events.length} label="当年事件"/></section>;
}
