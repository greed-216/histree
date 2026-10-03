// Ordinals keep BCE/CE continuous without introducing a historical year zero.
export const ordinal = (year: number) => year < 0 ? year : year - 1;
export const calendar = (value: number) => value < 0 ? value : value + 1;
export type TimeWindow = { from: number; to: number };
export function timeWindow(first: number, last: number, center: number, width: number): TimeWindow {
  const span = Math.min(Math.max(0, last - first), Math.max(1, Math.round(width)));
  const from = Math.max(first, Math.min(last - span, Math.round(center - span / 2)));
  return { from, to: from + span };
}
export function moveWindow(window: TimeWindow, first: number, last: number, shift: number) {
  return timeWindow(first, last, (window.from + window.to) / 2 + shift, window.to - window.from);
}
