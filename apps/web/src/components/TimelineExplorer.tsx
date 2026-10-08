import { HistoryScrollBackdrop } from "../components/HistoryScrollBackdrop";
import { historyScroll, initialScrollWindow } from "../lib/historyScroll";
import { guideHighlights } from "../lib/historyGuides";
import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
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
export function TimelineExplorer({ compact = false }: { compact?: boolean }) {
  const overview = useResource<TimelineOverview>("/timeline/overview");
  return (
    <div className={compact ? "timeline-page timeline-home" : "timeline-page"}>
      <LoadState {...overview} />
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
  const first = ordinal(Math.min(historyScroll.from_year, data.from!)),
    last = ordinal(Math.max(historyScroll.to_year, data.to!));
  const preferred = compact
    ? (data.years.find((row) => row.year === 907)?.year ??
      data.years.at(-1)!.year)
    : data.years.at(-1)!.year;
  const selected = calendar(
    Math.max(first, Math.min(last, ordinal(requested ?? preferred))),
  );
  const [window, setWindow] = useState<TimeWindow>(() =>
    initialScrollWindow(selected, data.from!, data.to!, compact),
  );
  useEffect(() => {
    setWindow(previous => ordinal(selected) >= previous.from && ordinal(selected) <= previous.to
      ? previous : timeWindow(first, last, ordinal(selected), previous.to - previous.from));
    setHoverYear(null);
  }, [selected, first, last]);
  const from = window.from,
    to = window.to;
  const span = Math.max(1, to - from);
  const focus = ordinal(selected);
  const [hoverYear, setHoverYear] = useState<number | null>(null);
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
  const drag = useRef<{
    x: number;
    window: TimeWindow;
    moved: boolean;
    mode: "chart" | "move" | "left" | "right";
  } | null>(null);
  const suppressClick = useRef(false);
  const wheelRemainder = useRef(0);
  const x = (year: number) =>
    to === from ? 500 : 40 + ((ordinal(year) - from) / span) * 920;
  const overviewX = (at: number) =>
    20 + ((at - first) / Math.max(1, last - first)) * 960;
  function browse(next: TimeWindow) {
    setWindow(next);
    setHoverYear(calendar(Math.round((next.from + next.to) / 2)));
  }
  function pan(shift: number) {
    browse(moveWindow(window, first, last, shift));
  }
  function resize(width: number) {
    browse(timeWindow(first, last, (from + to) / 2, width));
  }
  function reveal(year: number) {
    if (ordinal(year) < from || ordinal(year) > to)
      setWindow(timeWindow(first, last, ordinal(year), span));
  }
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    // Only horizontal trackpad motion pans; vertical wheel motion keeps page reading natural.
    const wheel = (event: WheelEvent) => {
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
    };
    chart.addEventListener("wheel", wheel, { passive: false });
    return () => chart.removeEventListener("wheel", wheel);
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
    const isChart = start.mode === "chart";
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
    const values = Array.from(
      { length: Math.ceil((to - from + 1) / size) },
      (_, i) => ({ at: from + i * size, count: 0 }),
    );
    for (const row of data.years) {
      const index = Math.floor((ordinal(row.year) - from) / size);
      if (ordinal(row.year) >= from && ordinal(row.year) <= to)
        values[index].count += row.count;
    }
    return values;
  }, [data.years, from, to]);
  const peak = Math.max(1, ...bins.map((b) => b.count));
  const half = (count: number) =>
    count ? 2 + 16 * Math.sqrt(count / peak) : 0;
  const bx = (at: number) =>
    to === from ? 500 : 40 + ((at - from) / span) * 920;
  const riverPath =
    area<(typeof bins)[number]>()
      .x((b) => bx(b.at))
      .y0((b) => 288 + half(b.count))
      .y1((b) => 288 - half(b.count))
      .curve(curveMonotoneX)(bins) ?? "";
  const shorePath =
    line<(typeof bins)[number]>()
      .x((b) => bx(b.at))
      .y((b) => 288 - half(b.count))
      .curve(curveMonotoneX)(bins) ?? "";
  const ticks = [
    ...new Set(
      Array.from({ length: 7 }, (_, i) =>
        calendar(Math.round(from + (span * i) / 6)),
      ),
    ),
  ].filter((y) => ordinal(y) <= to);
  function choose(year: number, replace = false) {
    year = calendar(Math.max(first, Math.min(last, ordinal(year))));
    setHoverYear(null);
    if (year === selected) return;
    const next = new URLSearchParams(params);
    next.set("year", String(year));
    setParams(next, { replace });
  }
  function pointYear(
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
    return calendar(Math.round(Math.min(to, from + ratio * span)));
  }
  function jump(e: React.FormEvent) {
    e.preventDefault();
    try {
      const year = timelineYear(draft);
      if (ordinal(year) < first || ordinal(year) > last) throw new Error();
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
      >
        <div className="timeline-topline">
          <div>
            <p className="eyebrow">历史画卷 · 前770年—1912年</p>
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
              disabled={to - from >= last - first}
              onClick={() => browse({ from: first, to: last })}
            >
              画卷全景
            </button>
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
            <button
              className="timeline-button"
              disabled={span >= last - first}
              onClick={() => resize(span * 2)}
            >
              缩小
            </button>
            <button
              className="timeline-button"
              disabled={span <= Math.min(10, last - first)}
              onClick={() => resize(Math.max(10, span / 2))}
            >
              放大
            </button>
            <span>{to - from + 1} 年视窗</span>
          </div>
          {compact ? (
            <details className="timeline-jump">
              <summary>跳至年份</summary>
              {yearJump}
            </details>
          ) : (
            yearJump
          )}
        </div>
        {invalid && (
          <p role="alert" className="text-sm text-rose-700">
            请输入画卷范围内的整数年份；公元前用负数，没有公元 0 年。
          </p>
        )}
        <nav className="timeline-periods" aria-label="浏览历史分期">
          {historyScroll.periods.map((period) => (
            <button
              key={period.label}
              type="button"
              className="timeline-button"
              aria-label={`浏览${period.label}画卷`}
              onClick={() =>
                browse(
                  timeWindow(
                    first,
                    last,
                    (ordinal(period.from_year) + ordinal(period.to_year)) / 2,
                    ordinal(period.to_year) - ordinal(period.from_year),
                  ),
                )
              }
            >
              {period.label}
            </button>
          ))}
        </nav>
        <div className="timeline-stage">
          <p className="timeline-art-caption">完整历史画卷 · 下方金色范围对应当前视窗</p>
          <svg className="timeline-art-overview" viewBox="0 0 1000 200"
            role="img" aria-label="完整历史画卷，点击选年，拖动浏览范围"
            onPointerDown={e => startDrag(e, true)} onPointerMove={moveDrag}
            onPointerUp={endDrag} onPointerCancel={e => {suppressClick.current=true;endDrag(e);}}
            onClick={e => {
              if(suppressClick.current){suppressClick.current=false;return;}
              const matrix=e.currentTarget.getScreenCTM();if(!matrix)return;
              const point=new DOMPoint(e.clientX,e.clientY).matrixTransform(matrix.inverse());
              choose(calendar(Math.round(first+Math.max(0,Math.min(1,(point.x-20)/960))*(last-first))));
            }}>
            <g transform="translate(0 4)"><HistoryScrollBackdrop from={first} to={last}/></g>
            <line x1="20" x2="980" y1="182" y2="182" stroke="#d5d8c8"/>
            <rect x={overviewX(from)} y="178" width={Math.max(2, overviewX(to)-overviewX(from))}
              height="8" rx="4" fill="#ab854c"/>
            <circle cx={overviewX(focus)} cy="182" r="4" fill="#315e52"/>
          </svg>
          <p className="timeline-art-caption">史事时间轴 · 可独立放大与拖动</p>
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
              {formatDisplayYear(calendar(from))} —{" "}
              {formatDisplayYear(calendar(to))}
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
          <svg
            ref={chartRef}
            data-from={from}
            data-to={to}
            viewBox="0 246 1000 110"
            className="timeline-chart"
            role="img"
            aria-label="历史时间图，拖动浏览，移动光标预览，点击固定年份"
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
                const year = pointYear(e);
                if (year !== undefined) setHoverYear(year);
              }
            }}
            onPointerLeave={() => {
              if (!drag.current) setHoverYear(null);
            }}
            onClick={(e) => {
              if (suppressClick.current) {
                suppressClick.current = false;
                return;
              }
              const year = pointYear(e);
              if (year !== undefined) choose(year);
            }}
          >
            <defs>
              <linearGradient id="river-colour" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#427d73" stopOpacity=".8" />
                <stop offset="48%" stopColor="#b69255" stopOpacity=".9" />
                <stop offset="100%" stopColor="#214e47" stopOpacity=".85" />
              </linearGradient>
            </defs>
            <line
              x1="40"
              x2="960"
              y1="288"
              y2="288"
              stroke="#c6d2c9"
              strokeWidth=".6"
            />
            <path d={riverPath} fill="url(#river-colour)" fillOpacity=".66" />
            <path
              d={
                area<(typeof bins)[number]>()
                  .x((b) => bx(b.at))
                  .y0((b) => 288 + half(b.count) * 0.17)
                  .y1((b) => 288 - half(b.count) * 0.17)
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
                    .y((b) => 288 + half(b.count) * factor)
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
                      cx={bx(b.at) + (seed(1) - 0.5) * Math.min(12, 920 / span)}
                      cy={288 + (seed(2) * 2 - 1) * half(b.count) * 0.83}
                      r={0.7 + seed(3) * 1.35}
                      fill={i % 3 ? "#ead4a1" : "#ffedc3"}
                      fillOpacity={0.45 + seed(4) * 0.5}
                    />
                  );
                }),
              )}
            {hoverYear !== null &&
              ordinal(hoverYear) >= from &&
              ordinal(hoverYear) <= to && (
                <g className="timeline-hover-mark">
                  <line
                    x1={x(hoverYear)}
                    x2={x(hoverYear)}
                    y1="260"
                    y2="304"
                    stroke="#ae8b51"
                    strokeDasharray="3 5"
                    strokeWidth="1"
                  />
                  <circle
                    cx={x(hoverYear)}
                    cy="288"
                    r="5"
                    fill="#d2ab64"
                    stroke="#fffdf6"
                    strokeWidth="2"
                  />
                </g>
              )}
            {ordinal(selected) >= from && ordinal(selected) <= to && (
              <g>
                <line
                  x1={x(selected)}
                  x2={x(selected)}
                  y1="260"
                  y2="304"
                  stroke="#315e52"
                  strokeWidth="1.5"
                />
                <circle
                  cx={x(selected)}
                  cy="288"
                  r="6"
                  fill="#315e52"
                  stroke="#fffdf6"
                  strokeWidth="2"
                />
                <rect
                  x={Math.max(40, Math.min(880, x(selected) - 40))}
                  y="248"
                  width="80"
                  height="24"
                  rx="12"
                  fill="#315e52"
                />
                <text
                  x={Math.max(80, Math.min(920, x(selected)))}
                  y="264"
                  textAnchor="middle"
                  fill="#fffdf6"
                  fontSize="12"
                >
                  {selected < 0 ? `前${-selected}` : selected} · 已选
                </text>
              </g>
            )}
            <line
              x1="500"
              x2="500"
              y1="132"
              y2="304"
              stroke="#847d65"
              strokeOpacity=".3"
              strokeDasharray="1 6"
            />
            {ticks.map((year) => (
              <g key={year}>
                <line
                  x1={x(year)}
                  x2={x(year)}
                  y1="310"
                  y2="316"
                  stroke="#a29b8b"
                />
                <text
                  x={x(year)}
                  y="337"
                  textAnchor="middle"
                  fill="#7a786f"
                  fontSize="13"
                >
                  {year < 0 ? `前${-year}` : year}
                </text>
              </g>
            ))}
          </svg>
        </div>
        <aside className="timeline-preview" aria-label="年度史事选读">
          <div className="timeline-preview-year">
            <p className="eyebrow">
              {hoverYear === null ? "已选年份" : "浏览预览 · 点击年份选中"}
            </p>
            <div className="timeline-preview-title">
              <h2>{formatDisplayYear(previewYear)}</h2>
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
                  {preview.highlights.map((event) => (
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
            <Link
              className="timeline-detail-link"
              to={`/timeline?year=${previewYear}`}
            >
              查看这一年的史事 →
            </Link>
          </div>
        </aside>
        {!compact && (
          <>
            <div className="timeline-overview" aria-label="全程时间导航">
              <div className="timeline-overview-labels">
                <span>{formatDisplayYear(calendar(first))}</span>
                <span>全程概览 · 拖动窗口或两端调整范围</span>
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
                {data.years.map((row) => (
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
                    reveal(selected);
                    setHoverYear(null);
                  }}
                >
                  回到已选年份
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
            <div className="timeline-selected">
              <span className="eyebrow">当前停驻</span>
              <h2>{formatDisplayYear(selected)}</h2>
            </div>
            <div className="timeline-slider">
              <button
                className="timeline-button"
                disabled={focus <= first}
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
                min={first}
                max={last}
                value={focus}
                onChange={(e) => {
                  const year = calendar(Number(e.target.value));
                  choose(year, true);
                  reveal(year);
                }}
              />
              <button
                className="timeline-button"
                disabled={focus >= last}
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
        <p className="timeline-note">
          完整画卷保留原图比例；缩放只作用于下方史事时间轴。拖动只浏览，点击年份才更新事件清单。底部曲线与光点表示该时间段开始的已录入事件数量。无数据表示暂无记录；画卷为AI生成的文化意象，不作疆域或场景复原。
          {bins.length < to - from + 1 &&
            "全景按时间段聚合，放大可查看更多细节。"}
        </p>
        <Link className="timeline-art-link" to="/timeline/scroll">
          查看完整底图与分期比例 →
        </Link>
      </section>
      {!compact && <YearEvents key={selected} year={selected} />}
    </>
  );
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
