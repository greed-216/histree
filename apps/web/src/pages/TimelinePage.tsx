import { useMemo, useState, type PointerEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { Event, PageResult, TimelineOverview } from '@histree/shared-types';
import { timelineYear } from '@histree/shared-types';
import { area, line, curveMonotoneX } from 'd3';
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
  return <div className="space-y-6"><header className="explore-heading"><p className="eyebrow">HISTREE · 时间探索</p><h1>让历史，沿时间展开</h1><p>划过年代，预览一年大事；点击年份，停下来读历史。</p></header><LoadState {...overview}/>{overview.data && (overview.data.from !== null && overview.data.to !== null ? <TimelineRiver data={overview.data}/> : <p className="reading-card">还没有已发布且有年份的事件。时间待补充：{overview.data.undated} 条。</p>)}</div>;
}
function TimelineRiver({ data }: { data: TimelineOverview }) {
  const [params, setParams] = useSearchParams();
  let requested: number | undefined;
  try { requested = timelineYear(params.get('year')); } catch { /* Default to the latest recorded starting year. */ }
  const first = ordinal(data.from!), last = ordinal(data.to!);
  const selected = calendar(Math.max(first, Math.min(last, ordinal(requested ?? data.years.at(-1)!.year))));
  const [zoomCenter, setZoomCenter] = useState<number | null>(null);
  const zoom = zoomCenter !== null;
  const [hoverYear, setHoverYear] = useState<number | null>(null);
  const previewYear = hoverYear ?? selected;
  const preview = data.years.find(row => row.year === previewYear);
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
  const half = (count: number) => count ? 8 + 72 * Math.sqrt(count / peak) : 0;
  const bx = (at: number) => 40 + (at - from) / span * 920;
  const riverPath = area<(typeof bins)[number]>().x(b => bx(b.at)).y0(b => 208 + half(b.count)).y1(b => 208 - half(b.count)).curve(curveMonotoneX)(bins) ?? '';
  const shorePath = line<(typeof bins)[number]>().x(b => bx(b.at)).y(b => 208 - half(b.count)).curve(curveMonotoneX)(bins) ?? '';
  const ticks = [...new Set(Array.from({ length: 7 }, (_, i) => calendar(Math.round(from + span * i / 6))))].filter(y => ordinal(y) <= to);
  function choose(year: number, replace = false) {
    setHoverYear(null);
    if (year === selected) return;
    const next = new URLSearchParams(params); next.set('year', String(year)); setParams(next, { replace });
  }
  function pointYear(e: Pick<PointerEvent<SVGSVGElement>, 'currentTarget' | 'clientX' | 'clientY'>) {
    const matrix = e.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrix.inverse());
    const ratio = Math.max(0, Math.min(1, (point.x - 40) / 920));
    return calendar(Math.round(from + ratio * span));
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
      <div className="timeline-stage">
      <aside className="timeline-preview" aria-label="年度大事提要">
        <p className="eyebrow">{hoverYear === null ? '已选年份' : '悬停预览 · 点击选中'}</p>
        <div className="timeline-preview-title"><h2>{formatDisplayYear(previewYear)}</h2><span>{preview?.count ?? 0} 条事件开始</span></div>
        {preview?.highlights?.length ? <ul>{preview.highlights.map(event => <li key={event.id}>{event.title}</li>)}</ul> : <p className="text-sm text-stone-500 leading-7">{preview ? '年度提要尚待整理，可点击查看已录入事件。' : '这一年暂无起始事件记录，可点击查看跨年事件。'}</p>}
      </aside>
      <svg viewBox="0 90 1000 270" className="timeline-chart" role="img" aria-label="历史时间图，移动光标预览，点击固定年份" onPointerMove={e => { if (e.pointerType === 'mouse' || e.pointerType === 'pen') { const year = pointYear(e); if (year !== undefined) setHoverYear(year); } }} onPointerLeave={() => setHoverYear(null)} onClick={e => { const year = pointYear(e); if (year !== undefined) choose(year); }}>
        <defs><linearGradient id="river-colour" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7caaa0" stopOpacity=".32"/><stop offset="48%" stopColor="#d6b478" stopOpacity=".8"/><stop offset="100%" stopColor="#436f66" stopOpacity=".38"/></linearGradient></defs>
        <line x1="40" x2="960" y1="208" y2="208" stroke="#c6d2c9" strokeWidth=".6"/>
        <path d={riverPath} fill="url(#river-colour)"/>
        <path d={shorePath} fill="none" stroke="#648d81" strokeWidth="1" strokeOpacity=".65"/>
        {[.3,.55,.8].map(factor => <path key={factor} d={line<(typeof bins)[number]>().x(b=>bx(b.at)).y(b=>208+half(b.count)*factor).curve(curveMonotoneX)(bins)??''} fill="none" stroke="#fffcf3" strokeOpacity=".35" strokeWidth=".7"/>)}
        {bins.filter(b=>b.count>0).flatMap(b=>Array.from({length:Math.min(7,b.count)},(_,i)=><circle key={`${b.at}-${i}`} cx={bx(b.at)+(i%3-1)*1.8} cy={208 + (i/Math.max(1,Math.min(7,b.count)-1)*2-1)*half(b.count)*.65} r="1.6" fill="#a87937" fillOpacity=".55"/>))}
        {hoverYear !== null && <g className="timeline-hover-mark"><line x1={x(hoverYear)} x2={x(hoverYear)} y1="126" y2="304" stroke="#ae8b51" strokeDasharray="3 5" strokeWidth="1"/><circle cx={x(hoverYear)} cy="208" r="5" fill="#d2ab64" stroke="#fffdf6" strokeWidth="2"/></g>}
        {ordinal(selected)>=from && ordinal(selected)<=to && <g><line x1={x(selected)} x2={x(selected)} y1="126" y2="304" stroke="#315e52" strokeWidth="1.5"/><circle cx={x(selected)} cy="208" r="6" fill="#315e52" stroke="#fffdf6" strokeWidth="2"/><rect x={Math.max(40,Math.min(880,x(selected)-40))} y="98" width="80" height="24" rx="12" fill="#315e52"/><text x={Math.max(80,Math.min(920,x(selected)))} y="114" textAnchor="middle" fill="#fffdf6" fontSize="12">{selected<0?`前${-selected}`:selected} · 已选</text></g>}
        {ticks.map(year => <g key={year}><line x1={x(year)} x2={x(year)} y1="310" y2="316" stroke="#a29b8b"/><text x={x(year)} y="337" textAnchor="middle" fill="#7a786f" fontSize="13">{year < 0 ? `前${-year}` : year}</text></g>)}
      </svg>
      </div>
      <div className="timeline-selected"><span className="eyebrow">停驻于 · 点击图中年份切换</span><h2>{formatDisplayYear(selected)}</h2></div>
      <div className="timeline-slider"><button className="timeline-button" disabled={focus <= first} aria-label="上一年" onClick={() => choose(calendar(focus - 1))}>←</button><input type="range" aria-label="选择历史年份" min={first} max={last} value={focus} onChange={e => choose(calendar(Number(e.target.value)), true)}/><button className="timeline-button" disabled={focus >= last} aria-label="下一年" onClick={() => choose(calendar(focus + 1))}>→</button></div>
      <p className="timeline-note">河流厚度与金色圆点表示该时间段开始的已录入事件数量。空白表示暂无记录；跨年事件见下方清单。{bins.length < to - from + 1 && '全景按时间段聚合，放大可查看更多细节。'}</p>
    </section>
    <YearEvents key={selected} year={selected}/>
  </>;
}
function YearEvents({ year }: { year: number }) {
  const result = useInfiniteResource<PageResult<Event>>(`/timeline?year=${year}`);
  const events = result.data?.items ?? [];
  return <section aria-label="当年历史事件" className="min-h-[420px]" aria-busy={result.loading}><div className="flex flex-wrap justify-between gap-3 mb-4"><h2 className="reading-heading mb-0">这一年发生了什么</h2><span className="text-sm text-stone-500">{`${formatDisplayYear(year)} · 包含持续的跨年事件`}</span></div><LoadState {...result}/>{!result.loading && !result.error && !events.length && <p className="reading-card">{formatDisplayYear(year)}暂无已录入事件。可以拖动时间轴，探索相邻年份。</p>}<div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{events.map(event => <Link key={event.id} to={`/events/${event.id}`} className="reading-card timeline-event"><p className="eyebrow">{event.dynasty || '历史事件'} · {formatDisplayRange(event.start_year, event.end_year)}</p><h3 className="font-serif text-xl mt-3 mb-2">{event.title}</h3>{event.time_original && <p className="text-xs text-amber-800 mb-2">{event.time_original}</p>}<p className="text-sm leading-7 text-stone-600 line-clamp-3">{event.description}</p><span className="block mt-4 text-sm text-teal-800">阅读全文与出处 →</span></Link>)}</div><InfiniteScroll {...result} count={events.length} label="当年事件"/></section>;
}
