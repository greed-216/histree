import { MAPS_ENABLED } from '../lib/features';
import { lazy, Suspense } from 'react';
import { Link } from 'react-router-dom';
import { TopicExplorer } from '../components/TopicExplorer';
import { GraphView } from './GraphPage';
const HistoricalMap = lazy(() => import('../components/HistoricalMap'));

function MapExplorePage() {
  return <div className="space-y-6">
    <header className="explore-heading">
      <p className="eyebrow">HISTREE / 图谱探索</p>
      <h1>历史地图</h1>
      <p className="mt-3 text-slate-600 leading-7">按年份加载独立的疆域底图，点击地块查看分区；在底图工坊中描绘边界、制作新时期版本。</p>
      <Link to="/map/edit" className="inline-block mt-4 mr-4 rounded-lg bg-teal-800 text-white px-4 py-3">打开底图工坊 →</Link>
      <Link to="/graph" className="inline-block mt-3 text-teal-700 underline">切换到图谱 →</Link>
    </header>
    <Suspense fallback={<p>正在加载疆域底图…</p>}><HistoricalMap /></Suspense>
    <TopicExplorer/>
  </div>;
}

export function VisualExplorePage({ mode }: { mode: 'graph' | 'map' }) {
 if(mode==='map')return <MapExplorePage/>;
 return <div className="space-y-6"><header className="explore-heading"><p className="eyebrow">HISTREE / 图谱探索</p><h1>沿着关系，读懂历史</h1><p>从一个人、一件事出发，逐层探索人物关系与历史脉络。</p>{MAPS_ENABLED&&<Link to="/map" className="inline-block mt-3 text-teal-700 underline">切换到地图 →</Link>}</header><GraphView/></div>;
}
