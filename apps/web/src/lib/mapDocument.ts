export type Position = [number, number]; // GeoJSON: longitude, latitude (WGS84)
export type Geometry = { type: 'Point'; coordinates: Position } | { type: 'LineString'; coordinates: Position[] } | { type: 'Polygon'; coordinates: Position[][] };
export interface MapFeature { type: 'Feature'; id: string; geometry: Geometry; properties: { name: string; color: string; start_year: number; end_year: number; source: string; note: string; status: 'draft' } }
export interface MapDocument { type: 'FeatureCollection'; histree_version: 1; title: string; features: MapFeature[] }
export const emptyMap = (): MapDocument => ({ type: 'FeatureCollection', histree_version: 1, title: '后梁时期地图草稿', features: [] });
export function vertices(feature: MapFeature): Position[] { return feature.geometry.type === 'Point' ? [feature.geometry.coordinates] : feature.geometry.type === 'LineString' ? feature.geometry.coordinates : feature.geometry.coordinates[0].slice(0, -1); }
export function geometry(type: Geometry['type'], points: Position[]): Geometry {
 if (type === 'Point') return { type, coordinates: points[0] };
 if (type === 'LineString') return { type, coordinates: points };
 return { type, coordinates: [[...points, [...points[0]]]] };
}
export function parseMap(text: string): MapDocument {
 const d = JSON.parse(text);
 if (d.type !== 'FeatureCollection' || d.histree_version !== 1 || typeof d.title !== 'string' || d.title.length > 200 || !Array.isArray(d.features) || d.features.length > 500) throw Error('需要 Histree 导出的 GeoJSON 文件，最多 500 个要素。');
 const ids = new Set();
 let total = 0;
 for (const f of d.features) {
  if (f.type !== 'Feature' || typeof f.id !== 'string' || !f.id || ids.has(f.id)) throw Error('要素 ID 缺失或重复。');
  ids.add(f.id);
  const p = f.properties;
  if (!p || typeof p.name !== 'string' || p.name.length > 200 || typeof p.source !== 'string' || typeof p.note !== 'string' || !/^#[0-9a-f]{6}$/i.test(p.color) || p.status !== 'draft' || !Number.isInteger(p.start_year) || !Number.isInteger(p.end_year) || p.start_year === 0 || p.end_year === 0 || p.start_year > p.end_year) throw Error('名称、年份、颜色或草稿状态不合法。');
  const g = f.geometry;
  if (!g || !['Point','LineString','Polygon'].includes(g.type)) throw Error('只支持点、线和单环区域。');
  const points = g.type === 'Point' ? [g.coordinates] : g.type === 'LineString' ? g.coordinates : g.coordinates?.[0];
  if (!Array.isArray(points) || (g.type === 'LineString' && points.length < 2) || (g.type === 'Polygon' && (g.coordinates.length !== 1 || points.length < 4 || JSON.stringify(points[0]) !== JSON.stringify(points.at(-1))))) throw Error('几何结构不完整，区域必须闭合。');
  for (const point of points) if (!Array.isArray(point) || point.length !== 2 || !point.every(Number.isFinite) || Math.abs(point[0]) > 180 || Math.abs(point[1]) > 90) throw Error('坐标须为有效的 WGS84 经度、纬度。');
  total += points.length;
  if (total > 10000) throw Error('文件顶点过多，最多 10000 个。');
 }
 return d;
}
