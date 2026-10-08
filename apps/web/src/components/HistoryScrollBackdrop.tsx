import { historyScroll, scrollPanelGeometry } from "../lib/historyScroll";
/** Draw the entire artwork in an independent overview, never magnified by data zoom. */
export function HistoryScrollBackdrop({from, to}: {from:number;to:number}) {
  return <g aria-hidden="true" pointerEvents="none" data-history-backdrop="true">
    {historyScroll.panels.map(panel => <svg key={panel.id} data-panel={panel.id}
      {...scrollPanelGeometry(panel, from, to)}
      viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
      preserveAspectRatio="xMidYMid meet" overflow="hidden">
      <image href={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
        width={panel.width} height={panel.height}/>
    </svg>)}
  </g>;
}
