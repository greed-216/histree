import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { GraphData, Person, Event } from '@histree/shared-types';
import './App.css';

// Type guard helpers
const isPerson = (node: Person | Event): node is Person => 'era' in node;

const Graph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [data, setData] = useState<GraphData | null>(null);

  useEffect(() => {
    // Fetch data from backend
    fetch(import.meta.env.VITE_API_URL || 'http://localhost:3000/api/graph/demo')
      .then((res) => res.json())
      .then((data: GraphData) => setData(data))
      .catch((err) => {
        console.warn('Failed to fetch graph data, using mock data fallback:', err);
        // Provide mock data so the D3 visualization works on GitHub Pages
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
    if (!data || !svgRef.current) return;

    const width = 800;
    const height = 600;

    const svg = d3.select(svgRef.current)
      .attr('viewBox', [0, 0, width, height])
      .style('background', '#f9f9f9')
      .style('border', '1px solid #ccc');

    svg.selectAll('*').remove();

    // Setup simulation
    // We must clone nodes and links so D3 doesn't mutate our React state directly
    const nodes = data.nodes.map(d => Object.create(d));
    const links = data.links.map(d => Object.create(d));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', 2);

    const node = svg.append('g')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 20)
      .attr('fill', (d: any) => isPerson(d) ? '#1f77b4' : '#ff7f0e')
      .call(drag(simulation) as any);

    // Labels
    const labels = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d: any) => isPerson(d) ? d.name : d.title)
      .attr('font-size', '12px')
      .attr('dx', 25)
      .attr('dy', 4);

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

  }, [data]);

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

  return (
    <div className="Graph-container">
      <h2>Histree MVP Demo</h2>
      <svg ref={svgRef} width={800} height={600}></svg>
      <div style={{ marginTop: '1rem' }}>
        <span style={{ color: '#1f77b4', marginRight: '1rem' }}>● Person</span>
        <span style={{ color: '#ff7f0e' }}>● Event</span>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App" style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Histree</h1>
      <p>A graph-driven platform for exploring Chinese history.</p>
      <Graph />
    </div>
  );
}

export default App;
