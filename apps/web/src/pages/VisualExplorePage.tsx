import { MAPS_ENABLED } from '../lib/features';
import { lazy, Suspense, useMemo } from 'react';
import { Link } from 'react-router-dom';
import type { Person, Event, RelationshipBundle, GraphResponse } from '@histree/shared-types';
import { useResource } from '../hooks/useResource';
import { LoadState } from '../components/Reading';
import { TopicExplorer } from '../components/TopicExplorer';
import { GraphView } from './GraphPage';
const HistoricalMap = lazy(() => import('../components/HistoricalMap'));

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
      ...r.person_relationships.map(e => ({ id: e.id, subject_table: 'person_relationship' as const, source: e.person_a, target: e.person_b, type: e.relation_type, description: e.description })),
      ...r.person_events.map(e => ({ id: e.id, subject_table: 'person_event' as const, source: e.person_id, target: e.event_id, type: e.role })),
      ...r.event_causalities.map(e => ({ id: e.id, subject_table: 'event_causality' as const, source: e.cause_event_id, target: e.effect_event_id, type: 'causes', description: e.description })),
    ] };
  }, [people.data, events.data, relationships.data]);
  const loading = people.loading || events.loading || (mode === 'graph' && relationships.loading);
  const error = people.error || events.error || (mode === 'graph' ? relationships.error : undefined);
  return <div className="space-y-6">
    <header>
      <h1 className="font-serif text-3xl">{mode === 'graph' ? '人物与事件图谱' : '历史地图'}</h1>
      <p className="mt-3 text-slate-600 leading-7">{mode === 'graph'
        ? '分开探索人物之间的关系与人物参与的事件。自由拖动节点，点击人物、事件或连线查看详情与史料依据。'
        : '按年份加载独立的疆域底图，点击地块查看分区；在底图工坊中描绘边界、制作新时期版本。'}</p>
      {mode === 'map' && <Link to="/map/edit" className="inline-block mt-4 mr-4 rounded-lg bg-teal-800 text-white px-4 py-3">打开底图工坊 →</Link>}
      {MAPS_ENABLED && <Link to={mode === 'graph' ? '/map' : '/graph'} className="inline-block mt-3 text-teal-700 underline">{mode === 'graph' ? '切换到地图 →' : '切换到图谱 →'}</Link>}
    </header>
    {mode === 'map' && <Suspense fallback={<p>正在加载疆域底图…</p>}><HistoricalMap /></Suspense>}
    <LoadState loading={loading} error={error} retry={() => { people.retry(); events.retry(); relationships.retry(); }} />
    {!loading && !error && (mode === 'graph'
      ? graph ? <GraphView data={graph} overview /> : <p>已发布内容整理后将在这里展示图谱。</p>
      : <TopicExplorer events={events.data ?? []} people={people.data ?? []} />)}
  </div>;
}
