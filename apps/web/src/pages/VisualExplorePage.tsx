import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import type { Person, Event, RelationshipBundle, GraphResponse } from '@histree/shared-types';
import { useResource } from '../hooks/useResource';
import { LoadState } from '../components/Reading';
import { TopicExplorer } from '../components/TopicExplorer';
import { GraphView } from './GraphPage';

export function VisualExplorePage({ mode }: { mode: 'graph' | 'map' }) {
  const people = useResource<Person[]>('/people');
  const events = useResource<Event[]>('/event');
  const relationships = useResource<RelationshipBundle>('/relationships');
  const graph = useMemo<GraphResponse | undefined>(() => {
    if (!people.data || !events.data || !relationships.data) return undefined;
    const nodes = [...people.data, ...events.data];
    if (!nodes.length) return undefined;
    const r = relationships.data;
    return { center: nodes[0], nodes, edges: [
      ...r.person_relationships.map(e => ({ id: e.id, source: e.person_a, target: e.person_b, type: e.relation_type, description: e.description })),
      ...r.person_events.map(e => ({ id: e.id, source: e.person_id, target: e.event_id, type: e.role })),
      ...r.event_causalities.map(e => ({ id: e.id, source: e.cause_event_id, target: e.effect_event_id, type: 'causes', description: e.description })),
    ] };
  }, [people.data, events.data, relationships.data]);
  const loading = people.loading || events.loading || (mode === 'graph' && relationships.loading);
  const error = people.error || events.error || (mode === 'graph' ? relationships.error : undefined);
  return <div className="space-y-6">
    <header>
      <h1 className="font-serif text-3xl">{mode === 'graph' ? '人物与事件图谱' : '历史地图'}</h1>
      <p className="mt-3 text-slate-600 leading-7">{mode === 'graph'
        ? '查看已发布人物与事件的关系。拖动节点调整布局，点击节点进入它的关系图谱，再打开条目阅读出处。'
        : '对照史图馆的907年形势图阅读后梁事件，也可切换现代地理底图。历史图的年份固定，事件按各自年代展示。'}</p>
      <Link to={mode === 'graph' ? '/map' : '/graph'} className="inline-block mt-3 text-teal-700 underline">{mode === 'graph' ? '切换到地图 →' : '切换到图谱 →'}</Link>
    </header>
    <LoadState loading={loading} error={error} retry={() => { people.retry(); events.retry(); relationships.retry(); }} />
    {!loading && !error && (mode === 'graph'
      ? graph ? <><p className="text-sm text-slate-500">{graph.nodes.length} 个节点 · {graph.edges.length} 条关系</p><GraphView data={graph} overview /></> : <p>已发布内容整理后将在这里展示图谱。</p>
      : <TopicExplorer events={events.data ?? []} people={people.data ?? []} />)}
  </div>;
}
