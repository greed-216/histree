import data from "../data/timeline-polities.json";
import { ordinal } from "./timelineViewport";

export const polityReferences = data.references;
export type TimelinePolity = (typeof data.polities)[number];

/** Clip only to the viewport. Era boundaries never truncate a polity. */
export function visibleInterval(start: number, end: number, from: number, to: number) {
  const left = Math.max(ordinal(start), from);
  const right = Math.min(ordinal(end), to);
  if (right <= left) return null;
  const span = Math.max(1, to - from);
  return { left: 4 + (left - from) / span * 92, width: (right - left) / span * 92 };
}

export function visiblePolityLanes(from: number, to: number) {
  const detailed = to - from <= 180;
  const visible = data.polities.filter(polity =>
    (!polity.level || polity.level === (detailed ? "detail" : "overview"))
    && visibleInterval(polity.from_year, polity.to_year, from, to));
  return [...new Set(visible.map(polity => polity.lane))].sort((a, b) => a - b)
    .map(lane => visible.filter(polity => polity.lane === lane));
}

export function yearInInterval(year: number, start: number, end: number) {
  return year >= start && year < end;
}

/** Pack readable captions independently of the true-duration marks beneath them. */
export function layoutBandLabels(items: { label: string; left: number; width: number }[], viewportWidth: number) {
  const compact = viewportWidth < 720;
  const pitch = compact ? 18 : 22, labelHeight = compact ? 18 : 20;
  const edge = viewportWidth * .04, available = viewportWidth * .92, gap = 4;
  const sorted = items.map((item, index) => ({ index,
    width: Math.min(available, Math.max(28, item.label.length * 14 + 12)),
    center: (item.left + item.width / 2) / 100 * viewportWidth,
  })).sort((a, b) => a.center - b.center);
  const tracks: typeof sorted[] = [];
  let occupied = 0;
  for (const item of sorted) {
    if (!tracks.length || occupied + item.width + gap > available) {
      tracks.push([]); occupied = 0;
    }
    tracks.at(-1)!.push(item);
    occupied += item.width + (occupied ? gap : 0);
  }
  const positions: { left: number; width: number; track: number; center: number; shifted: boolean }[] = [];
  tracks.forEach((track, trackIndex) => {
    const placed = track.map(item => ({ ...item, left: Math.max(edge, Math.min(edge + available - item.width, item.center - item.width / 2)) }));
    for (let i = 1; i < placed.length; i++) placed[i].left = Math.max(placed[i].left, placed[i-1].left + placed[i-1].width + gap);
    if (placed.length) placed.at(-1)!.left = Math.min(placed.at(-1)!.left, edge + available - placed.at(-1)!.width);
    for (let i = placed.length - 2; i >= 0; i--) placed[i].left = Math.min(placed[i].left, placed[i+1].left - gap - placed[i].width);
    for (const item of placed) positions[item.index] = {
      left: item.left, width: item.width, track: trackIndex, center: item.center,
      shifted: Math.abs(item.left + item.width / 2 - item.center) > 2,
    };
  });
  return { positions, pitch, labelHeight, compact, height: Math.max(1, tracks.length) * pitch + (compact ? 5 : 7) };
}
