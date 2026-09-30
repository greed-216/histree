import { Link, useSearchParams } from 'react-router-dom';
import type { SearchResponse } from '@histree/shared-types';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { useDebounced } from '../hooks/useDebounced';
import { EntryCard, LoadState } from '../components/Reading';

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';
  const kind = params.get('kind') || 'all';
  const settled = useDebounced(q.trim());
  const result = useInfiniteResource<SearchResponse>(`/search?${new URLSearchParams({ q: settled, kind, limit: '20' })}`);
  const pending = settled !== q.trim();
  function update(q: string, kind: string) { setParams({ q, kind }, { replace: true }); }
  return <div className="space-y-7">
    <header><p className="eyebrow">寻找历史线索</p><h1 className="text-3xl font-serif mt-3">搜索与浏览</h1><Link to="/ask" className="inline-block mt-3 text-sm text-teal-800 underline">想了解来龙去脉？试试问史料 →</Link></header>
    <label className="block"><span className="sr-only">搜索关键词</span><input type="search" value={q} maxLength={200} onChange={e => update(e.target.value, kind)} placeholder="姓名、别名、事件、标签…" className="reading-input text-lg" /></label>
    <div className="flex flex-wrap gap-2">{[['all','全部'],['person','人物'],['event','事件'],['topic','专题']].map(([value,label]) => <button key={value} aria-pressed={kind === value} onClick={() => update(q,value)} className={`px-5 py-2 rounded-full text-sm ${kind === value ? 'bg-teal-800 text-white' : 'bg-white border border-stone-200'}`}>{label}</button>)}</div>
    {pending ? <p role="status">正在搜索…</p> : <LoadState {...result} />}
    {!pending && !result.error && result.data && <>
      <p className="text-sm text-slate-500">已加载 {result.data.items.length} 条结果{q && ` · “${q}”`}</p>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">{result.data.items.map(n => n.type === 'topic' ? <Link className="reading-card" to={`/topics/${n.slug}`} key={n.id}><p className="eyebrow">专题</p><h2 className="text-xl font-semibold mt-2">{n.title}</h2><p className="mt-3 text-sm leading-7 text-slate-600">{n.description}</p></Link> : <EntryCard node={n} key={n.id} />)}</div>
      {result.data.items.length === 0 && <p className="py-12 text-center text-slate-500">暂时没有匹配的条目，试试别名或更短的关键词。</p>}
      <InfiniteScroll {...result} count={result.data.items.length} disabled={pending} label="搜索结果"/>
    </>}
  </div>;
}
