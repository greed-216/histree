import { useEffect, useId, useRef, useState } from "react";
import { historyScroll, ancientChapters, type AncientChapter } from "../lib/historyScroll";
import { formatDisplayRange } from "../lib/content";
import { layoutBandLabels, polityTones, visibleInterval, visiblePolityLanes, yearInInterval } from "../lib/timelinePeriods";
import { ordinal } from "../lib/timelineViewport";

type BandItem = {
  id: string; label: string; from_year?: number; to_year?: number;
  chapter?: AncientChapter;
  note?: string; fullLabel?: string; tone?: number; polity?: string; current?: boolean;
  phases?: { id: string; label: string; from_year: number; to_year: number }[];
  transition?: { year: number; label: string };
};

function BandLane({ items, from, to, width, kind, onBrowse, onBrowseChapter }: {
  items: BandItem[]; from: number; to: number; width: number; kind: "era" | "polity";
  onBrowse: (start: number, end: number) => void;
  onBrowseChapter?: (chapter: AncientChapter) => void;
}) {
  function markFor(item: Pick<BandItem, "from_year" | "to_year" | "chapter">) {
    if (item.chapter) {
      const left = Math.max(from, item.chapter.from), right = Math.min(to, item.chapter.to);
      return right > left ? { left: 4 + (left - from) / (to - from) * 92, width: (right - left) / (to - from) * 92 } : null;
    }
    return item.from_year !== undefined && item.to_year !== undefined
      ? visibleInterval(item.from_year, item.to_year, from, to) : null;
  }
  const visible = items.flatMap(item => {
    const mark = markFor(item);
    return mark ? [{ ...item, mark }] : [];
  });
  const captions = visible.flatMap(item => (item.phases || [item]).flatMap((phase, index) => {
    const mark = markFor(phase);
    return mark ? [{ ...item, ...phase, owner: item.id, polity: item.phases ? phase.id : item.polity,
      tone: kind === "polity" ? ((item.tone ?? 0) + index) % 5 : item.tone, mark }] : [];
  }));
  const layout = layoutBandLabels(captions.map(item => ({ label: item.label, ...item.mark })), width);
  const height = layout.height - (kind === "era" ? 2 : 0);
  return <div className={`timeline-${kind}-lane ${layout.compact ? "timeline-band-lane-compact" : ""}`} style={{ height }}>
    {visible.map(item => <div key={item.id} className="timeline-band-item">
      {item.phases && <span aria-hidden="true" data-duration-polity={item.polity}
        className={`timeline-${kind}-duration timeline-${kind}-tone-${item.tone ?? 0} timeline-polity-continuity`}
        style={{ left: `${item.mark.left}%`, width: `${item.mark.width}%` }}/>}
      {captions.map((caption, index) => {
        if (caption.owner !== item.id) return null;
        const position = layout.positions[index], range = caption.chapter ? "按时代浏览，宽度不代表年数" : formatDisplayRange(caption.from_year, caption.to_year);
        return <div key={caption.id} className={`timeline-band-segment timeline-${kind}-tone-${caption.tone ?? 0}`}>
      <svg className="timeline-band-connectors" viewBox={`0 0 ${width} ${height}`} aria-hidden="true" preserveAspectRatio="none">
        {(position.shifted || position.width > caption.mark.width / 100 * width) &&
          <line x1={position.left + position.width / 2} y1={position.track * layout.pitch + layout.labelHeight}
            x2={position.center} y2={height - 4}/>}
      </svg>
      <span aria-hidden="true" data-duration-polity={item.phases ? undefined : item.polity}
        data-duration-phase={item.phases ? caption.id : undefined}
        className={`timeline-${kind}-duration${item.phases ? " timeline-polity-phase" : ""}`}
        aria-current={item.current ? "true" : undefined}
        style={{ left: `${caption.mark.left}%`, width: `${caption.mark.width}%` }}/>
      <button type="button"
        className={`timeline-${kind}-band`}
        style={{ left: position.left, width: position.width, top: position.track * layout.pitch }}
        data-polity={caption.polity} data-chapter={caption.chapter?.id} data-start={caption.from_year} data-end={caption.to_year}
        title={`${item.phases ? caption.label : item.fullLabel || item.label} · ${range}${item.note ? `。${item.note}` : ""}`}
        aria-label={`浏览${item.phases ? caption.label : item.fullLabel || item.label}，${range}${item.note ? `，${item.note}` : ""}`}
        aria-current={item.current ? "true" : undefined}
        onClick={() => {
          if (caption.chapter) onBrowseChapter?.(caption.chapter);
          else if (caption.from_year !== undefined && caption.to_year !== undefined) onBrowse(caption.from_year, caption.to_year);
        }}>
        <span className="timeline-band-name">{caption.label}</span>
      </button>
      </div>;
      })}
      {item.transition && ordinal(item.transition.year) >= from && ordinal(item.transition.year) <= to && (() => {
        const x = (4 + (ordinal(item.transition.year) - from) / (to - from) * 92) / 100 * width;
        return <div className="timeline-polity-transition" data-transition-year={item.transition.year}>
          <span className="timeline-transition-tick" style={{ left: x, top: height - 10 }}/>
        </div>;
      })()}
    </div>)}
  </div>;
}

