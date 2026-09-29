/** Image-space basemaps. Coordinates are SVG canvas units, never longitude/latitude. */
export type AtlasPoint = [number, number];
export interface AtlasRegion {
  id: string;
  name: string;
  color: string;
  nodes: string[];
  label: AtlasPoint;
  note: string;
}
export interface AtlasSnapshot {
  id: string;
  year: number;
  title: string;
  status: 'draft';
  source: string;
  reference: 'shituguan-907' | null;
  nodes: Record<string, AtlasPoint>;
  regions: AtlasRegion[];
}
export interface AtlasDocument {
  format: 'histree-atlas';
  version: 1;
  width: 576;
  height: 390;
  snapshots: AtlasSnapshot[];
}
export function regionPoints(snapshot: AtlasSnapshot, region: AtlasRegion): string {
  return region.nodes.map(id => snapshot.nodes[id].join(',')).join(' ');
}
export function snapshotAt(document: AtlasDocument, year: number) {
  // An undrawn year has no map. Never silently carry 907 borders into a later year.
  return document.snapshots.find(snapshot => snapshot.year === year);
}
export function cloneSnapshot(snapshot: AtlasSnapshot, year: number): AtlasSnapshot {
  return {...structuredClone(snapshot), id: crypto.randomUUID(), year, title: `${year} 年底图草稿`, reference: null};
}
export function parseAtlas(raw: string): AtlasDocument {
  const document = JSON.parse(raw) as AtlasDocument;
  if (!document || document.format !== 'histree-atlas' || document.version !== 1 || document.width !== 576 || document.height !== 390 || !Array.isArray(document.snapshots) || !document.snapshots.length || document.snapshots.length > 50) throw Error('请导入 Histree 底图 JSON，最多 50 个年份版本。');
  const years = new Set<number>();
  const ids = new Set<string>();
  const text = (s: unknown): s is string => typeof s === 'string' && s.length <= 4000;
  const point = (p: unknown): p is AtlasPoint => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite) && p[0] >= 0 && p[0] <= 576 && p[1] >= 0 && p[1] <= 390;
  for (const snapshot of document.snapshots) {
    if (!snapshot || !text(snapshot.id) || !snapshot.id || ids.has(snapshot.id) || !Number.isSafeInteger(snapshot.year) || snapshot.year === 0 || years.has(snapshot.year) || !text(snapshot.title) || !text(snapshot.source) || snapshot.status !== 'draft' || ![null, 'shituguan-907'].includes(snapshot.reference)) throw Error('底图年份、ID、出处或草稿状态不合法；年份不能重复。');
    ids.add(snapshot.id); years.add(snapshot.year);
    if (!snapshot.nodes || Array.isArray(snapshot.nodes) || typeof snapshot.nodes !== 'object' || Object.keys(snapshot.nodes).length > 10000 || !Object.values(snapshot.nodes).every(point) || !Array.isArray(snapshot.regions) || snapshot.regions.length > 500) throw Error('底图顶点或分块超出支持范围。');
    const regions = new Set<string>();
    for (const region of snapshot.regions) {
      if (!region || !text(region.id) || !region.id || regions.has(region.id) || !text(region.name) || !text(region.note) || !/^#[0-9a-f]{6}$/i.test(region.color) || !point(region.label) || !Array.isArray(region.nodes) || region.nodes.length < 3 || new Set(region.nodes).size !== region.nodes.length || !region.nodes.every(id => typeof id === 'string' && Object.hasOwn(snapshot.nodes, id))) throw Error('分块名称、颜色、顶点引用或标签位置不合法。');
      regions.add(region.id);
    }
  }
  return document;
}
