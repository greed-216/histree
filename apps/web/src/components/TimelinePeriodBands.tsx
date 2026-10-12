import { Fragment, useState } from "react";
import { historyScroll } from "../lib/historyScroll";
import { formatDisplayRange } from "../lib/content";
import { layoutBandLabels, visibleInterval, visiblePolityLanes, yearInInterval } from "../lib/timelinePeriods";

type BandItem = {
  id: string; label: string; from_year: number; to_year: number;
  note?: string; fullLabel?: string; tone?: number; polity?: string; current?: boolean;
};

function BandLane({ items, from, to, width, kind, onBrowse }: {
  items: BandItem[]; from: number; to: number; width: number; kind: "era" | "polity";
  onBrowse: (start: number, end: number) => void;
}) {
  const visible = items.flatMap(item => {
    const mark = visibleInterval(item.from_year, item.to_year, from, to);
    return mark ? [{ ...item, mark }] : [];
  });
  const layout = layoutBandLabels(visible.map(item => ({ label: item.label, ...item.mark })), width);
  return <div className={`timeline-${kind}-lane ${layout.compact ? "timeline-band-lane-compact" : ""}`} style={{ height: layout.height }}>
    <svg className="timeline-band-connectors" viewBox={`0 0 ${width} ${layout.height}`} aria-hidden="true" preserveAspectRatio="none">
      {visible.map((item, index) => {
        const position = layout.positions[index];
        return position.shifted || position.width > item.mark.width / 100 * width
          ? <line key={item.id} x1={position.left + position.width / 2} y1={position.track * layout.pitch + layout.labelHeight}
            x2={position.center} y2={layout.height - 4}/> : null;
      })}
    </svg>
    {visible.map((item, index) => {
      const position = layout.positions[index], range = formatDisplayRange(item.from_year, item.to_year);
      return <Fragment key={item.id}>
      <span aria-hidden="true" data-duration-polity={item.polity}
        className={`timeline-${kind}-duration timeline-${kind}-tone-${item.tone ?? 0}`}
        aria-current={item.current ? "true" : undefined}
        style={{ left: `${item.mark.left}%`, width: `${item.mark.width}%` }}/>
      <button type="button"
        className={`timeline-${kind}-band timeline-${kind}-tone-${item.tone ?? 0}`}
        style={{ left: position.left, width: position.width, top: position.track * layout.pitch }}
        data-polity={item.polity} data-start={item.from_year} data-end={item.to_year}
        title={`${item.fullLabel || item.label} · ${range}${item.note ? `。${item.note}` : ""}`}
        aria-label={`浏览${item.fullLabel || item.label}，${range}${item.note ? `，${item.note}` : ""}`}
        aria-current={item.current ? "true" : undefined}
        onClick={() => onBrowse(item.from_year, item.to_year)}>
        <span className="timeline-band-name">{item.label}</span>
      </button>
      </Fragment>;
    })}
  </div>;
}

export function TimelinePeriodBands({ from, to, width, previewYear, onBrowse }: {
  from: number; to: number; width: number; previewYear: number;
  onBrowse: (start: number, end: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const lanes = visiblePolityLanes(from, to);
  const limit = 4;
  const showPolities = to - from <= 1800 || expanded;
  const shown = showPolities ? lanes.slice(0, expanded ? lanes.length : limit) : [];
  const hidden = showPolities ? lanes.slice(shown.length).flat().length : lanes.flat().length;

  return <div className="timeline-period-bands" aria-label="大分期与主要并立政权">
    <div className="timeline-band-scroll" tabIndex={0} role="region" aria-label="分期与政权时间带，可上下滚动">
    <div className="timeline-band-lanes" style={{width}}>
    <div className="timeline-era-wrapper" aria-label="大分期"><BandLane from={from} to={to} width={width} kind="era" onBrowse={onBrowse}
      items={historyScroll.periods.map((period, index) => ({ ...period, id: period.label, tone: index % 2, note: "浏览分期",
        current: yearInInterval(previewYear, period.from_year, period.to_year) }))}/></div>
    {shown.map((lane, index) => <div key={lane[0].lane} aria-label={`并立政权第${index + 1}行`}>
      <BandLane from={from} to={to} width={width} kind="polity" onBrowse={onBrowse}
        items={lane.map(polity => ({ ...polity, fullLabel: polity.label, label: polity.short_label || polity.label,
          tone: polity.lane % 3, polity: polity.id }))}/>
    </div>)}
    </div>
    </div>
    <div className="timeline-band-caption">
      <span>{shown.length ? expanded ? "主要政权 · 上下滚动查看" : "主要政权 · 点击名称浏览" : lanes.length ? "大分期 · 放大查看并立政权" : "大分期 · 点击名称浏览"}</span>
      {hidden > 0 && !expanded && <button type="button" onClick={() => setExpanded(true)}>
        {showPolities ? `另${hidden}个政权` : "展开政权带"} <span aria-hidden="true">⌄</span>
      </button>}
      {expanded && <button type="button" onClick={() => setExpanded(false)}>收起 <span aria-hidden="true">⌃</span></button>}
    </div>
  </div>;
}
