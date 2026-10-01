export interface TimelineOverview {
  years: Array<{ year: number; count: number }>;
  total: number;
  undated: number;
  from: number | null;
  to: number | null;
}
export function timelineYear(value: unknown): number {
  if (value === null || value === undefined || value === '') throw new Error('请选择年份');
  const year = Number(value);
  if (!Number.isInteger(year) || year === 0 || Math.abs(year) > 10000) throw new Error('无效的年份');
  return year;
}
