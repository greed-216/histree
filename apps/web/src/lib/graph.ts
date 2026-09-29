import type { Edge, GraphResponse, Person, Event, ClaimSubject } from '@histree/shared-types';
export type GraphEntry = Person | Event;
export type Point = {x:number; y:number};
export type GraphSelection = {kind:'node' | 'edge'; id:string} | null;
export function edgeKey(edge: Edge): string {
  return `${edge.subject_table ?? 'relation'}:${edge.id ?? `${edge.source}:${edge.target}:${edge.type}`}`;
}
export function edgeSubject(edge: Edge, nodes: GraphEntry[]): ClaimSubject {
  if (edge.subject_table) return edge.subject_table;
  const source=nodes.find(n=>n.id===edge.source), target=nodes.find(n=>n.id===edge.target);
  return source?.type==='person' && target?.type==='person' ? 'person_relationship' : source?.type==='event' && target?.type==='event' ? 'event_causality' : 'person_event';
}
export function neighborhood(data: GraphResponse, id: string, depth: number): Set<string> {
  const found=new Set([id]);
  for(let i=0;i<depth;i++) {
    const frontier=new Set(found);
    data.edges.forEach(e=>{if(frontier.has(e.source)||frontier.has(e.target)){found.add(e.source);found.add(e.target);}});
  }
  return found;
}
export function sortedEvents(nodes: GraphEntry[]): Event[] {
  // Stable input order is retained for equal years; no invented day/month ordering.
  return nodes.filter((n): n is Event=>n.type==='event').sort((a,b)=>(a.start_year ?? Infinity)-(b.start_year ?? Infinity));
}
export function clipToCard(from: Point, to: Point): Point {
  const dx=to.x-from.x,dy=to.y-from.y;
  if(dx===0&&dy===0)return from;
  const scale=Math.min(86/Math.max(Math.abs(dx),.001),38/Math.max(Math.abs(dy),.001));
  return {x:from.x+dx*scale,y:from.y+dy*scale};
}
export function edgeCurve(a: Point, b: Point, bend=0) {
  if(a.x===b.x&&a.y===b.y)return {path:`M ${a.x+70} ${a.y-38} C ${a.x+180} ${a.y-170},${a.x-180} ${a.y-170},${a.x-70} ${a.y-38}`,label:{x:a.x,y:a.y-125}};
  const start=clipToCard(a,b),end=clipToCard(b,a);
  const length=Math.hypot(b.x-a.x,b.y-a.y);
  const control={x:(start.x+end.x)/2-(b.y-a.y)/length*bend,y:(start.y+end.y)/2+(b.x-a.x)/length*bend};
  return {path:`M ${start.x} ${start.y} Q ${control.x} ${control.y} ${end.x} ${end.y}`,label:{x:(start.x+2*control.x+end.x)/4,y:(start.y+2*control.y+end.y)/4}};
}
export function isDrag(start: Point, current: Point) {return Math.hypot(current.x-start.x,current.y-start.y)>=6;}

export type GraphViewMode = 'people' | 'events';
export function graphForView(data: GraphResponse, mode: GraphViewMode): GraphResponse {
  const nodes=data.nodes.filter(n=>mode==='events'||n.type==='person');
  const ids=new Set(nodes.map(n=>n.id));
  const subject=mode==='people'?'person_relationship':'person_event';
  return {...data,nodes,edges:data.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&edgeSubject(e,data.nodes)===subject)};
}
