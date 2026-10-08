import scroll from "../data/history-scroll.json";
import { ordinal, timeWindow } from "./timelineViewport";
export const historyScroll = scroll;
/** All data and artwork share this exact year-to-screen transform. */
export function scrollYearX(year:number,from:number,to:number) {
  return 40 + (ordinal(year)-from)/Math.max(1,to-from)*920;
}
export function scrollPanelGeometry(panel:(typeof scroll.panels)[number],from:number,to:number) {
  const x=scrollYearX(panel.from_year,from,to);
  const width=scrollYearX(panel.to_year,from,to)-x;
  const height=width*panel.crop.height/panel.crop.width;
  return {x,width,height,y:96};
}
export function scrollSceneLayout(from:number,to:number) {
  const height=scrollPanelGeometry(scroll.panels[0],from,to).height;
  const bottom=96+height;
  return {height,bottom,riverY:Math.max(136,bottom-20),viewBoxHeight:Math.max(128,height+70)};
}
export function scrollPeriodShare(from: number, to: number) {
  return (
    (ordinal(to) - ordinal(from)) /
    (ordinal(scroll.to_year) - ordinal(scroll.from_year))
  );
}

export function initialScrollWindow(selected: number, dataFrom: number, dataTo: number, compact: boolean) {
  const first = ordinal(Math.min(historyScroll.from_year, dataFrom));
  const last = ordinal(Math.max(historyScroll.to_year, dataTo));
  if (compact) return timeWindow(first, last, ordinal(selected), 600);
  if (selected < dataFrom || selected > dataTo) return timeWindow(first, last, ordinal(selected), 100);
  return timeWindow(ordinal(dataFrom), ordinal(dataTo), ordinal(selected), Math.min(100, ordinal(dataTo) - ordinal(dataFrom)));
}

// Background and graph move/zoom together, with no independent speed or progress calculation.
export const scrollBackgroundGeometry=scrollPanelGeometry;