export function TimelinePeriodBands({ from, to, width, previewYear, onBrowse, onBrowseChapter, navigationKey = 0, collapsed, onToggle }: {
  from: number; to: number; width: number; previewYear: number | null;
  onBrowse: (start: number, end: number) => void;
  onBrowseChapter: (chapter: AncientChapter) => void;
  navigationKey?: number;
  collapsed: boolean;
  onToggle: () => void;
}) {
  const [remaining, setRemaining] = useState(0);
  const polityId = useId();
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [navigationKey]);
  useEffect(() => {
    const scroll = scrollRef.current;
    if (!scroll || collapsed) return;
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const bottom = scroll.getBoundingClientRect().bottom;
        const atEnd = scroll.scrollHeight - scroll.scrollTop - scroll.clientHeight <= 1;
        setRemaining(atEnd ? 0 : [...scroll.querySelectorAll('[data-polity]')]
          .filter(item => item.getBoundingClientRect().bottom > bottom + 1).length);
      });
    };
    const observer = new ResizeObserver(update);
    observer.observe(scroll);
    if (scroll.firstElementChild) observer.observe(scroll.firstElementChild);
    scroll.addEventListener('scroll', update, { passive: true });
    update();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      scroll.removeEventListener('scroll', update);
    };
  }, [from, to, width, navigationKey, collapsed]);
  const lanes = visiblePolityLanes(from, to);
  const transition = lanes.flat().find(item => item.transition && ordinal(item.transition.year) >= from && ordinal(item.transition.year) <= to)?.transition;

  return <div className={`timeline-period-bands${collapsed ? " is-collapsed" : ""}`} aria-label="大分期与主要并立政权">
    <div ref={scrollRef} className="timeline-band-scroll" tabIndex={0} role="region" aria-label="分期与政权时间带，可上下滚动">
    <div className="timeline-band-lanes" style={{width}}>
    <div className="timeline-era-wrapper" aria-label="朝代分期概览"><BandLane from={from} to={to} width={width} kind="era" onBrowse={onBrowse} onBrowseChapter={onBrowseChapter}
      items={[
        ...ancientChapters.map((chapter,index) => ({ id: chapter.id, label: chapter.label, chapter, tone: index % 2 })),
        ...historyScroll.periods.map((period, index) => ({ ...period, id: period.label, tone: index % 2, note: "浏览分期",
          current: previewYear !== null && yearInInterval(previewYear, period.from_year, period.to_year) })),
      ]}/></div>
    <div id={polityId} hidden={collapsed}>
    {!collapsed && lanes.map((lane, index) => <div key={lane[0].lane} aria-label={`并立政权第${index + 1}行`}>
      <BandLane from={from} to={to} width={width} kind="polity" onBrowse={onBrowse}
        items={lane.map(polity => ({ ...polity, fullLabel: polity.label, label: polity.short_label || polity.label,
          tone: polityTones[polity.id], polity: polity.id }))}/>
    </div>)}
    </div>
    </div>
    </div>
    <div className="timeline-band-caption">
      <span>{collapsed ? "朝代分期" : transition ? <span className="timeline-transition-legend">◆ 前221 · {transition.label}</span>
        : "左右滑动浏览"}</span>
      <div className="timeline-band-actions">
      {!collapsed && remaining > 0 && <span className="timeline-band-remaining" data-remaining-polities={remaining}
        title="向下滚动查看其余政权">另 {remaining} 个政权 <span aria-hidden="true">↓</span></span>}
      <button type="button" aria-expanded={!collapsed} aria-controls={polityId}
        aria-label={collapsed ? "展开政权时间线" : "收起政权时间线"} onClick={onToggle}>
        {collapsed ? "展开国家" : "收起国家"} <span aria-hidden="true">{collapsed ? "⌄" : "⌃"}</span>
      </button>
      </div>
    </div>
  </div>;
}
