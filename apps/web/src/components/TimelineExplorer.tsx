import { HistoryScrollBackdrop } from "../components/HistoryScrollBackdrop";
import "../styles/timeline-ancient.css";
import { TimelinePeriodBands } from "./TimelinePeriodBands";
import { polityReferences } from "../lib/timelinePeriods";
import { historyScroll, initialScrollWindow, minimumScrollSpan, nextScrollZoomSpan, scrollSceneLayout, scrollYearX,
  ancientChapters, annualStart, scrollStart, scrollPositionX, scrollPositionLabel, chapterAtPosition, chapterById, type AncientChapter } from "../lib/historyScroll";
import { guideHighlights } from "../lib/historyGuides";
import { useEffect, useMemo, useRef, useState, type PointerEvent, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type {
  Event,
  PageResult,
  TimelineOverview,
} from "@histree/shared-types";
import { timelineYear } from "@histree/shared-types";
import { area, line, curveMonotoneX } from "d3";
import { useResource } from "../hooks/useResource";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { LoadState } from "../components/Reading";
import { InfiniteScroll } from "../components/InfiniteScroll";
import { formatDisplayYear, formatDisplayRange } from "../lib/content";

import {
  ordinal,
  calendar,
  timeWindow,
  moveWindow,
  type TimeWindow,
} from "../lib/timelineViewport";
export function TimelineExplorer({ compact = false, loadingFallback }: { compact?: boolean; loadingFallback?: ReactNode }) {
  const overview = useResource<TimelineOverview>("/timeline/overview");
  return (
    <div className={compact ? "timeline-page timeline-home" : "timeline-page"}>
      {overview.loading && loadingFallback ? loadingFallback : <LoadState {...overview} />}
      {overview.data &&
        (overview.data.from !== null && overview.data.to !== null ? (
          <TimelineRiver data={overview.data} compact={compact} />
        ) : (
          <p className="reading-card">
            还没有已发布且有年份的事件。时间待补充：{overview.data.undated} 条。
          </p>
        ))}
    </div>
  );
}
function TimelineRiver({
  data,
  compact,
}: {
  data: TimelineOverview;
  compact: boolean;
}) {
  const [params, setParams] = useSearchParams();
  let requested: number | undefined;
  try {
    requested = timelineYear(params.get("year"));
  } catch {
    /* Default to the latest recorded starting year. */
  }
  const first = scrollStart,
    last = ordinal(Math.max(historyScroll.to_year, data.to!));
  const selectedChapter = chapterById(params.get("era"));
  const preferred = compact
    ? (data.years.find((row) => row.year === 907)?.year ??
      data.years.at(-1)!.year)
    : data.years.at(-1)!.year;
  const selected = calendar(
    Math.max(annualStart, Math.min(last, ordinal(requested ?? preferred))),
  );
  const focus = selectedChapter ? (selectedChapter.from + selectedChapter.to) / 2 : ordinal(selected);
  const [window, setWindow] = useState<TimeWindow>(() =>
    selectedChapter ? timeWindow(first, last, focus, selectedChapter.to - selectedChapter.from + 20)
      : initialScrollWindow(selected, data.from!, data.to!, compact),
  );
  useEffect(() => {
    setWindow(previous => focus >= previous.from && focus <= previous.to
      ? previous : timeWindow(first, last, focus, previous.to - previous.from));
    setHoverYear(null);
    setHoverChapter(null);
  }, [focus, first, last]);
  const from = window.from,
    to = window.to;
  const span = Math.max(1, to - from);
  const [chartWidth, setChartWidth] = useState(800);
  const [chartHeightBudget, setChartHeightBudget] = useState(280);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [politiesExpanded, setPolitiesExpanded] = useState(false);
  const [periodNavigation, setPeriodNavigation] = useState(0);
  const [viewMode, setViewMode] = useState<"scroll" | "detail">("scroll");
  const [artPosition, setArtPosition] = useState(.5);
  const canvasRef = useRef<HTMLDivElement>(null);
  const initialCanvasMeasured = useRef(false);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width <= 0 || height < 80) return;
      setChartWidth(width);
      setChartHeightBudget(height);
      if (!initialCanvasMeasured.current) {
        initialCanvasMeasured.current = true;
        setWindow(timeWindow(first, last, focus,
          selectedChapter ? Math.max(minimumScrollSpan(width, height), selectedChapter.to - selectedChapter.from + 20)
            : minimumScrollSpan(width, height)));
      }
    });
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [first, last, focus, selectedChapter]);
  const scene=scrollSceneLayout(from,to,chartWidth,chartHeightBudget,viewMode);
  const riverY=scene.riverY;
  const [hoverYear, setHoverYear] = useState<number | null>(null);
  const [hoverChapter, setHoverChapter] = useState<AncientChapter | null>(null);
  const previewChapter = hoverChapter ?? (hoverYear === null ? selectedChapter : undefined);
  const previewYear = hoverYear ?? selected;
  const recordedPreview = data.years.find((row) => row.year === previewYear);
  const selectedHighlights = guideHighlights(previewYear);
  const preview = recordedPreview
    ? {
        ...recordedPreview,
        highlights: selectedHighlights.length
          ? selectedHighlights
          : recordedPreview.highlights,
      }
    : undefined;
  const [draft, setDraft] = useState("");
  const [invalid, setInvalid] = useState(false);
  const chartRef = useRef<SVGSVGElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{
    x: number;
    y: number;
    artPosition: number;
    artTravel: number;
    horizontal: boolean;
    window: TimeWindow;
    moved: boolean;
    mode: "chart" | "move" | "left" | "right";
  } | null>(null);
  const suppressClick = useRef(false);
  const wheelRemainder = useRef(0);
  const x = (year: number) => scrollYearX(year,from,to);
  const positionX = (position: number) => scrollPositionX(position,from,to);
  const overviewX = (at: number) =>
    20 + ((at - first) / Math.max(1, last - first)) * 960;
  function browse(next: TimeWindow) {
    setWindow(next);
    previewPosition((next.from + next.to) / 2);
  }
  function previewPosition(position: number) {
    const chapter = chapterAtPosition(position);
    setHoverChapter(chapter ?? null);
    setHoverYear(chapter ? null : calendar(Math.max(annualStart, Math.round(position))));
  }
  function browseChapter(chapter: AncientChapter) {
    setPeriodNavigation(value => value + 1);
    browse(timeWindow(first, last, (chapter.from + chapter.to) / 2, Math.max(scene.minimumSpan, (chapter.to - chapter.from) * 1.12)));
    setHoverChapter(chapter);setHoverYear(null);
  }
  function chooseChapter(chapter: AncientChapter) {
    const next = new URLSearchParams(params);
    next.set("era", chapter.id);
    setHoverYear(null);setHoverChapter(null);
    setParams(next);
  }
  function pan(shift: number) {
    browse(moveWindow(window, first, last, shift));
  }
  function resize(width: number) {
    browse(timeWindow(first, last, (from + to) / 2, width));
  }
  function browsePeriod(start: number, end: number) {
    setPeriodNavigation(value => value + 1);
    const width = Math.max(10, (ordinal(end) - ordinal(start)) * 1.12);
    browse(timeWindow(first, last, (ordinal(start) + ordinal(end)) / 2, width));
  }
  function reveal(year: number) {
    if (ordinal(year) < from || ordinal(year) > to)
      setWindow(timeWindow(first, last, ordinal(year), span));
  }
  useEffect(() => {
    const chart = chartRef.current;
    const stage = stageRef.current;
    if (!chart || !stage) return;
    // Only horizontal trackpad motion pans; vertical wheel motion keeps page reading natural.
    const wheel = (event: WheelEvent) => {
      if (!(event.target instanceof Element) || !event.target.closest('.timeline-period-bands, .timeline-chart')) return;
      if (event.ctrlKey) return;
      if (Math.abs(event.deltaX) <= Math.abs(event.deltaY) || !event.deltaX)
        return;
      event.preventDefault();
      wheelRemainder.current +=
        (event.deltaX / Math.max(1, (chart.getScreenCTM()?.a ?? 1) * 920)) *
        span;
      const shift = Math.trunc(wheelRemainder.current);
      wheelRemainder.current -= shift;
      if (!shift) return;
      setWindow((previous) => moveWindow(previous, first, last, shift));
      setHoverYear(null);
      setHoverChapter(null);
    };
    stage.addEventListener("wheel", wheel, { passive: false });
    return () => stage.removeEventListener("wheel", wheel);
  }, [first, last, span]);
  function startDrag(e: PointerEvent<SVGSVGElement>, overview = false) {
    if (e.button !== 0) return;
    suppressClick.current = false;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(
      e.currentTarget.getScreenCTM()!.inverse(),
    );
    const at =
      first + Math.max(0, Math.min(1, (point.x - 20) / 960)) * (last - first);
    let mode: "chart" | "move" | "left" | "right" = "chart";
    let initial = window;
    if (overview) {
      const tolerance = Math.min(
        20 / (e.currentTarget.getScreenCTM()?.a ?? 1),
        (overviewX(to) - overviewX(from)) / 3,
      );
      mode =
        Math.abs(point.x - overviewX(from)) < tolerance
          ? "left"
          : Math.abs(point.x - overviewX(to)) < tolerance
            ? "right"
            : "move";
      if (at < from || at > to) {
        initial = timeWindow(first, last, at, span);
        browse(initial);
      }
    }
    drag.current = { x: e.clientX, y: e.clientY, artPosition,
      artTravel: !overview && scene.cropped
        ? (scene.naturalHeight - scene.height) * (e.currentTarget.getScreenCTM()?.a ?? 1) : 0,
      horizontal: false, window: initial, moved: false, mode };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function moveDrag(e: PointerEvent<SVGSVGElement>) {
    const start = drag.current;
    if (!start) return false;
    const pixels = e.clientX - start.x;
    const verticalPixels = e.clientY - start.y;
    const isChart = start.mode === "chart";
    if (Math.abs(pixels) > 5) start.horizontal = true;
    if (Math.hypot(pixels, isChart ? verticalPixels : 0) > 5) start.moved = true;
    if (!start.moved) return true;
    suppressClick.current = true;
    if (isChart && start.artTravel > 0) {
      setArtPosition(Math.max(0, Math.min(1, start.artPosition - verticalPixels / start.artTravel)));
    }
    if (isChart && !start.horizontal) {
      setHoverYear(null);
      return true;
    }
    const shift =
      (pixels /
        Math.max(
          1,
          (e.currentTarget.getScreenCTM()?.a ?? 1) * (isChart ? 920 : 960),
        )) *
      (isChart ? start.window.to - start.window.from : last - first);
    const minimum = Math.min(10, last - first);
    if (start.mode === "left")
      browse({
        from: Math.max(
          first,
          Math.min(
            start.window.to - minimum,
            Math.round(start.window.from + shift),
          ),
        ),
        to: start.window.to,
      });
    else if (start.mode === "right")
      browse({
        from: start.window.from,
        to: Math.min(
          last,
          Math.max(
            start.window.from + minimum,
            Math.round(start.window.to + shift),
          ),
        ),
      });
    else
      browse(moveWindow(start.window, first, last, isChart ? -shift : shift));
    return true;
  }
  function endDrag(e: PointerEvent<SVGSVGElement>) {
    drag.current = null;
    if (e.currentTarget.hasPointerCapture(e.pointerId))
      e.currentTarget.releasePointerCapture(e.pointerId);
  }
  const bins = useMemo(() => {
    const size = Math.max(1, Math.ceil((to - from + 1) / 100));
    const bucketFrom = Math.max(annualStart, Math.ceil(from));
    const bucketTo = Math.floor(to);
    const values = Array.from(
      { length: Math.max(0, Math.ceil((bucketTo - bucketFrom + 1) / size)) },
      (_, i) => ({ at: bucketFrom + i * size, count: 0 }),
    );
    for (const row of data.years) {
      if (row.year < historyScroll.annual_start_year) continue;
      const index = Math.floor((ordinal(row.year) - bucketFrom) / size);
      if (ordinal(row.year) >= bucketFrom && ordinal(row.year) <= bucketTo)
        values[index].count += row.count;
    }
    return values;
  }, [data.years, from, to]);
  const peak = Math.max(1, ...bins.map((b) => b.count));
  const pointScale = scene.mode === "detail" ? scene.viewBoxHeight / 270 : 1;
  const half = (count: number) => count
    ? scene.mode === "detail" ? (8 + 72 * Math.sqrt(count / peak)) * pointScale
      : 2 + 16 * Math.sqrt(count / peak)
    : 0;
  const bx = (at: number) =>
    to === from ? 500 : 40 + ((at - from) / span) * 920;
  const riverPath =
    area<(typeof bins)[number]>()
      .x((b) => bx(b.at))
      .y0((b) => riverY + half(b.count))
      .y1((b) => riverY - half(b.count))
      .curve(curveMonotoneX)(bins) ?? "";
  const shorePath =
    line<(typeof bins)[number]>()
      .x((b) => bx(b.at))
      .y((b) => riverY - half(b.count))
      .curve(curveMonotoneX)(bins) ?? "";
  const overviewTicks = [
    ...new Set(
      Array.from({ length: 7 }, (_, i) =>
        calendar(Math.round(from + (span * i) / 6)),
      ),
    ),
  ].filter((y) => y >= historyScroll.annual_start_year && ordinal(y) <= to);
  const boundaries = [...historyScroll.periods.map(period => period.from_year), historyScroll.to_year]
    .filter(year => ordinal(year) >= from && ordinal(year) <= to);
  const candidates = [...boundaries, ...overviewTicks];
  const ticks: number[] = [];
  for (const year of candidates) {
    if (ticks.every(other => Math.abs(x(year) - x(other)) * chartWidth / 1000 >= 58)) ticks.push(year);
  }
  ticks.sort((a, b) => a - b);
  const binYears = Math.max(1, Math.ceil((to - from + 1) / 100));
  function choose(year: number, replace = false) {
    year = calendar(Math.max(annualStart, Math.min(last, ordinal(year))));
    setHoverYear(null);
    setHoverChapter(null);
    if (year === selected && !selectedChapter) return;
    const next = new URLSearchParams(params);
    next.delete("era");
    next.set("year", String(year));
    setParams(next, { replace });
  }
  function pointPosition(
    e: Pick<
      PointerEvent<SVGSVGElement>,
      "currentTarget" | "clientX" | "clientY"
    >,
  ) {
    const matrix = e.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(
      matrix.inverse(),
    );
    const ratio = Math.max(0, Math.min(1, (point.x - 40) / 920));
    return Math.min(to, from + ratio * span);
  }
  function jump(e: React.FormEvent) {
    e.preventDefault();
    try {
      const year = timelineYear(draft);
      if (ordinal(year) < annualStart || ordinal(year) > last) throw new Error();
      choose(year);
      reveal(year);
      setInvalid(false);
    } catch {
      setInvalid(true);
    }
  }
  const yearJump = (
    <form onSubmit={jump} className="flex gap-2 items-center">
      <label className="text-sm" htmlFor="timeline-jump">
        跳至
      </label>
      <input
        id="timeline-jump"
        aria-label="跳至年份"
        type="number"
        placeholder="如 900 或 -403"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        className="timeline-year-input"
      />
      <button className="timeline-button">前往</button>
    </form>
  );

  return (
    <>
      <section
        className={`timeline-river ${compact ? "timeline-river-compact" : ""}`}
        aria-label="历史时间图"
        data-polities-expanded={politiesExpanded}
      >
        <div className="timeline-topline">
          <div>
            <p className="eyebrow">历史画卷 · 神话时代—1912年</p>
            <p className="font-serif text-xl mt-2">
              史事记录分布：{formatDisplayYear(data.from)} —{" "}
              {formatDisplayYear(data.to)}
            </p>
          </div>
          <p className="text-sm text-stone-500">
            {data.total - data.undated} 条有年事件
            {!compact && ` · ${data.undated} 条时间待补充`}
          </p>
        </div>
        <div className="timeline-controls">
          <div className="timeline-zoom">
            <button
              className="timeline-button"
              aria-label="画卷全景"
              disabled={to - from >= last - first}
              onClick={() => browse({ from: first, to: last })}
            >
              <span className="timeline-panoramic-full">画卷</span>全景
            </button>
            <button
              className="timeline-button"
              disabled={span >= last - first}
              onClick={() => resize(nextScrollZoomSpan(span, false))}
            >
              缩小
            </button>
            <button
              className="timeline-button"
              disabled={span <= Math.min(10, last - first)}
              onClick={() => resize(nextScrollZoomSpan(span, true))}
            >
              放大
            </button>
            <span>{from < annualStart ? "时代与年份视窗" : `${Math.round(to - from + 1)} 年视窗`}</span>

          </div>
          <details className="timeline-more">
            <summary><span className="timeline-options-full">浏览</span>选项</summary>
            <div className="timeline-secondary-tools">
            <button
              className="timeline-button"
              onClick={() =>
                browse(
                  timeWindow(
                    first,
                    last,
                    (ordinal(data.from!) + ordinal(data.to!)) / 2,
                    Math.max(10, ordinal(data.to!) - ordinal(data.from!)),
                  ),
                )
              }
            >
              看已录史事
            </button>
            </div>
          </details>
          <details className="timeline-jump">
            <summary>跳至年份</summary>
            {yearJump}
          </details>
        </div>
        {invalid && (
          <p role="alert" className="text-sm text-rose-700">
            请输入前841年至画卷末尾的整数年份；公元前用负数，没有公元 0 年。更早内容请按时代浏览。
          </p>
        )}
        <div className="timeline-navigation">
          <div className="timeline-view-switch" role="group" aria-label="时间图浏览方式">
            <button type="button" aria-label="画卷浏览" aria-pressed={viewMode === "scroll"}
              onClick={() => setViewMode("scroll")}>画卷</button>
            <button type="button" aria-label="史事细览" aria-pressed={viewMode === "detail"}
              onClick={() => setViewMode("detail")}>史事</button>
          </div>
        <nav className="timeline-periods" aria-label="浏览历史分期">
          {ancientChapters.map(chapter => <button key={chapter.id} type="button" className="timeline-button timeline-ancient-button"
            aria-label={`浏览${chapter.label}画卷`} onClick={() => browseChapter(chapter)}>{chapter.label}</button>)}
          {historyScroll.periods.map((period) => (
            <button
              key={period.label}
              type="button"
              className="timeline-button"
              aria-label={`浏览${period.label}画卷`}
              onClick={() => browsePeriod(period.from_year, period.to_year)}
            >
              {period.label}
            </button>
          ))}
        </nav>
        </div>
        <div className="timeline-workspace">
        <div className="timeline-main">
        <div ref={stageRef} className="timeline-stage">
          <div className="timeline-window-heading">
            <button
              className="timeline-button"
              aria-label="前一段历史"
              disabled={from <= first}
              onClick={() => pan(-span * 0.8)}
            >
              ← 前一段
            </button>
            <span>
              {scrollPositionLabel(from)} — {scrollPositionLabel(to)}
            </span>
            <button
              className="timeline-button"
              aria-label="后一段历史"
              disabled={to >= last}
              onClick={() => pan(span * 0.8)}
            >
              后一段 →
            </button>
          </div>
          <TimelinePeriodBands from={from} to={to} width={chartWidth} previewYear={previewChapter ? null : previewYear} onBrowse={browsePeriod} onBrowseChapter={browseChapter}
            navigationKey={periodNavigation} collapsed={!politiesExpanded}
            onToggle={() => setPolitiesExpanded(value => !value)}/>
          <div className="timeline-art-pan">
            <label htmlFor={compact ? "home-art-position" : "timeline-art-position"}>画面上下</label>
            <input id={compact ? "home-art-position" : "timeline-art-position"} type="range"
              aria-label="上下查看画卷" min="0" max="100" disabled={!scene.cropped} value={Math.round(artPosition * 100)}
              onChange={event => setArtPosition(Number(event.target.value) / 100)}/>
            <button type="button" disabled={!scene.cropped} onClick={() => resize(scene.minimumSpan)}>看完整画幅</button>
          </div>
          <div ref={canvasRef} className="timeline-canvas-scroll" data-view={scene.mode}
            aria-label={scene.mode === "scroll" ? "历史画卷" : "史事数量分布"}>
          <svg
            ref={chartRef}
            data-from={from}
            data-to={to}
            viewBox={`0 90 1000 ${scene.viewBoxHeight}`}
            style={{aspectRatio:`1000 / ${scene.viewBoxHeight}`}}
            className={`timeline-chart ${scene.mode === "detail" ? "timeline-detail-chart" : ""} ${scene.cropped ? "timeline-artwork-draggable" : ""}`}
            role="img"
            aria-label="历史时间图，前841年以前按时代浏览，之后按年浏览；左右拖动，点击选中时代或年份"
            onPointerDown={(e) => startDrag(e)}
            onPointerUp={endDrag}
            onPointerCancel={(e) => {
              suppressClick.current = true;
              endDrag(e);
            }}
            onPointerMove={(e) => {
              if (
                !moveDrag(e) &&
                (e.pointerType === "mouse" || e.pointerType === "pen")
              ) {
                const position = pointPosition(e);
                if (position !== undefined) previewPosition(position);
              }
            }}
            onPointerLeave={() => {
              if (!drag.current) { setHoverYear(null); setHoverChapter(null); }
            }}
            onClick={(e) => {
              if (suppressClick.current) {
                suppressClick.current = false;
                return;
              }
              const position = pointPosition(e);
              if (position !== undefined) {
                const chapter = chapterAtPosition(position);
                if (chapter) chooseChapter(chapter);
                else choose(calendar(Math.max(annualStart, Math.round(position))));
              }
            }}
          >
            {scene.mode === "scroll" && <HistoryScrollBackdrop from={from} to={to} height={scene.height} position={artPosition} pixelsPerSvgUnit={chartWidth/1000}/>}
            {ancientChapters.filter(chapter => chapter.to > from && chapter.from < to).map(chapter => <g key={chapter.id} aria-hidden="true" pointerEvents="none">
              <text x={positionX((Math.max(from,chapter.from)+Math.min(to,chapter.to))/2)} y={scene.bottom+24*1000/chartWidth}
                textAnchor="middle" fill="#6e755e" style={{fontSize:12*1000/chartWidth}}>{chapter.label}</text>
            </g>)}
            {annualStart >= from && annualStart <= to && <g className="timeline-chronology-transition" aria-hidden="true" pointerEvents="none">
              <line x1={positionX(annualStart)} x2={positionX(annualStart)} y1="96" y2={scene.bottom} stroke="#a48856" strokeDasharray="4 5"/>
              <text x={Math.min(890,positionX(annualStart)+8)} y="113" fill="#496044" style={{fontSize:11*1000/chartWidth}}>前841年起按年</text>
            </g>}
            <g className="timeline-period-boundaries" aria-hidden="true" pointerEvents="none">
              {boundaries.map(year => <line key={year} data-boundary-year={year}
                x1={x(year)} x2={x(year)} y1="96" y2={scene.bottom + 2}
                stroke="#546854" strokeOpacity=".55" strokeDasharray="3 5"
                strokeWidth="1" vectorEffect="non-scaling-stroke"/>)}
            </g>
            <defs>
              <linearGradient id="river-colour" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#427d73" stopOpacity=".8" />
                <stop offset="48%" stopColor="#b69255" stopOpacity=".9" />
                <stop offset="100%" stopColor="#214e47" stopOpacity=".85" />
              </linearGradient>
            </defs>
            <g className="timeline-event-dots" aria-hidden="true" pointerEvents="none">
            <line
              x1="40"
              x2="960"
              y1={riverY}
              y2={riverY}
              stroke="#c6d2c9"
              strokeWidth=".6"
            />
            <path d={riverPath} fill="url(#river-colour)" fillOpacity={scene.mode === "detail" ? 1 : .66} />
            <path
              d={
                area<(typeof bins)[number]>()
                  .x((b) => bx(b.at))
                  .y0((b) => riverY + half(b.count) * 0.17)
                  .y1((b) => riverY - half(b.count) * 0.17)
                  .curve(curveMonotoneX)(bins) ?? ""
              }
              fill="#dfc38c"
              fillOpacity=".18"
            />
            <path
              d={shorePath}
              fill="none"
              stroke="#315d54"
              strokeWidth=".7"
              strokeOpacity=".4"
            />
            {[0.3, 0.55, 0.8].map((factor) => (
              <path
                key={factor}
                d={
                  line<(typeof bins)[number]>()
                    .x((b) => bx(b.at))
                    .y((b) => riverY + half(b.count) * factor)
                    .curve(curveMonotoneX)(bins) ?? ""
                }
                fill="none"
                stroke="#fffcf3"
                strokeOpacity=".35"
                strokeWidth=".7"
              />
            ))}
            {bins
              .filter((b) => b.count > 0)
              .flatMap((b) =>
                Array.from({ length: Math.min(13, b.count) }, (_, i) => {
                  const seed = (salt: number) => {
                    const n =
                      Math.sin(b.at * 37.7 + i * 113.1 + salt * 17.3) *
                      43758.5453;
                    return n - Math.floor(n);
                  };
                  return (
                    <circle
                      key={`${b.at}-${i}`}
                      data-event-dot="true" data-year={calendar(b.at)}
                      cx={bx(b.at) + (seed(1) - 0.5) * Math.min(12, 920 / span)}
                      cy={riverY + (seed(2) * 2 - 1) * half(b.count) * 0.83}
                      r={(0.7 + seed(3) * 1.35) * pointScale}
                      fill={i % 3 ? "#ead4a1" : "#ffedc3"}
                      fillOpacity={0.45 + seed(4) * 0.5}
                    />
                  );
                }),
              )}
            </g>
            {hoverYear !== null &&
              ordinal(hoverYear) >= from &&
              ordinal(hoverYear) <= to && (
                <g className="timeline-hover-mark">
                  <line
                    x1={x(hoverYear)}
                    x2={x(hoverYear)}
                    y1="126"
                    y2={scene.bottom-4}
                    stroke="#ae8b51"
                    strokeDasharray="3 5"
                    strokeWidth="1"
                  />
                  <circle
                    cx={x(hoverYear)}
                    cy={riverY}
                    r="5"
                    fill="#d2ab64"
                    stroke="#fffdf6"
                    strokeWidth="2"
                  />
                </g>
              )}
            {!selectedChapter && ordinal(selected) >= from && ordinal(selected) <= to && (
              <g className="timeline-selected-mark">
                <line
                  x1={x(selected)}
                  x2={x(selected)}
                  y1="126"
                  y2={scene.bottom-4}
                  stroke="#315e52"
                  strokeWidth="1.5"
                />
                <circle
                  cx={x(selected)}
                  cy={riverY}
                  r="6"
                  fill="#315e52"
                  stroke="#fffdf6"
                  strokeWidth="2"
                />
              </g>
            )}
            {ticks.map((year) => (
              <g key={year}>
                <line
                  x1={x(year)}
                  x2={x(year)}
                  y1={scene.bottom+2}
                  y2={scene.bottom+8}
                  stroke="#a29b8b"
                />
                <text
                  x={x(year)}
                  y={scene.bottom + 24 * 1000 / chartWidth}
                  textAnchor={x(year) < 80 ? "start" : x(year) > 920 ? "end" : "middle"}
                  fill={boundaries.includes(year) ? "#315e52" : "#7a786f"}
                  style={{fontSize: 12 * 1000 / chartWidth, fontWeight: boundaries.includes(year) ? 500 : 400}}
                >
                  {year < 0 ? `前${-year}` : year}
                </text>
              </g>
            ))}
          </svg>
          </div>
          <p className="sr-only">
            {scene.mode === "detail"
              ? `${binYears === 1 ? "按年展示" : `按${binYears}年汇总`}起始事件记录。河流厚度与光点表示记录分布；点击年份查看史事。`
              : scene.cropped ? "左右拖动浏览年份，上下拖动查看画卷局部，也可用画面上下滑块调整；纵向拖动不改变年份。"
              : "画卷随时间轴同步移动和缩放；史事模式可主动切换。"}
          </p>
        </div>
        {(
          <>
            <div className="timeline-overview" aria-label="全程时间导航">
              <div className="timeline-overview-labels">
                <span>{ancientChapters[0].label}</span>
                <span>全程概览<span className="timeline-overview-help"> · 拖动窗口或两端调整范围</span></span>
                <span>{formatDisplayYear(calendar(last))}</span>
              </div>
              <svg
                viewBox="0 0 1000 70"
                className="timeline-minimap"
                role="img"
                aria-label="全程概览，点击定位，拖动窗口或边缘调整范围"
                onPointerDown={(e) => startDrag(e, true)}
                onPointerMove={moveDrag}
                onPointerUp={endDrag}
                onPointerCancel={endDrag}
              >
                <line
                  x1="20"
                  x2="980"
                  y1="36"
                  y2="36"
                  stroke="#dadccb"
                  strokeWidth="2"
                />
                {ancientChapters.map((chapter,index) => <rect key={chapter.id} data-overview-chapter={chapter.id}
                  x={overviewX(chapter.from)} y="50" width={Math.max(0,overviewX(chapter.to)-overviewX(chapter.from)-1)} height="5" fill={index%2?'#c6bea2':'#b5c5ab'}/>)}
                {historyScroll.periods.map((period, index) => <rect key={period.label}
                  data-overview-period={period.label} x={overviewX(ordinal(period.from_year))} y="50"
                  width={Math.max(0, overviewX(ordinal(period.to_year)) - overviewX(ordinal(period.from_year)) - 1)}
                  height="5" fill={index % 2 ? "#bac7b1" : "#d9dcc9"}/>) }
                {data.years.filter(row=>row.year>=historyScroll.annual_start_year).map((row) => (
                  <line
                    key={row.year}
                    x1={overviewX(ordinal(row.year))}
                    x2={overviewX(ordinal(row.year))}
                    y1={36 - Math.min(22, 3 + Math.sqrt(row.count) * 1.2)}
                    y2="36"
                    stroke="#81998a"
                    strokeWidth="2"
                  />
                ))}
                <rect
                  x={overviewX(from)}
                  y="8"
                  width={Math.max(1, overviewX(to) - overviewX(from))}
                  height="48"
                  fill="#bdb08a"
                  fillOpacity=".15"
                  stroke="#8b956e"
                />
                {[from, to].map((at, i) => (
                  <rect
                    key={i}
                    x={overviewX(at) - 3}
                    y="22"
                    width="6"
                    height="20"
                    rx="2"
                    fill="#637e66"
                  />
                ))}
                <circle
                  cx={overviewX(focus)}
                  cy="36"
                  r="4"
                  fill="#254f44"
                  stroke="#faf8f1"
                  strokeWidth="2"
                />
              </svg>
              <div className="timeline-overview-keys">
                <button
                  className="timeline-button"
                  onClick={() => browse(timeWindow(first, last, first, span))}
                  disabled={from <= first}
                >
                  卷首
                </button>
                <button
                  className="timeline-button"
                  onClick={() => {
                    if (selectedChapter) browseChapter(selectedChapter); else reveal(selected);
                    setHoverYear(null);
                    setHoverChapter(null);
                  }}
                >
                  {selectedChapter ? "回到已选时代" : "回到已选年份"}
                </button>
                <button
                  className="timeline-button"
                  onClick={() => browse(timeWindow(first, last, last, span))}
                  disabled={to >= last}
                >
                  卷尾
                </button>
              </div>
            </div>
            <div className="timeline-slider">
              <span className="timeline-slider-year">已选 {selectedChapter?.label ?? formatDisplayYear(selected)}</span>
              <button
                className="timeline-button"
                disabled={!!selectedChapter || ordinal(selected) <= annualStart}
                aria-label="上一年"
                onClick={() => {
                  const year = calendar(focus - 1);
                  choose(year);
                  reveal(year);
                }}
              >
                ←
              </button>
              <input
                type="range"
                aria-label="选择历史年份"
                min={annualStart}
                max={last}
                value={ordinal(selected)}
                disabled={!!selectedChapter}
                onChange={(e) => {
                  const year = calendar(Number(e.target.value));
                  choose(year, true);
                  reveal(year);
                }}
              />
              <button
                className="timeline-button"
                disabled={!!selectedChapter || ordinal(selected) >= last}
                aria-label="下一年"
                onClick={() => {
                  const year = calendar(focus + 1);
                  choose(year);
                  reveal(year);
                }}
              >
                →
              </button>
            </div>
          </>
        )}
        </div>
        <aside className={`timeline-preview ${previewExpanded ? "is-expanded" : ""} ${previewChapter ? "timeline-era-preview" : ""}`} aria-label={previewChapter ? "时代选读" : "年度史事选读"}>
          {previewChapter ? <>
            <div className="timeline-preview-year"><p className="eyebrow">{selectedChapter?.id === previewChapter.id && !hoverChapter ? "已选时代" : "时代预览 · 点击画面选中"}</p>
              <div className="timeline-preview-title"><h2>{previewChapter.label}</h2><span>按时代选读</span></div>
            </div>
            <div className="timeline-preview-content">
              <p>这一时期的史事选读尚待整理。</p>
              <button type="button" className="timeline-detail-link" onClick={()=>chooseChapter(previewChapter)}>查看这一时期的史事 →</button>
            </div>
          </> : <>
          <div className="timeline-preview-year">
            <p className="eyebrow">
              {hoverYear === null ? "已选年份" : "浏览预览 · 点击年份选中"}
            </p>
            <div className="timeline-preview-title">
              <h2 aria-label={formatDisplayYear(previewYear)}>{previewYear < 0 ? `前${-previewYear}年` : formatDisplayYear(previewYear)}</h2>
              <span>{preview?.count ?? 0} 条起始事件记录</span>
            </div>
          </div>
          <div className="timeline-preview-content">
            {preview?.highlights?.length ? (
              <>
                <p className="timeline-preview-note">
                  {selectedHighlights.length
                    ? "导读精选"
                    : "系统选例 · 年度提要待整理"}
                </p>
                <ul>
                  {preview.highlights.slice(0, 5).map((event) => (
                    <li key={event.id}>
                      <Link to={`/events/${event.id}`}>{event.title} ↗</Link>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p>
                {preview
                  ? "年度提要尚待整理。"
                  : "这个年份暂无起始事件记录，背景画面不代表史料已录入。"}
              </p>
            )}
            {(preview?.highlights?.length ?? 0) > 2 && <button type="button" className="timeline-preview-expand"
              aria-expanded={previewExpanded} onClick={() => setPreviewExpanded(value => !value)}>
              {previewExpanded ? "收起精选" : "展开更多精选"}
            </button>}
            <Link
              className="timeline-detail-link"
              to={`/timeline?year=${previewYear}`}
            >
              查看这一年的史事 →
            </Link>
          </div>
          </>}
        </aside>
        </div>
        <details className="timeline-explanation">
          <summary>画卷与分期说明</summary>
        <p className="timeline-note">
          前841年以前按时代章节展开，章节宽度不代表年数，不为未定年叙事补造年份。前841年起画卷与年份刻度同步，细览显示起始事件记录数量。拖动只浏览，点击才选中时代或年份。无数据表示暂无记录；画卷为AI生成的文化意象，不作疆域或场景复原。
          {bins.length < to - from + 1 &&
            "全景按时间段聚合，放大可查看更多细节。"}
        </p>
        <Link className="timeline-art-link" to="/timeline/scroll">
          查看完整底图与分期比例 →
        </Link>
          <p className="timeline-note">大分期为浏览导航；主要政权按各自起止年份展开，可能并立，不表示疆域。十六国各国、南朝的宋齐梁陈、北朝的北魏、东魏、西魏、北齐、北周分别显示，可点击各自名称浏览，更多政权可上下滚动查看。短时期用外置名称和连接线标示，底部时间条仍按真实年数绘制。画卷放大后保留比例，观察窗显示局部，可上下查看或恢复完整画幅；只有主动切换才进入史事模式。元从1271年定国号、清从1636年改国号算起，画卷分界仍沿用1279年、1644年。</p>
          <nav className="timeline-period-references" aria-label="分期参考">
            {Object.values(polityReferences).map(reference => <a key={reference.url} href={reference.url} target="_blank" rel="noreferrer">{reference.title} ↗</a>)}
          </nav>
        </details>
      </section>
      {!compact && (selectedChapter ? <EraReading chapter={selectedChapter}/> : <YearEvents key={selected} year={selected} />)}
    </>
  );
}
function EraReading({ chapter }: { chapter: AncientChapter }) {
  return <section className="timeline-era-reading min-h-[420px]" aria-label="时代史事">
    <div className="flex flex-wrap justify-between gap-3 mb-4">
      <h2 className="reading-heading mb-0">这一时期发生了什么</h2>
      <span className="text-sm text-stone-500">{chapter.label}</span>
    </div>
    <p className="reading-card">这一时期的史事选读尚待整理。</p>
  </section>;
}
function YearEvents({ year }: { year: number }) {
  const result = useInfiniteResource<PageResult<Event>>(
    `/timeline?year=${year}`,
  );
  const events = result.data?.items ?? [];
  return (
    <section
      aria-label="当年历史事件"
      className="min-h-[420px]"
      aria-busy={result.loading}
    >
      <div className="flex flex-wrap justify-between gap-3 mb-4">
        <h2 className="reading-heading mb-0">这一年发生了什么</h2>
        <span className="text-sm text-stone-500">{`${formatDisplayYear(year)} · 包含持续的跨年事件`}</span>
      </div>
      <LoadState {...result} />
      {!result.loading && !result.error && !events.length && (
        <p className="reading-card">
          {formatDisplayYear(year)}
          暂无已录入事件。可以拖动时间轴，探索相邻年份。
        </p>
      )}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {events.map((event) => (
          <Link
            key={event.id}
            to={`/events/${event.id}`}
            className="reading-card timeline-event"
          >
            <p className="eyebrow">
              {event.dynasty || "历史事件"} ·{" "}
              {formatDisplayRange(event.start_year, event.end_year)}
            </p>
            <h3 className="font-serif text-xl mt-3 mb-2">{event.title}</h3>
            {event.time_original && (
              <p className="text-xs text-amber-800 mb-2">
                {event.time_original}
              </p>
            )}
            <p className="text-sm leading-7 text-stone-600 line-clamp-3">
              {event.description}
            </p>
            <span className="block mt-4 text-sm text-teal-800">
              阅读全文与出处 →
            </span>
          </Link>
        ))}
      </div>
      <InfiniteScroll {...result} count={events.length} label="当年事件" />
    </section>
  );
}
