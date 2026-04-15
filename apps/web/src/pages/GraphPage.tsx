import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import * as d3 from 'd3';
import { useTranslation } from 'react-i18next';
import type { GraphResponse, Person, Event } from '@histree/shared-types';
import { UserIcon, AcademicCapIcon, MapIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const isPerson = (node: Person | Event): node is Person => node.type === 'person';

export const GraphPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Person | Event | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setSelectedNode(null);
    
    fetch(import.meta.env.VITE_API_URL?.replace('/graph/person/00000000-0000-0000-0000-000000000001', `/graph/${id}`) || `http://localhost:3000/api/v1/graph/${id}`)
      .then(res => res.json())
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
      .text((d: any) => t(d.type))
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
          <div class="font-bold text-slate-800 mb-1">${t(isPerson(d) ? d.name : d.title)}</div>
          <div class="text-xs text-slate-500 mb-1">${isPerson(d) ? t('Era: ') + t(d.era || '') : t('Time: ') + (d.start_year || '')}</div>
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
      .attr('fill', '#38bdf8') // sky-400
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
      .attr('fill', '#fb923c') // orange-400
      .attr('stroke', (d: any) => d.id === data.center?.id ? '#10b981' : '#fff')
      .attr('stroke-width', (d: any) => d.id === data.center?.id ? 4 : 2)
      .attr('filter', 'drop-shadow(0px 4px 6px rgba(0,0,0,0.1))');

    node.append('text')
      .text((d: any) => t(isPerson(d) ? d.name : d.title))
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

  }, [data, t, navigate]);

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
    return <div className="flex justify-center items-center h-96 text-slate-400">{t('loading')}</div>;
  }

  if (!data || !selectedNode) {
    return <div className="flex justify-center items-center h-96 text-slate-400">{t('Node not found')}</div>;
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
              {t('Interactive Graph')}
            </h2>
          </div>
          <div className="flex gap-4 text-sm font-medium">
            <div className="flex items-center gap-2 bg-sky-50 px-2 py-1 rounded-md text-sky-700">
              <span className="w-3 h-3 rounded-full bg-sky-400 inline-block"></span>
              {t('Person')}
            </div>
            <div className="flex items-center gap-2 bg-orange-50 px-2 py-1 rounded-md text-orange-700">
              <span className="w-4 h-3 rounded-sm bg-orange-400 inline-block"></span>
              {t('Event')}
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
            {isPerson(selectedNode) ? t('Person Details') : t('Event Details')}
          </h3>
          <h1 className="text-3xl font-extrabold text-slate-800 mb-2">
            {isPerson(selectedNode) ? selectedNode.name : selectedNode.title}
          </h1>
          <div className="inline-flex px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-sm font-semibold border border-slate-200">
            {isPerson(selectedNode) ? selectedNode.era : `${selectedNode.start_year || '?'} - ${selectedNode.end_year || '?'}`}
          </div>
        </div>
        
        <div className="p-6 flex-1 space-y-8">
          <div>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">{t('Description')}</h4>
            <p className="text-slate-600 leading-relaxed text-base">
              {selectedNode.description || t('No description available.')}
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">{t('Related Nodes')}</h4>
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
                <div className="text-center text-sm text-slate-400 pt-2">+ {data.nodes.length - 9} {t('more nodes in graph')}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
