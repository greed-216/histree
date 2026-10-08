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
/** Minimum year span at which the full artwork fits the available canvas. */
export function minimumScrollSpan(viewportWidth = 1000) {
  const width = Math.max(240, viewportWidth);
  const maxCanvasHeight = 1200;
  const availableHeight = Math.max(1, maxCanvasHeight * 1000 / width - 70);
  const panel = scroll.panels[0];
  const annualHeight = 920 * (ordinal(panel.to_year) - ordinal(panel.from_year))
    * panel.crop.height / panel.crop.width;
  const nativePixels = width * .92 / (scroll.pixels_per_elapsed_year * 2);
  return Math.max(10, Math.ceil(annualHeight / availableHeight), Math.ceil(nativePixels));
}
/** Stop once at the artwork limit before entering the closer event view. */
export function nextScrollZoomSpan(span: number, limit: number, zoomIn: boolean) {
  const next = Math.max(10, span * (zoomIn ? .5 : 2));
  if ((zoomIn && span > limit && next < limit) || (!zoomIn && span < limit && next >= limit)) return limit;
  return next;
}
export function scrollSceneLayout(from: number, to: number, viewportWidth = 1000) {
  const width = Math.max(240, viewportWidth);
  const minimumSpan = minimumScrollSpan(width);
  const mode = to - from >= minimumSpan ? "scroll" : "detail";
  const naturalHeight = scrollPanelGeometry(scroll.panels[0], from, to).height;
  const viewBoxHeight = mode === "scroll" ? Math.max(128, naturalHeight + 70)
    : (width < 640 ? 270 : 310) * 1000 / width;
  const height = mode === "scroll" ? naturalHeight : viewBoxHeight - 70;
  const bottom = mode === "scroll" ? 96 + height : 90 + viewBoxHeight * (214 / 270);
  return { mode, minimumSpan, height, bottom,
    riverY: mode === "scroll" ? Math.max(136, bottom - 20) : 90 + viewBoxHeight * (118 / 270),
    viewBoxHeight };
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
