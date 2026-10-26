import { useId } from "react";
import { scrollPanels, scrollBackgroundGeometry } from "../lib/historyScroll";
import { ScrollPanelTiles } from "./ScrollPanelTiles";
/** Preserve aspect ratio and year coordinates inside a bounded observation window. */
export function HistoryScrollBackdrop({from,to,height,position=.5,rounded=true,pixelsPerSvgUnit=1,loadFrom=from,loadTo=to}: {
  from:number;to:number;height:number;position?:number;rounded?:boolean;pixelsPerSvgUnit?:number;loadFrom?:number;loadTo?:number;
}) {
  const id=useId().replace(/:/g,"");
  const naturalHeight=scrollBackgroundGeometry(scrollPanels[0],from,to).height;
  const offset=Math.max(0,naturalHeight-height)*position;
  const centered=Math.max(0,height-naturalHeight)/2;
  return <g pointerEvents="none" data-history-backdrop="true">
    <defs><clipPath id={`background-${id}`}><rect x="40" y="96" width="920" height={height} rx={rounded?12:0}/></clipPath></defs>
    <g clipPath={`url(#background-${id})`}>
      <rect x="40" y="96" width="920" height={height} fill="#f0ecdf"/>
      <g data-artwork-position={position} transform={`translate(0,${centered-offset})`}>
      {scrollPanels.map((panel, index) => <svg key={panel.id} data-panel={panel.id}
        {...scrollBackgroundGeometry(panel,from,to)}
        viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
        preserveAspectRatio="xMidYMid meet" overflow="hidden">
        {panel.fade_in_pixels > 0 && <defs>
          <linearGradient id={`join-${id}-${index}`} x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="white" stopOpacity="0"/>
            <stop offset={`${Math.min(1, panel.fade_in_pixels / (panel.crop.width * 720 / panel.crop.height)) * 100}%`} stopColor="white"/>
            <stop offset="100%" stopColor="white"/>
          </linearGradient>
          <mask id={`mask-${id}-${index}`} maskUnits="userSpaceOnUse" x={panel.crop.x} y={panel.crop.y} width={panel.crop.width} height={panel.crop.height}>
            <rect x={panel.crop.x} y={panel.crop.y} width={panel.crop.width} height={panel.crop.height} fill={`url(#join-${id}-${index})`}/>
          </mask>
        </defs>}
        <ScrollPanelTiles panel={panel} next={scrollPanels[index+1]} from={loadFrom} to={loadTo}
          scale={naturalHeight/panel.crop.height*pixelsPerSvgUnit} mask={panel.fade_in_pixels>0?`url(#mask-${id}-${index})`:undefined}/>
      </svg>)}
      </g>
    </g>
  </g>;
}
