import { useEffect, useMemo, useRef, useState, type PointerEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { Event, PageResult, TimelineOverview } from '@histree/shared-types';
import { timelineYear } from '@histree/shared-types';
import { area, line, curveMonotoneX } from 'd3';
import { useResource } from '../hooks/useResource';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { LoadState } from '../components/Reading';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { formatDisplayYear, formatDisplayRange } from '../lib/content';

import { ordinal, calendar, timeWindow, moveWindow, type TimeWindow } from '../lib/timelineViewport';
export function TimelinePage() {
  const overview = useResource<TimelineOverview>('/timeline/overview');
  return <div className="timeline-page space-y-6"><header className="explore-heading"><p className="eyebrow">HISTREE · 时间探索</p><h1>让历史，沿时间展开</h1><p>拖动画卷，浏览历史；划过年份看大事，点击停下来读。</p></header><LoadState {...overview}/>{overview.data && (overview.data.from !== null && overview.data.to !== null ? <TimelineRiver data={overview.data}/> : <p className="reading-card">还没有已发布且有年份的事件。时间待补充：{overview.data.undated} 条。</p>)}</div>;
}
function TimelineRiver({ data }: { data: TimelineOverview }) {
  const [params, setParams] = useSearchParams();
  let requested: number | undefined;
  try { requested = timelineYear(params.get('year')); } catch { /* Default to the latest recorded starting year. */ }
  const first = ordinal(data.from!), last = ordinal(data.to!);
  const selected = calendar(Math.max(first, Math.min(last, ordinal(requested ?? data.years.at(-1)!.year))));
  const [window, setWindow] = useState<TimeWindow>(() => timeWindow(first, last, ordinal(selected), Math.min(100, last - first)));
  const from = window.from, to = window.to;
  const span = Math.max(1, to - from);
  const focus = ordinal(selected);
  const [hoverYear, setHoverYear] = useState<number | null>(null);
  const previewYear = hoverYear ?? selected;
  const preview = data.years.find(row => row.year === previewYear);
  const [draft, setDraft] = useState('');
  const [invalid, setInvalid] = useState(false);
  const chartRef = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; window: TimeWindow; moved: boolean; mode: 'chart' | 'move' | 'left' | 'right' } | null>(null);
  const suppressClick = useRef(false);
  const wheelRemainder = useRef(0);
  const x = (year: number) => to === from ? 500 : 40 + (ordinal(year) - from) / span * 920;
  const overviewX = (at: number) => 20 + (at - first) / Math.max(1, last - first) * 960;
  function browse(next: TimeWindow) {
    setWindow(next);
    setHoverYear(calendar(Math.round((next.from + next.to) / 2)));
  }
  function pan(shift: number) { browse(moveWindow(window, first, last, shift)); }
  function resize(width: number) { browse(timeWindow(first, last, (from + to) / 2, width)); }
  function reveal(year: number) {
    if (ordinal(year) < from || ordinal(year) > to) setWindow(timeWindow(first, last, ordinal(year), span));
  }
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    // Only horizontal trackpad motion pans; vertical wheel motion keeps page reading natural.
    const wheel = (event: WheelEvent) => {
      if (Math.abs(event.deltaX) <= Math.abs(event.deltaY) || !event.deltaX) return;
      event.preventDefault();
      wheelRemainder.current += event.deltaX / Math.max(1, (chart.getScreenCTM()?.a ?? 1) * 920) * span;
      const shift = Math.trunc(wheelRemainder.current);
      wheelRemainder.current -= shift;
      if (!shift) return;
      setWindow(previous => moveWindow(previous, first, last, shift));
      setHoverYear(null);
    };
    chart.addEventListener('wheel', wheel, { passive: false });
    return () => chart.removeEventListener('wheel', wheel);
  }, [first, last, span]);
  function startDrag(e: PointerEvent<SVGSVGElement>, overview = false) {
    if (e.button !== 0) return;
    suppressClick.current = false;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(e.currentTarget.getScreenCTM()!.inverse());
    const at = first + Math.max(0, Math.min(1, (point.x - 20) / 960)) * (last - first);
    let mode: 'chart' | 'move' | 'left' | 'right' = 'chart';
    let initial = window;
    if (overview) {
      const tolerance = Math.min(20 / (e.currentTarget.getScreenCTM()?.a ?? 1), (overviewX(to) - overviewX(from)) / 3);
      mode = Math.abs(point.x - overviewX(from)) < tolerance ? 'left' : Math.abs(point.x - overviewX(to)) < tolerance ? 'right' : 'move';
      if (at < from || at > to) { initial = timeWindow(first, last, at, span); browse(initial); }
    }
    drag.current = { x: e.clientX, window: initial, moved: false, mode };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function moveDrag(e: PointerEvent<SVGSVGElement>) {
    const start = drag.current;
    if (!start) return false;
    const pixels = e.clientX - start.x;
    if (Math.abs(pixels) > 5) start.moved = true;
    if (!start.moved) return true;
    suppressClick.current = true;
    const isChart = start.mode === 'chart';
    const shift = pixels / Math.max(1, (e.currentTarget.getScreenCTM()?.a ?? 1) * (isChart ? 920 : 960)) * (isChart ? start.window.to - start.window.from : last - first);
    const minimum = Math.min(10, last - first);
    if (start.mode === 'left') browse({ from: Math.max(first, Math.min(start.window.to - minimum, Math.round(start.window.from + shift))), to: start.window.to });
    else if (start.mode === 'right') browse({ from: start.window.from, to: Math.min(last, Math.max(start.window.from + minimum, Math.round(start.window.to + shift))) });
    else browse(moveWindow(start.window, first, last, isChart ? -shift : shift));
    return true;
  }
  function endDrag(e: PointerEvent<SVGSVGElement>) {
    drag.current = null;
    if (e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
  }
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
  const bx = (at: number) => to === from ? 500 : 40 + (at - from) / span * 920;
  const riverPath = area<(typeof bins)[number]>().x(b => bx(b.at)).y0(b => 208 + half(b.count)).y1(b => 208 - half(b.count)).curve(curveMonotoneX)(bins) ?? '';
  const shorePath = line<(typeof bins)[number]>().x(b => bx(b.at)).y(b => 208 - half(b.count)).curve(curveMonotoneX)(bins) ?? '';
  const ticks = [...new Set(Array.from({ length: 7 }, (_, i) => calendar(Math.round(from + span * i / 6))))].filter(y => ordinal(y) <= to);
  function choose(year: number, replace = false) {
    year = calendar(Math.max(first, Math.min(last, ordinal(year))));
    setHoverYear(null);
    if (year === selected) return;
    const next = new URLSearchParams(params); next.set('year', String(year)); setParams(next, { replace });
  }
  function pointYear(e: Pick<PointerEvent<SVGSVGElement>, 'currentTarget' | 'clientX' | 'clientY'>) {
    const matrix = e.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrix.inverse());
    const ratio = Math.max(0, Math.min(1, (point.x - 40) / 920));
    return calendar(Math.round(Math.min(to, from + ratio * span)));
  }
  function jump(e: React.FormEvent) {
    e.preventDefault();
    try { const year = timelineYear(draft); if (ordinal(year) < first || ordinal(year) > last) throw new Error(); choose(year); reveal(year); setInvalid(false); }
    catch { setInvalid(true); }
  }
  return <>
    <section className="timeline-river" aria-label="历史时间图">
      <div className="timeline-topline"><div><p className="eyebrow">编年 · 历史长卷</p><p className="font-serif text-xl mt-2">{formatDisplayYear(data.from)} — {formatDisplayYear(data.to)}</p></div><p className="text-sm text-stone-500">{data.total - data.undated} 条有年事件 · {data.years.length} 个起始年份{data.undated > 0 && ` · ${data.undated} 条时间待补充`}</p></div>
      <div className="timeline-controls"><div className="timeline-zoom"><button className="timeline-button" disabled={to - from >= last - first} onClick={() => browse({ from: first, to: last })}>全程</button><button className="timeline-button" disabled={span >= last - first} onClick={() => resize(span * 2)}>缩小</button><button className="timeline-button" disabled={span <= Math.min(10, last - first)} onClick={() => resize(Math.max(10, span / 2))}>放大</button><span>{to - from + 1} 年视窗</span></div><form onSubmit={jump} className="flex gap-2 items-center"><label className="text-sm" htmlFor="timeline-jump">跳至</label><input id="timeline-jump" aria-label="跳至年份" type="number" placeholder="如 900 或 -403" value={draft} onChange={e => setDraft(e.target.value)} className="timeline-year-input"/><button className="timeline-button">前往</button></form></div>
      {invalid && <p role="alert" className="text-sm text-rose-700">请输入资料范围内的整数年份；公元前用负数，没有公元 0 年。</p>}
      <div className="timeline-stage">
      <aside className="timeline-preview" aria-label="年度大事提要">
        <p className="eyebrow">{hoverYear === null ? '已选年份' : '浏览预览 · 点击年份选中'}</p>
        <div className="timeline-preview-title"><h2>{formatDisplayYear(previewYear)}</h2><span>{preview?.count ?? 0} 条事件开始</span></div>
        {preview?.highlights?.length ? <ul>{preview.highlights.map(event => <li key={event.id}>{event.title}</li>)}</ul> : <p className="text-sm text-stone-500 leading-7">{preview ? '年度提要尚待整理，可点击查看已录入事件。' : '这一年暂无起始事件记录，可点击查看跨年事件。'}</p>}
      </aside>
      <div className="timeline-window-heading"><button className="timeline-button" aria-label="前一段历史" disabled={from <= first} onClick={() => pan(-span * .8)}>← 前一段</button><span>{formatDisplayYear(calendar(from))} — {formatDisplayYear(calendar(to))}</span><button className="timeline-button" aria-label="后一段历史" disabled={to >= last} onClick={() => pan(span * .8)}>后一段 →</button></div>
      <svg ref={chartRef} data-from={from} data-to={to} viewBox="0 90 1000 270" className="timeline-chart" role="img" aria-label="历史时间图，拖动浏览，移动光标预览，点击固定年份" onPointerDown={e => startDrag(e)} onPointerUp={endDrag} onPointerCancel={e => { suppressClick.current = true; endDrag(e); }} onPointerMove={e => { if (!moveDrag(e) && (e.pointerType === 'mouse' || e.pointerType === 'pen')) { const year = pointYear(e); if (year !== undefined) setHoverYear(year); } }} onPointerLeave={() => { if (!drag.current) setHoverYear(null); }} onClick={e => { if (suppressClick.current) { suppressClick.current = false; return; } const year = pointYear(e); if (year !== undefined) choose(year); }}>

        <defs><linearGradient id="river-colour" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#427d73" stopOpacity=".8"/><stop offset="48%" stopColor="#b69255" stopOpacity=".9"/><stop offset="100%" stopColor="#214e47" stopOpacity=".85"/></linearGradient></defs>
        <line x1="40" x2="960" y1="208" y2="208" stroke="#c6d2c9" strokeWidth=".6"/>
        <path d={riverPath} fill="url(#river-colour)"/>
        <path d={area<(typeof bins)[number]>().x(b=>bx(b.at)).y0(b=>208+half(b.count)*.17).y1(b=>208-half(b.count)*.17).curve(curveMonotoneX)(bins)??''} fill="#dfc38c" fillOpacity=".18"/>
        <path d={shorePath} fill="none" stroke="#315d54" strokeWidth=".7" strokeOpacity=".4"/>
        {[.3,.55,.8].map(factor => <path key={factor} d={line<(typeof bins)[number]>().x(b=>bx(b.at)).y(b=>208+half(b.count)*factor).curve(curveMonotoneX)(bins)??''} fill="none" stroke="#fffcf3" strokeOpacity=".35" strokeWidth=".7"/>)}
        {bins.filter(b=>b.count>0).flatMap(b=>Array.from({length:Math.min(13,b.count)},(_,i)=>{
          const seed = (salt: number) => { const n=Math.sin(b.at*37.7+i*113.1+salt*17.3)*43758.5453; return n-Math.floor(n); };
          return <circle key={`${b.at}-${i}`} cx={bx(b.at)+(seed(1)-.5)*Math.min(12,920/span)} cy={208+(seed(2)*2-1)*half(b.count)*.83} r={.7+seed(3)*1.35} fill={i%3?'#ead4a1':'#ffedc3'} fillOpacity={.45+seed(4)*.5}/>;
        }))}
        {hoverYear !== null && ordinal(hoverYear) >= from && ordinal(hoverYear) <= to && <g className="timeline-hover-mark"><line x1={x(hoverYear)} x2={x(hoverYear)} y1="126" y2="304" stroke="#ae8b51" strokeDasharray="3 5" strokeWidth="1"/><circle cx={x(hoverYear)} cy="208" r="5" fill="#d2ab64" stroke="#fffdf6" strokeWidth="2"/></g>}
        {ordinal(selected)>=from && ordinal(selected)<=to && <g><line x1={x(selected)} x2={x(selected)} y1="126" y2="304" stroke="#315e52" strokeWidth="1.5"/><circle cx={x(selected)} cy="208" r="6" fill="#315e52" stroke="#fffdf6" strokeWidth="2"/><rect x={Math.max(40,Math.min(880,x(selected)-40))} y="98" width="80" height="24" rx="12" fill="#315e52"/><text x={Math.max(80,Math.min(920,x(selected)))} y="114" textAnchor="middle" fill="#fffdf6" fontSize="12">{selected<0?`前${-selected}`:selected} · 已选</text></g>}
        <line x1="500" x2="500" y1="132" y2="304" stroke="#847d65" strokeOpacity=".3" strokeDasharray="1 6"/>
        {ticks.map(year => <g key={year}><line x1={x(year)} x2={x(year)} y1="310" y2="316" stroke="#a29b8b"/><text x={x(year)} y="337" textAnchor="middle" fill="#7a786f" fontSize="13">{year < 0 ? `前${-year}` : year}</text></g>)}
      </svg>
      </div>
      <div className="timeline-overview" aria-label="全程时间导航"><div className="timeline-overview-labels"><span>{formatDisplayYear(data.from)}</span><span>全程概览 · 拖动窗口或两端调整范围</span><span>{formatDisplayYear(data.to)}</span></div>
      <svg viewBox="0 0 1000 70" className="timeline-minimap" role="img" aria-label="全程概览，点击定位，拖动窗口或边缘调整范围" onPointerDown={e => startDrag(e, true)} onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={endDrag}>
        <line x1="20" x2="980" y1="36" y2="36" stroke="#dadccb" strokeWidth="2"/>
        {data.years.map(row => <line key={row.year} x1={overviewX(ordinal(row.year))} x2={overviewX(ordinal(row.year))} y1={36 - Math.min(22, 3 + Math.sqrt(row.count) * 1.2)} y2="36" stroke="#81998a" strokeWidth="2"/>)}
        <rect x={overviewX(from)} y="8" width={Math.max(1, overviewX(to) - overviewX(from))} height="48" fill="#bdb08a" fillOpacity=".15" stroke="#8b956e"/>
        {[from, to].map((at, i) => <rect key={i} x={overviewX(at)-3} y="22" width="6" height="20" rx="2" fill="#637e66"/>)}
        <circle cx={overviewX(focus)} cy="36" r="4" fill="#254f44" stroke="#faf8f1" strokeWidth="2"/>
      </svg><div className="timeline-overview-keys"><button className="timeline-button" onClick={() => browse(timeWindow(first, last, first, span))} disabled={from <= first}>卷首</button><button className="timeline-button" onClick={() => { reveal(selected); setHoverYear(null); }}>回到已选年份</button><button className="timeline-button" onClick={() => browse(timeWindow(first, last, last, span))} disabled={to >= last}>卷尾</button></div></div>
      <div className="timeline-selected"><span className="eyebrow">当前停驻</span><h2>{formatDisplayYear(selected)}</h2></div>
      <div className="timeline-slider"><button className="timeline-button" disabled={focus <= first} aria-label="上一年" onClick={() => { const year = calendar(focus - 1); choose(year); reveal(year); }}>←</button><input type="range" aria-label="选择历史年份" min={first} max={last} value={focus} onChange={e => { const year = calendar(Number(e.target.value)); choose(year, true); reveal(year); }}/><button className="timeline-button" disabled={focus >= last} aria-label="下一年" onClick={() => { const year = calendar(focus + 1); choose(year); reveal(year); }}>→</button></div>
      <p className="timeline-note">拖动画卷或概览只浏览，点击年份才更新事件清单。河流厚度与光点表示该时间段开始的已录入事件数量。空白表示暂无记录；跨年事件见下方清单。{bins.length < to - from + 1 && '全景按时间段聚合，放大可查看更多细节。'}</p>
    </section>
    <YearEvents key={selected} year={selected}/>
  </>;
}
function YearEvents({ year }: { year: number }) {
  const result = useInfiniteResource<PageResult<Event>>(`/timeline?year=${year}`);
  const events = result.data?.items ?? [];
  return <section aria-label="当年历史事件" className="min-h-[420px]" aria-busy={result.loading}><div className="flex flex-wrap justify-between gap-3 mb-4"><h2 className="reading-heading mb-0">这一年发生了什么</h2><span className="text-sm text-stone-500">{`${formatDisplayYear(year)} · 包含持续的跨年事件`}</span></div><LoadState {...result}/>{!result.loading && !result.error && !events.length && <p className="reading-card">{formatDisplayYear(year)}暂无已录入事件。可以拖动时间轴，探索相邻年份。</p>}<div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{events.map(event => <Link key={event.id} to={`/events/${event.id}`} className="reading-card timeline-event"><p className="eyebrow">{event.dynasty || '历史事件'} · {formatDisplayRange(event.start_year, event.end_year)}</p><h3 className="font-serif text-xl mt-3 mb-2">{event.title}</h3>{event.time_original && <p className="text-xs text-amber-800 mb-2">{event.time_original}</p>}<p className="text-sm leading-7 text-stone-600 line-clamp-3">{event.description}</p><span className="block mt-4 text-sm text-teal-800">阅读全文与出处 →</span></Link>)}</div><InfiniteScroll {...result} count={events.length} label="当年事件"/></section>;
}
