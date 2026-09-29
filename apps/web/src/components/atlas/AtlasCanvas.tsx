import { useRef, useState, type PointerEvent, type ReactNode } from 'react';
import { regionPoints, type AtlasPoint, type AtlasSnapshot } from '../../lib/atlas';

interface Props {
  snapshot: AtlasSnapshot;
  selected?: string;
  onSelect: (id: string) => void;
  referenceOpacity?: number;
  referenceUrl?: string;
  editing?: boolean;
  drawing?: boolean;
  draft?: AtlasPoint[];
  onPoint?: (point: AtlasPoint) => void;
  onMoveNode?: (id: string, point: AtlasPoint) => void;
  /** Event layers can use the same canvas, without becoming part of basemap data. */
  children?: ReactNode;
}
const focusView = [297, 183, 191, 196];
export function AtlasCanvas({ snapshot, selected, onSelect, referenceOpacity = 0, referenceUrl, editing, drawing, draft = [], onPoint, onMoveNode, children }: Props) {
  const svg = useRef<SVGSVGElement>(null);
  const [view, setView] = useState(focusView);
  const [drag, setDrag] = useState<{ id: string; point: AtlasPoint }>();
  const gesture = useRef<{ start: AtlasPoint; view: number[]; node?: string; region?: string; moved: boolean } | null>(null);
  const shown = drag ? {...snapshot, nodes: {...snapshot.nodes, [drag.id]: drag.point}} : snapshot;
  const selectedRegion = shown.regions.find(region => region.id === selected);
  function point(event: PointerEvent): AtlasPoint {
    const matrix = svg.current?.getScreenCTM();
    if (!matrix) return [0, 0];
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return [Math.max(0, Math.min(576, p.x)), Math.max(0, Math.min(390, p.y))];
  }
  function zoom(factor: number) {
    setView(([x,y,w,h]) => {
      const width = Math.max(45, Math.min(576, w * factor));
      const height = width * h / w;
      return [x + (w-width)/2, y + (h-height)/2, width, height];
    });
  }
  return <div className="atlas-stage">
    <div className="atlas-tools" aria-label="底图视野">
      <button onClick={() => zoom(.75)} aria-label="放大底图">＋</button>
      <button onClick={() => zoom(1.33)} aria-label="缩小底图">−</button>
      <button onClick={() => setView(focusView)}>五代核心区</button>
      <button onClick={() => setView([0,0,576,390])}>全幅参考范围</button>
    </div>
    <svg ref={svg} viewBox={view.join(' ')} aria-label={`${snapshot.year} 年分块疆域底图`} className={`atlas-svg ${drawing ? 'atlas-drawing' : ''}`}
      onPointerDown={event => {
        if (event.button !== 0 || drawing) return;
        const node = (event.target as Element).getAttribute('data-node') ?? undefined;
        const region = (event.target as Element).closest('[data-region]')?.getAttribute('data-region') ?? undefined;
        gesture.current = {start: point(event), view: [...view], node, region, moved: false};
        if (node) setDrag({id: node, point: snapshot.nodes[node]});
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={event => {
        const g = gesture.current;
        if (!g) return;
        const p = point(event);
        if (g.node) {
          if (Math.hypot(p[0]-g.start[0], p[1]-g.start[1]) > .15) g.moved = true;
          setDrag({id: g.node, point:p});
        } else {
          // Use the initial view's scale so that movement does not feed back into panning.
          const matrix = svg.current?.getScreenCTM();
          if (!matrix) return;
          const dx = event.movementX / matrix.a, dy = event.movementY / matrix.d;
          if (Math.abs(dx)+Math.abs(dy) > .15) g.moved = true;
          setView(v => [Math.max(-100, Math.min(550,v[0]-dx)),Math.max(-100,Math.min(370,v[1]-dy)),v[2],v[3]]);
        }
      }}
      onPointerUp={event => {
        const g = gesture.current;
        if (g?.node && g.moved) onMoveNode?.(g.node,point(event));
        if (g?.region && !g.node && !g.moved) onSelect(g.region);
        gesture.current = null;
        setDrag(undefined);
        if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
      }}
      onPointerCancel={() => {gesture.current = null; setDrag(undefined);}}
      onClick={event => {
        if (drawing) {onPoint?.(point(event as unknown as PointerEvent)); return;}
      }}>
      <rect x="-1000" y="-1000" width="2500" height="2500" fill="#c5d2cc" />
      {/* Context silhouette follows the source drawing, not a modern national boundary. */}
      <path d="M0 0H576V140L550 163 531 191 514 202 502 223 481 219 466 231 466 250 458 260 454 277 464 284 457 294 462 296 459 307 451 317 445 328 439 342 427 353 414 358 401 361 390 368 372 366 353 378 333 390H220L220 374 190 374 171 359 133 351 121 339 88 347 57 332 0 330Z" fill="#e8e1ce" stroke="#9aab9e" strokeWidth=".65" />
      <g className="atlas-context" pointerEvents="none"><text x="321" y="197">周 边 区 域</text><text x="302" y="320">待 补 绘</text><text x="475" y="330" transform="rotate(90 475 330)">海 域</text></g>
      {referenceOpacity > 0 && <image href={referenceUrl ?? `${import.meta.env.BASE_URL}maps/shituguan-907.jpg`} x="0" y="0" width="576" height="390" opacity={referenceOpacity} pointerEvents="none" />}
      <g aria-label="疆域分块" className="atlas-regions">
        {shown.regions.map(region => <polygon key={region.id} points={regionPoints(shown,region)} fill={region.color} fillOpacity={1-referenceOpacity} stroke={selected === region.id ? '#fff7d4' : '#635c46'} strokeWidth={selected === region.id ? 1.2 : .55} data-region={region.id} role="button" tabIndex={drawing ? -1 : 0} aria-label={`选择地块：${region.name}`} aria-pressed={selected === region.id}
          onKeyDown={event => {if (event.key === 'Enter' || event.key === ' ') {event.preventDefault();onSelect(region.id);}}}>
          <title>{region.name} · {snapshot.year} 年 · 概略描绘稿</title>
        </polygon>)}
      </g>
      <g className="atlas-labels" opacity={1-referenceOpacity} pointerEvents="none" aria-hidden="true">
        {shown.regions.map(region => <text key={region.id} x={region.label[0]} y={region.label[1]} fontSize={region.name.length > 2 ? 4 : 5}>{region.name}</text>)}
      </g>
      <g aria-label="事件叠加层">{children}</g>
      {drawing && <g pointerEvents="none"><polyline points={draft.map(p=>p.join(',')).join(' ')} fill="none" stroke="#9c3f29" strokeWidth=".7" strokeDasharray="2 1" />{draft.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="1" fill="#9c3f29" />)}</g>}
      {editing && !drawing && selectedRegion && <g aria-label="地块边界控制点">{selectedRegion.nodes.map((id,i) => <circle key={id} data-node={id} cx={shown.nodes[id][0]} cy={shown.nodes[id][1]} r="1" fill="#fffdf0" stroke="#563f2e" strokeWidth=".35" role="button" tabIndex={0} aria-label={`边界顶点 ${i+1}`} onKeyDown={event => {
        const offsets: Record<string, AtlasPoint> = {ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
        const d=offsets[event.key]; if (!d) return;
        event.preventDefault(); const p=shown.nodes[id]; onMoveNode?.(id,[Math.max(0,Math.min(576,p[0]+d[0])),Math.max(0,Math.min(390,p[1]+d[1]))]);
      }} />)}</g>}
    </svg>
    <div className="atlas-map-caption">{snapshot.year} · 疆域描绘稿 <span>拖动平移 · 点击选中地块</span></div>
  </div>;
}
