import React, { useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import * as d3 from 'd3';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { GraphResponse, Person, Event, Edge } from '@histree/shared-types';
import { UserIcon, AcademicCapIcon, MapIcon, ArrowLeftIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { entryPath } from '../lib/reading';
import { useResource } from '../hooks/useResource';
import { edgeTypeLabel, formatDisplayRange, formatDisplayYear, referenceTypeLabel } from '../lib/content';

// Fix leaflet default icon
delete (L.Icon.Default.prototype as L.Icon.Default & { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const isPerson = (node: Person | Event): node is Person => node.type === 'person';

const tagList = (node: Person | Event) => node.tags ?? [];

type GraphNode = (Person | Event) & d3.SimulationNodeDatum;
type GraphEdge = Omit<Edge, 'source' | 'target'> & { source: GraphNode; target: GraphNode };
const drag = (simulation: d3.Simulation<GraphNode, GraphEdge>) => {
    function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    return d3.drag<SVGGElement, GraphNode>().on('start', dragstarted).on('drag', dragged).on('end', dragended);
  };

export const GraphPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error } = useResource<GraphResponse>(`/graph/${id}`);
  return <GraphView data={data} loading={loading} error={error} />;
};

export function GraphView({ data, loading = false, error, overview = false }: { data?: GraphResponse; loading?: boolean; error?: string; overview?: boolean }) {
  const navigate = useNavigate();
  const selectedNode = data?.center;
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!data || !svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 800;
    const height = 600;

    const svg = d3.select(svgRef.current)
      .attr('viewBox', [0, 0, width, height]);

    svg.selectAll('*').remove();

    // Tooltip div
    d3.select(containerRef.current).selectAll('.d3-tooltip').remove();
    const tooltip = d3.select(containerRef.current)
      .append('div')
      .attr('class', 'd3-tooltip');

    // Arrow markers
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 28) // Shift arrow back so it doesn't hide under node
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#94a3b8')
      .style('stroke','none');

    const nodes: GraphNode[] = data.nodes.map(d => ({ ...d }));
    const byId = new Map(nodes.map(n => [n.id, n]));
    const edges: GraphEdge[] = data.edges.filter(e => byId.has(e.source) && byId.has(e.target))
      .map(e => ({ ...e, source: byId.get(e.source)!, target: byId.get(e.target)! }));

    // Create defs for image patterns
    const defs = svg.select('defs');
    nodes.forEach((n) => {
      if (n.image_url) {
        defs.append('pattern')
          .attr('id', `img-${n.id}`)
          .attr('patternUnits', 'objectBoundingBox')
          .attr('width', 1)
          .attr('height', 1)
          .append('image')
          .attr('href', n.image_url)
          .attr('width', isPerson(n) ? 56 : 64) // diameter for circle, width for rect
          .attr('height', isPerson(n) ? 56 : 48)
          .attr('preserveAspectRatio', 'xMidYMid slice');
      }
    });

    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphEdge>(edges).id((d) => d.id).distance(180))
      .force('charge', d3.forceManyBody().strength(-800))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(60));

    // Links container
    const linkGroup = svg.append('g').attr('class', 'links');
    const link = linkGroup.selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', (d) => d.type === 'causes' ? '#f87171' : '#cbd5e1')
      .attr('stroke-width', (d) => d.type === 'causes' ? 3 : 2)
      .attr('stroke-dasharray', (d) => d.type === 'causes' ? '4,4' : 'none')
      .attr('marker-end', 'url(#arrowhead)');

    // Link Labels
    const linkLabel = linkGroup.selectAll('text')
      .data(edges)
      .join('text')
      .attr('class', 'link-label')
      .text((d) => edgeTypeLabel(d.type))
      .attr('font-size', '10px')
      .attr('font-weight', (d) => d.type === 'causes' ? 'bold' : 'normal')
      .attr('fill', (d) => d.type === 'causes' ? '#ef4444' : '#64748b')
      .attr('text-anchor', 'middle')
      .attr('dy', -4)
      .style('background', 'white');

    // Nodes container
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    const node = nodeGroup.selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node cursor-pointer')
      .attr('role', 'link')
      .attr('tabindex', 0)
      .attr('aria-label', d => isPerson(d) ? d.name : d.title)
      .on('keydown', (event, d) => { if (event.key === 'Enter') navigate(`/graph/${d.id}`); })
      .call(drag(simulation))
      .on('click', (_event, d) => {
        navigate(`/graph/${d.id}`);
      })
      .on('mouseover', (event, d) => {
        d3.select(event.currentTarget).select(isPerson(d) ? 'circle' : 'rect')
          .transition().duration(200)
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 4);
        
        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.text(`${isPerson(d) ? d.name : d.title} · ${isPerson(d) ? d.era || '时代待补充' : formatDisplayRange(d.start_year, d.end_year)}`);
        const [x, y] = d3.pointer(event, containerRef.current);
        tooltip.style('left', `${x + 15}px`).style('top', `${y + 15}px`);
      })
      .on('mouseout', (event, d) => {
        d3.select(event.currentTarget).select(isPerson(d) ? 'circle' : 'rect')
          .transition().duration(200)
          .attr('stroke', d.id === data.center?.id ? '#10b981' : '#fff')
          .attr('stroke-width', d.id === data.center?.id ? 4 : 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Render Person as Circle
    node.filter((d) => isPerson(d))
      .append('circle')
      .attr('r', 28)
      .attr('fill', (d) => d.image_url ? `url(#img-${d.id})` : '#38bdf8') // sky-400
      .attr('stroke', (d) => d.id === data.center?.id ? '#10b981' : '#fff')
      .attr('stroke-width', (d) => d.id === data.center?.id ? 4 : 2)
      .attr('filter', 'drop-shadow(0px 4px 6px rgba(0,0,0,0.1))');

    // Render Event as Rectangle
    node.filter((d) => !isPerson(d))
      .append('rect')
      .attr('width', 64)
      .attr('height', 48)
      .attr('x', -32)
      .attr('y', -24)
      .attr('rx', 12)
      .attr('fill', (d) => d.image_url ? `url(#img-${d.id})` : '#fb923c') // orange-400
      .attr('stroke', (d) => d.id === data.center?.id ? '#10b981' : '#fff')
      .attr('stroke-width', (d) => d.id === data.center?.id ? 4 : 2)
      .attr('filter', 'drop-shadow(0px 4px 6px rgba(0,0,0,0.1))');

    node.append('text')
      .text((d) => isPerson(d) ? d.name : d.title)
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', '#1e293b')
      .attr('dx', (d) => isPerson(d) ? 34 : 36)
      .attr('dy', 4)
      .style('text-shadow', '0 1px 3px rgba(255,255,255,0.8), 0 -1px 3px rgba(255,255,255,0.8), 1px 0 3px rgba(255,255,255,0.8), -1px 0 3px rgba(255,255,255,0.8)');

    simulation.on('end', () => {
      const bounds = nodeGroup.node()?.getBBox();
      if (bounds) svg.attr('viewBox', [bounds.x - 40, bounds.y - 40, bounds.width + 80, bounds.height + 80]);
    });

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source.x ?? 0))
        .attr('y1', (d) => (d.source.y ?? 0))
        .attr('x2', (d) => (d.target.x ?? 0))
        .attr('y2', (d) => (d.target.y ?? 0));
      
      linkLabel
        .attr('x', (d) => ((d.source.x ?? 0) + (d.target.x ?? 0)) / 2)
        .attr('y', (d) => ((d.source.y ?? 0) + (d.target.y ?? 0)) / 2);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); tooltip.remove(); };
  }, [data, navigate]);

  if (loading) {
    return <div className="flex justify-center items-center h-96 text-slate-400">加载中...</div>;
  }

  if (error) return <p role="alert" className="py-16 text-center">图谱暂时无法加载，请刷新重试。</p>;

  if (!data || !selectedNode) {
    return <div className="flex justify-center items-center h-96 text-slate-400">未找到该节点数据</div>;
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Graph Area */}
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col relative" ref={containerRef}>
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 absolute top-0 w-full z-10 opacity-90 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-200 rounded-lg text-slate-500 transition-colors">
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-bold text-slate-700 flex items-center gap-2">
              <MapIcon className="w-5 h-5 text-sky-500" />
              关系图谱
            </h2>
          </div>
          <div className="flex gap-4 text-sm font-medium">
            <div className="flex items-center gap-2 bg-sky-50 px-2 py-1 rounded-md text-sky-700">
              <span className="w-3 h-3 rounded-full bg-sky-400 inline-block"></span>
              人物
            </div>
            <div className="flex items-center gap-2 bg-orange-50 px-2 py-1 rounded-md text-orange-700">
              <span className="w-4 h-3 rounded-sm bg-orange-400 inline-block"></span>
              事件
            </div>
          </div>
        </div>
        <svg aria-label="人物与事件关系图谱" ref={svgRef} className="w-full h-[600px] lg:h-[800px] cursor-grab active:cursor-grabbing bg-slate-50/50 mt-16"></svg>
      </div>

      {/* Info Panel */}
      {!overview && <div className="w-full lg:w-96 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-y-auto h-[600px] lg:h-[800px] flex flex-col shrink-0">
        <div className="p-6 border-b border-slate-100 sticky top-0 bg-white/95 backdrop-blur-sm z-10">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            {isPerson(selectedNode) ? <UserIcon className="w-4 h-4" /> : <AcademicCapIcon className="w-4 h-4" />}
            {isPerson(selectedNode) ? '人物条目' : '事件条目'}
          </h3>
          <h1 className="text-3xl font-extrabold text-slate-800 mb-2">
            {isPerson(selectedNode) ? selectedNode.name : selectedNode.title}
          </h1>
          <Link to={entryPath(selectedNode)} className="block text-teal-700 text-sm mb-4">阅读全文与出处 →</Link>
          <div className="inline-flex px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-sm font-semibold border border-slate-200">
            {isPerson(selectedNode) ? selectedNode.era || '时代待补充' : formatDisplayRange(selectedNode.start_year, selectedNode.end_year)}
          </div>
        </div>
        
        <div className="p-6 flex-1 space-y-8">
          {selectedNode.image_url && (
            <div className="w-full rounded-xl overflow-hidden border border-slate-200 shadow-sm">
              <img src={selectedNode.image_url} alt={isPerson(selectedNode) ? selectedNode.name : selectedNode.title} className="w-full h-48 object-cover" />
            </div>
          )}

          {tagList(selectedNode).length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tagList(selectedNode).map((tag) => (
                <span key={tag} className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-xs font-medium text-slate-600">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {isPerson(selectedNode) && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">人物信息</h4>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                {selectedNode.courtesy_name && (
                  <div>
                    <dt className="text-slate-400">字</dt>
                    <dd className="font-medium text-slate-700">{selectedNode.courtesy_name}</dd>
                  </div>
                )}
                {selectedNode.faction && (
                  <div>
                    <dt className="text-slate-400">阵营</dt>
                    <dd className="font-medium text-slate-700">{selectedNode.faction}</dd>
                  </div>
                )}
                {selectedNode.native_place && (
                  <div>
                    <dt className="text-slate-400">籍贯</dt>
                    <dd className="font-medium text-slate-700">{selectedNode.native_place}</dd>
                  </div>
                )}
                {(selectedNode.birth_year || selectedNode.death_year) && (
                  <div>
                    <dt className="text-slate-400">生卒</dt>
                    <dd className="font-medium text-slate-700">{formatDisplayYear(selectedNode.birth_year)} - {formatDisplayYear(selectedNode.death_year)}</dd>
                  </div>
                )}
              </dl>
              {selectedNode.aliases && selectedNode.aliases.length > 0 && (
                <div className="mt-3 text-sm text-slate-600">
                  <span className="text-slate-400">别名：</span>{selectedNode.aliases.join('、')}
                </div>
              )}
            </div>
          )}

          <div>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">概述</h4>
            <p className="text-slate-600 leading-relaxed text-base">
              {selectedNode.description || '暂无描述信息。'}
            </p>
          </div>

          {isPerson(selectedNode) && selectedNode.biography && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">生平</h4>
              <p className="text-slate-600 leading-relaxed text-base whitespace-pre-line">{selectedNode.biography}</p>
            </div>
          )}

          {isPerson(selectedNode) && selectedNode.historical_evaluation && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">历史评价</h4>
              <p className="text-slate-600 leading-relaxed text-base whitespace-pre-line">{selectedNode.historical_evaluation}</p>
            </div>
          )}

          {isPerson(selectedNode) && selectedNode.family && selectedNode.family.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">亲属关系</h4>
              <div className="space-y-2">
                {selectedNode.family.map((item, index) => (
                  <div key={`${item.name}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                    <div className="text-sm font-semibold text-slate-700">{item.name} <span className="text-slate-400 font-normal">/ {item.relation}</span></div>
                    {item.note && <div className="text-xs text-slate-500 mt-1">{item.note}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {isPerson(selectedNode) && selectedNode.social_relations && selectedNode.social_relations.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">交际关系</h4>
              <div className="space-y-2">
                {selectedNode.social_relations.map((item, index) => (
                  <div key={`${item.name}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                    <div className="text-sm font-semibold text-slate-700">{item.name} <span className="text-slate-400 font-normal">/ {item.relation}</span></div>
                    {item.note && <div className="text-xs text-slate-500 mt-1">{item.note}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedNode.references && selectedNode.references.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">参考资料</h4>
              <div className="space-y-2">
                {selectedNode.references.map((reference, index) => (
                  <div key={`${reference.title}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-700">{reference.title}</div>
                      <span className="shrink-0 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[11px] text-slate-500">
                        {referenceTypeLabel(reference.reference_type)}
                      </span>
                    </div>
                    {reference.note && <div className="text-xs text-slate-500 mt-1 leading-relaxed">{reference.note}</div>}
                    {reference.url && (
                      <a href={reference.url} target="_blank" rel="noreferrer" className="text-xs text-sky-600 hover:text-sky-700 mt-2 inline-block break-all">
                        {reference.url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!isPerson(selectedNode) && selectedNode.phases && selectedNode.phases.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">事件阶段</h4>
              <div className="space-y-3">
                {selectedNode.phases.map((phase, index) => (
                  <div key={`${phase.title}-${index}`} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                    <div className="text-sm font-semibold text-slate-700">{phase.title}</div>
                    {(phase.start_year || phase.end_year) && <div className="text-xs text-slate-400">{formatDisplayRange(phase.start_year, phase.end_year)}</div>}
                    {phase.description && <div className="text-xs text-slate-500 mt-1 leading-relaxed">{phase.description}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!isPerson(selectedNode) && selectedNode.location_lat && selectedNode.location_lng && (
            <div>
              <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1">
                <MapPinIcon className="w-4 h-4" /> 地点{selectedNode.location_name ? ` - ${selectedNode.location_name}` : ''}
              </h4>
              <div className="w-full h-48 rounded-xl overflow-hidden border border-slate-200 shadow-sm z-0 relative">
                <MapContainer 
                  center={[selectedNode.location_lat, selectedNode.location_lng]} 
                  zoom={6} 
                  scrollWheelZoom={false}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <Marker position={[selectedNode.location_lat, selectedNode.location_lng]}>
                    {selectedNode.location_name && <Popup>{selectedNode.location_name}</Popup>}
                  </Marker>
                </MapContainer>
              </div>
            </div>
          )}
          
          <div>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">相关节点</h4>
            <div className="space-y-2">
              {data.nodes.filter(n => n.id !== selectedNode.id).slice(0, 8).map(n => (
                <Link 
                  key={n.id} 
                  to={`/graph/${n.id}`}
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-sky-200 hover:bg-sky-50 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isPerson(n) ? 'bg-sky-100 text-sky-600' : 'bg-orange-100 text-orange-600'}`}>
                      {isPerson(n) ? <UserIcon className="w-4 h-4" /> : <AcademicCapIcon className="w-4 h-4" />}
                    </div>
                    <span className="font-semibold text-slate-700 group-hover:text-sky-700">{isPerson(n) ? n.name : n.title}</span>
                  </div>
                  <ArrowLeftIcon className="w-4 h-4 text-slate-300 group-hover:text-sky-500 rotate-180" />
                </Link>
              ))}
              {data.nodes.length > 9 && (
                <div className="text-center text-sm text-slate-400 pt-2">+ {data.nodes.length - 9} 个更多节点仍在图中</div>
              )}
            </div>
          </div>
        </div>
      </div>}
    </div>
  );
};
