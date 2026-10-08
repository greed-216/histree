import { useId } from "react";
import { historyScroll, scrollPanelGeometry } from "../lib/historyScroll";
import { ordinal } from "../lib/timelineViewport";
/** Art follows the same year coordinate as data; it contains no asserted event markers. */
export function HistoryScrollBackdrop({
  from,
  to,
}: {
  from: number;
  to: number;
}) {
  const id = useId().replace(/:/g, "");
  return (
    <g aria-hidden="true" pointerEvents="none" data-history-backdrop="true">
      <defs>
        <clipPath id={`scroll-clip-${id}`}>
          <rect x="40" y="96" width="920" height="212" rx="12" />
        </clipPath>
        <linearGradient id={`scroll-wash-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#faf8f1" stopOpacity=".28" />
          <stop offset="70%" stopColor="#faf8f1" stopOpacity=".08" />
          <stop offset="100%" stopColor="#faf8f1" stopOpacity=".45" />
        </linearGradient>
      </defs>
      <g clipPath={`url(#scroll-clip-${id})`}>
        <rect x="40" y="96" width="920" height="212" fill="#f0ecdf" />
        {historyScroll.panels
          .filter(
            (panel) =>
              ordinal(panel.to_year) >= from && ordinal(panel.from_year) <= to,
          )
          .map((panel) => {
            const geometry = scrollPanelGeometry(panel, from, to);
            return (
              <image
                key={panel.id}
                data-panel={panel.id}
                href={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
                {...geometry}
                preserveAspectRatio="none"
                opacity=".88"
              />
            );
          })}
        <rect
          x="40"
          y="96"
          width="920"
          height="212"
          fill={`url(#scroll-wash-${id})`}
        />
      </g>
    </g>
  );
}
