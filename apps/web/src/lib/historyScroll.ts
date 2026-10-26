import scroll from "../data/history-scroll.json";
import { ordinal, calendar, timeWindow } from "./timelineViewport";
export const historyScroll = scroll;
export const annualStart = ordinal(scroll.annual_start_year);
const pixelsPerPosition = scroll.pixels_per_elapsed_year;
export const ancientChapters = scroll.ancient_chapters.map((chapter, index, all) => {
  const remaining = all.slice(index).reduce((sum, item) => sum + item.width_pixels, 0);
  const from = annualStart - remaining / pixelsPerPosition;
  return { ...chapter, from, to: from + chapter.width_pixels / pixelsPerPosition };
});
export type AncientChapter = (typeof ancientChapters)[number];
export const scrollStart = ancientChapters[0].from;
export const chapterAtPosition = (position: number) => ancientChapters.find(chapter => position >= chapter.from && position < chapter.to);
export const chapterById = (id: string | null) => ancientChapters.find(chapter => chapter.id === id);
export function scrollPositionLabel(position: number) {
  const chapter = chapterAtPosition(position);
  if (chapter) return chapter.label;
  const year = calendar(Math.round(position));
  return year < 0 ? `前${-year}年` : `${year}年`;
}
export const scrollPanels = [
  { ...scroll.ancient_panel, from_position: scrollStart, to_position: annualStart, fade_in_pixels: 0 },
  ...scroll.panels.map(panel => ({ ...panel, from_position: ordinal(panel.from_year), to_position: ordinal(panel.to_year) })),
];
export function scrollPositionX(position: number, from: number, to: number) {
  return 40 + (position - from) / Math.max(1, to - from) * 920;
}
/** All data and artwork share this exact year-to-screen transform. */
export function scrollYearX(year:number,from:number,to:number) {
  return scrollPositionX(ordinal(year), from, to);
}
export function scrollPanelGeometry(panel:(typeof scrollPanels)[number],from:number,to:number) {
  const x=scrollPositionX(panel.from_position,from,to);
  const height=920 / Math.max(1,to-from) / pixelsPerPosition * scroll.logical_canvas.height;
  const width=height*panel.crop.width/panel.crop.height;
  return {x,width,height,y:96};
}
/** Minimum year span at which the full artwork fits the available canvas. */
export function minimumScrollSpan(viewportWidth = 1000, maxCanvasHeight = 320) {
  const width = Math.max(240, viewportWidth);
  const availableHeight = Math.max(1, (maxCanvasHeight - 36) * 1000 / width - 6);
  const annualHeight = 920 * scroll.logical_canvas.height / pixelsPerPosition;
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
  const naturalHeight = scrollPanelGeometry(scrollPanels[0], from, to).height;
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
    (ordinal(scroll.to_year) - scrollStart)
  );
}

export function initialScrollWindow(selected: number, _dataFrom: number, dataTo: number, compact: boolean) {
  const first = scrollStart;
  const last = ordinal(Math.max(historyScroll.to_year, dataTo));
  return timeWindow(first, last, ordinal(selected), compact ? 700 : 600);
}

// Background and graph move/zoom together, with no independent speed or progress calculation.
export const scrollBackgroundGeometry=scrollPanelGeometry;
