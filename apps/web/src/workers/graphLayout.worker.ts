import * as d3 from "d3";

self.onmessage = ({
  data,
}: MessageEvent<{
  ids: string[];
  edges: { source: string; target: string }[];
}>) => {
  const nodes = data.ids.map((id, i) => ({
    id,
    x: 180 + (i % 4) * 260,
    y: 100 + Math.floor(i / 4) * 160,
  }));
  const small = nodes.length <= 24;
  const simulation = d3
    .forceSimulation(nodes)
    .stop()
    .force("charge", d3.forceManyBody().strength(small ? -600 : -1400))
    .force(
      "link",
      d3
        .forceLink(data.edges)
        .id((n) => (n as { id: string }).id)
        .distance(small ? 190 : 265),
    )
    .force("center", d3.forceCenter(450, 380))
    .force("x", d3.forceX(450).strength(0.12))
    .force("y", d3.forceY(380).strength(0.14))
    .force("collide", d3.forceCollide(small ? 90 : 105));
  simulation.tick(240);
  simulation.stop();
  self.postMessage(
    Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }])),
  );
};
