import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useTranslation } from 'react-i18next';
import type { GraphData, Person, Event } from '@histree/shared-types';

// Type guard helpers
const isPerson = (node: Person | Event): node is Person => 'era' in node;

const Graph: React.FC = () => {
  const { t } = useTranslation();
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [data, setData] = useState<GraphData | null>(null);

  useEffect(() => {
    // Fetch data from backend
    fetch(import.meta.env.VITE_API_URL || 'http://localhost:3000/api/graph/demo')
      .then((res) => res.json())
      .then((data: GraphData) => setData(data))
      .catch((err) => {
        console.warn('Failed to fetch graph data, using mock data fallback:', err);
        // Provide mock data
        setData({
          nodes: [
            { id: 'p1', name: 'Liu Bei', era: 'Three Kingdoms', description: 'Founder of Shu Han' } as Person,
            { id: 'p2', name: 'Zhuge Liang', era: 'Three Kingdoms', description: 'Chancellor of Shu Han' } as Person,
            { id: 'e1', title: 'Battle of Red Cliffs', time_start: 208, time_end: 208, description: 'Decisive battle at the end of the Han dynasty', dynasty: 'Eastern Han', impact_level: 10 } as Event,
          ],
          links: [
            { id: 'r1', source: 'p1', target: 'p2', type: 'ruler', description: 'Liu Bei recruited Zhuge Liang' },
            { id: 'r2', source: 'p2', target: 'e1', type: 'participant', description: 'Zhuge Liang planned the alliance' },
            { id: 'r3', source: 'p1', target: 'e1', type: 'participant', description: 'Liu Bei led allied forces' },
          ]
        });
      });
  }, []);

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

    // We must clone nodes and links so D3 doesn't mutate our React state directly
    const nodes = data.nodes.map(d => Object.create(d));
    const links = data.links.map(d => Object.create(d));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(180))
      .force('charge', d3.forceManyBody().strength(-800))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(50));

    // Links container
    const linkGroup = svg.append('g').attr('class', 'links');
    const link = linkGroup.selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Link Labels
    const linkLabel = linkGroup.selectAll('text')
      .data(links)
      .join('text')
      .attr('class', 'link-label')
      .text((d: any) => t(d.type))
      .attr('font-size', '10px')
      .attr('fill', '#64748b')
      .attr('text-anchor', 'middle')
      .attr('dy', -4);

    // Nodes container
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    const node = nodeGroup.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(drag(simulation) as any)
      .on('mouseover', (event, d: any) => {
        d3.select(event.currentTarget).select('circle')
          .transition().duration(200)
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 3);
        
        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.html(`
          <div class="font-bold text-slate-800 mb-1">${t(isPerson(d) ? d.name : d.title)}</div>
          <div class="text-xs text-slate-500 mb-1">${isPerson(d) ? t('Era: ') + t(d.era) : t('Time: ') + d.time_start}</div>
          <div class="text-sm text-slate-600">${t(d.description)}</div>
        `)
          .style('left', (event.pageX + 15) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', (event) => {
        d3.select(event.currentTarget).select('circle')
          .transition().duration(200)
          .attr('stroke', '#fff')
          .attr('stroke-width', 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    node.append('circle')
      .attr('r', 24)
      .attr('fill', (d: any) => isPerson(d) ? '#38bdf8' : '#fb923c') // sky-400 and orange-400
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('filter', 'drop-shadow(0px 2px 4px rgba(0,0,0,0.1))');

    node.append('text')
      .text((d: any) => t(isPerson(d) ? d.name : d.title))
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', '#334155')
      .attr('dx', 30)
      .attr('dy', 4);

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

  }, [data, t]);

  // Drag function for d3 nodes
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

    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  };

  if (!data) return <div className="flex justify-center items-center h-64 text-slate-400">{t('loading')}</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden" ref={containerRef}>
      <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h2 className="text-lg font-semibold text-slate-700">{t('demoTitle')}</h2>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-400 inline-block shadow-sm"></span>
            <span className="text-slate-600">{t('person')}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-orange-400 inline-block shadow-sm"></span>
            <span className="text-slate-600">{t('event')}</span>
          </div>
        </div>
      </div>
      <div className="relative">
        <svg ref={svgRef} className="w-full h-[600px] cursor-grab active:cursor-grabbing"></svg>
      </div>
    </div>
  );
};

function App() {
  const { t, i18n } = useTranslation();

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4">
          <div>
            <h1 className="text-4xl font-bold text-slate-800 tracking-tight mb-2">{t('title')}</h1>
            <p className="text-slate-500 text-lg">{t('subtitle')}</p>
          </div>
          
          {/* Improved Language Toggle */}
          <div className="flex bg-slate-200/60 p-1 rounded-lg shrink-0 self-start md:self-auto">
            <button 
              onClick={() => i18n.changeLanguage('zh')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all cursor-pointer ${
                i18n.language === 'zh' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              中文
            </button>
            <button 
              onClick={() => i18n.changeLanguage('en')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all cursor-pointer ${
                i18n.language === 'en' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              EN
            </button>
          </div>
        </div>
        
        <Graph />
        
        <footer className="text-center text-slate-400 text-sm pt-8">
          © {new Date().getFullYear()} Histree MVP
        </footer>
      </div>
    </div>
  );
}

export default App;
