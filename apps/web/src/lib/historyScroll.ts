import scroll from "../data/history-scroll.json";
import { ordinal, timeWindow } from "./timelineViewport";
export const historyScroll = scroll;
export function scrollPanelGeometry(
  panel: (typeof scroll.panels)[number],
  from: number,
  to: number,
) {
  const span = Math.max(1, to - from);
  const x = 40 + ((ordinal(panel.from_year) - from) / span) * 920;
  const width =
    ((ordinal(panel.to_year) - ordinal(panel.from_year)) / span) * 920;
  const height = (width * panel.height) / panel.width;
  return { x, width, height, y: 198 - height / 2 };
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
