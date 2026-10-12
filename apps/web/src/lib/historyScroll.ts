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
export function minimumScrollSpan(viewportWidth = 1000, maxCanvasHeight = 320) {
  const width = Math.max(240, viewportWidth);
  const availableHeight = Math.max(1, (maxCanvasHeight - 36) * 1000 / width - 6);
  const panel = scroll.panels[0];
  const annualHeight = 920 * (ordinal(panel.to_year) - ordinal(panel.from_year))
    * panel.crop.height / panel.crop.width;
  const nativePixels = width * .92 / (scroll.pixels_per_elapsed_year * 2);
  return Math.max(10, Math.ceil(annualHeight / availableHeight), Math.ceil(nativePixels));
}
/** Zoom the shared time coordinates without changing the user's chosen view. */
export function nextScrollZoomSpan(span: number, zoomIn: boolean) {
  return Math.max(10, Math.round(span * (zoomIn ? .5 : 2)));
}
export function scrollSceneLayout(from: number, to: number, viewportWidth = 1000,
  maxCanvasHeight = 320, mode: "scroll" | "detail" = "scroll") {
  const width = Math.max(240, viewportWidth);
  const minimumSpan = minimumScrollSpan(width, maxCanvasHeight);
  const naturalHeight = scrollPanelGeometry(scroll.panels[0], from, to).height;
  // Both views occupy the allocated cell; zoom and content never resize it.
  const viewBoxHeight = Math.max(80, maxCanvasHeight) * 1000 / width;
  const height = Math.max(48, viewBoxHeight - 6 - 36 * 1000 / width);
  const bottom = 96 + height;
  const artHeight = Math.min(height, naturalHeight);
  const artTop = 96 + Math.max(0, height - naturalHeight) / 2;
  return { mode, minimumSpan, height, naturalHeight, cropped: mode === "scroll" && naturalHeight > height + 1, bottom,
    riverY: mode === "scroll" ? artTop + Math.max(6, artHeight - 20) : 96 + height * .55,
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
  return timeWindow(first, last, ordinal(selected), compact ? 700 : 600);
}

// Background and graph move/zoom together, with no independent speed or progress calculation.
export const scrollBackgroundGeometry=scrollPanelGeometry;
