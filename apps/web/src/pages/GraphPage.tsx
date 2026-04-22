import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import * as d3 from 'd3';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { GraphResponse, Person, Event } from '@histree/shared-types';
import { UserIcon, AcademicCapIcon, MapIcon, ArrowLeftIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { apiFetch } from '../lib/api';
import { formatDisplayRange, formatDisplayYear, referenceTypeLabel } from '../lib/content';

// Fix leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const isPerson = (node: Person | Event): node is Person => node.type === 'person';

const tagList = (node: Person | Event) => node.tags ?? [];

export const GraphPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Person | Event | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setSelectedNode(null);

    apiFetch<GraphResponse>(`/graph/${id}`)
      .then((data: GraphResponse) => {
        setData(data);
        setSelectedNode(data.center);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch graph data:', err);
        setLoading(false);
      });
  }, [id]);

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

    const nodes = data.nodes.map(d => Object.create(d));
    const edges = data.edges.map(d => Object.create(d));

    // Create defs for image patterns
    const defs = svg.select('defs');
    nodes.forEach((n: any) => {
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

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id((d: any) => d.id).distance(180))
      .force('charge', d3.forceManyBody().strength(-800))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(60));

    // Links container
    const linkGroup = svg.append('g').attr('class', 'links');
    const link = linkGroup.selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', (d: any) => d.type === 'causes' ? '#f87171' : '#cbd5e1')
      .attr('stroke-width', (d: any) => d.type === 'causes' ? 3 : 2)
      .attr('stroke-dasharray', (d: any) => d.type === 'causes' ? '4,4' : 'none')
      .attr('marker-end', 'url(#arrowhead)');

    // Link Labels
    const linkLabel = linkGroup.selectAll('text')
      .data(edges)
      .join('text')
      .attr('class', 'link-label')
      .text((d: any) => d.type)
      .attr('font-size', '10px')
      .attr('font-weight', (d: any) => d.type === 'causes' ? 'bold' : 'normal')
      .attr('fill', (d: any) => d.type === 'causes' ? '#ef4444' : '#64748b')
      .attr('text-anchor', 'middle')
      .attr('dy', -4)
      .style('background', 'white');

    // Nodes container
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    const node = nodeGroup.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node cursor-pointer')
      .call(drag(simulation) as any)
      .on('click', (_event, d: any) => {
        setSelectedNode(d);
        navigate(`/graph/${d.id}`);
      })
      .on('mouseover', (event, d: any) => {
        d3.select(event.currentTarget).select(isPerson(d) ? 'circle' : 'rect')
          .transition().duration(200)
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 4);
        
        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.html(`
          <div class="font-bold text-slate-800 mb-1">${isPerson(d) ? d.name : d.title}</div>
          <div class="text-xs text-slate-500 mb-1">${isPerson(d) ? `时代：${d.era || '待补充'}` : `时间：${formatDisplayRange(d.start_year, d.end_year)}`}</div>
        `)
          .style('left', (event.pageX + 15) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', (event, d: any) => {
        d3.select(event.currentTarget).select(isPerson(d) ? 'circle' : 'rect')
          .transition().duration(200)
          .attr('stroke', d.id === data.center?.id ? '#10b981' : '#fff')
          .attr('stroke-width', d.id === data.center?.id ? 4 : 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Render Person as Circle
    node.filter((d: any) => isPerson(d))
      .append('circle')
      .attr('r', 28)
      .attr('fill', (d: any) => d.image_url ? `url(#img-${d.id})` : '#38bdf8') // sky-400
      .attr('stroke', (d: any) => d.id === data.center?.id ? '#10b981' : '#fff')
      .attr('stroke-width', (d: any) => d.id === data.center?.id ? 4 : 2)
      .attr('filter', 'drop-shadow(0px 4px 6px rgba(0,0,0,0.1))');

    // Render Event as Rectangle
    node.filter((d: any) => !isPerson(d))
      .append('rect')
      .attr('width', 64)
      .attr('height', 48)
      .attr('x', -32)
      .attr('y', -24)
      .attr('rx', 12)
      .attr('fill', (d: any) => d.image_url ? `url(#img-${d.id})` : '#fb923c') // orange-400
      .attr('stroke', (d: any) => d.id === data.center?.id ? '#10b981' : '#fff')
      .attr('stroke-width', (d: any) => d.id === data.center?.id ? 4 : 2)
      .attr('filter', 'drop-shadow(0px 4px 6px rgba(0,0,0,0.1))');

    node.append('text')
      .text((d: any) => isPerson(d) ? d.name : d.title)
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', '#1e293b')
      .attr('dx', (d: any) => isPerson(d) ? 34 : 36)
      .attr('dy', 4)
      .style('text-shadow', '0 1px 3px rgba(255,255,255,0.8), 0 -1px 3px rgba(255,255,255,0.8), 1px 0 3px rgba(255,255,255,0.8), -1px 0 3px rgba(255,255,255,0.8)');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      
      linkLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

  }, [data, navigate]);

  const drag = (simulation: d3.Simulation<any, any>) => {
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-96 text-slate-400">加载中...</div>;
  }

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
        <svg ref={svgRef} className="w-full h-[600px] lg:h-[800px] cursor-grab active:cursor-grabbing bg-slate-50/50 mt-16"></svg>
      </div>

      {/* Info Panel */}
      <div className="w-full lg:w-96 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-y-auto h-[600px] lg:h-[800px] flex flex-col shrink-0">
        <div className="p-6 border-b border-slate-100 sticky top-0 bg-white/95 backdrop-blur-sm z-10">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            {isPerson(selectedNode) ? <UserIcon className="w-4 h-4" /> : <AcademicCapIcon className="w-4 h-4" />}
            {isPerson(selectedNode) ? '人物条目' : '事件条目'}
          </h3>
          <h1 className="text-3xl font-extrabold text-slate-800 mb-2">
            {isPerson(selectedNode) ? selectedNode.name : selectedNode.title}
          </h1>
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
      </div>
    </div>
  );
};
