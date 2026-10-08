import { useId } from "react";
import { historyScroll, scrollBackgroundGeometry, scrollSceneLayout } from "../lib/historyScroll";
/** Exact shared year coordinates; only the sides are clipped, never artwork height. */
export function HistoryScrollBackdrop({from,to}: {from:number;to:number}) {
  const id=useId().replace(/:/g,"");
  const scene=scrollSceneLayout(from,to);
  return <g aria-hidden="true" pointerEvents="none" data-history-backdrop="true">
    <defs><clipPath id={`background-${id}`}><rect x="40" y="96" width="920" height={scene.height} rx="12"/></clipPath></defs>
    <g clipPath={`url(#background-${id})`}>
      <rect x="40" y="96" width="920" height={scene.height} fill="#f0ecdf"/>
      {historyScroll.panels.map(panel => <svg key={panel.id} data-panel={panel.id}
        {...scrollBackgroundGeometry(panel,from,to)}
        viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
        preserveAspectRatio="xMidYMid meet" overflow="hidden">
        <image href={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
          width={panel.width} height={panel.height}/>
      </svg>)}
    </g>
  </g>;
}
