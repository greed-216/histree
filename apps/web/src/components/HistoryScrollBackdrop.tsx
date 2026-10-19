import { useId } from "react";
import { historyScroll, scrollBackgroundGeometry } from "../lib/historyScroll";
/** Preserve aspect ratio and year coordinates inside a bounded observation window. */
export function HistoryScrollBackdrop({from,to,height,position=.5}: {
  from:number;to:number;height:number;position?:number;
}) {
  const id=useId().replace(/:/g,"");
  const naturalHeight=scrollBackgroundGeometry(historyScroll.panels[0],from,to).height;
  const offset=Math.max(0,naturalHeight-height)*position;
  const centered=Math.max(0,height-naturalHeight)/2;
  return <g aria-hidden="true" pointerEvents="none" data-history-backdrop="true">
    <defs><clipPath id={`background-${id}`}><rect x="40" y="96" width="920" height={height} rx="12"/></clipPath></defs>
    <g clipPath={`url(#background-${id})`}>
      <rect x="40" y="96" width="920" height={height} fill="#f0ecdf"/>
      <g data-artwork-position={position} transform={`translate(0,${centered-offset})`}>
      {historyScroll.panels.map(panel => <svg key={panel.id} data-panel={panel.id}
        {...scrollBackgroundGeometry(panel,from,to)}
        viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
        preserveAspectRatio="xMidYMid meet" overflow="hidden">
        <image href={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
          width={panel.width} height={panel.height}/>
      </svg>)}
      </g>
    </g>
  </g>;
}
