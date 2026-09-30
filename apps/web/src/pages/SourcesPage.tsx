import { Link, useParams } from 'react-router-dom';
import type { Source, EvidenceClaim, ClaimSubject } from '@histree/shared-types';
import { useInfiniteResource, uniqueRows } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { Evidence, EvidenceCard, LoadState } from '../components/Reading';
import { safeUrl } from '../lib/reading';
type SourceClaims = { source: Source; claims: EvidenceClaim[]; count: number };
const sourcePages = {
  merge: (before: SourceClaims, next: SourceClaims) => ({ ...next, claims: uniqueRows([...before.claims, ...next.claims]) }),
  hasMore: (data: SourceClaims, page: number) => (page + 1) * 50 < data.count,
};
export function SourcePage() {
  const { id } = useParams();
  const result = useInfiniteResource<SourceClaims>(`/sources/${id}`, false, sourcePages);
  const data = result.data;
  return <div className="max-w-3xl mx-auto space-y-6">
    <Link to="/" className="text-teal-700">← 专题探索</Link><LoadState {...result} />
    {data && <>
      <header><p className="eyebrow">史料与引用索引</p><h1 className="text-3xl font-semibold mt-2">{data.source.title}</h1>
        <p className="mt-3">{data.source.author} · {data.source.edition}</p>
        <p className="mt-3 text-slate-600 leading-7">{data.source.note}</p>
        {safeUrl(data.source.url) && !data.source.url?.includes('isyd.net') && <a className="text-teal-700 underline" href={safeUrl(data.source.url)} target="_blank" rel="noreferrer">查看参考原文 ↗</a>}
      </header>
      <h2 className="text-xl font-semibold">本网站引用此来源的说法（{data.count} 条）</h2>
      <p className="text-sm text-slate-500">点击固定链接可返回对应条目的证据；原文中的异体字、缺字代码和不同记载保留供核对。</p>
      {data.claims.map(c => <div key={c.id} className="space-y-2">
        {(c.subject_table === 'person' || c.subject_table === 'event') && <Link className="text-teal-700 text-sm" to={`/${c.subject_table === 'person' ? 'people' : 'events'}/${c.subject_id}`}>查看对应{c.subject_table === 'person' ? '人物' : '事件'} →</Link>}
        <EvidenceCard claim={c} />
      </div>)}
      {data.claims.length === 0 && <p>暂无已发布引用。</p>}
      <InfiniteScroll {...result} count={data.claims.length} label="来源引用"/>
    </>}
  </div>;
}
export function EvidencePage() {
  const { subject, id } = useParams();
  if (!id || !/^[0-9a-f-]{36}$/i.test(id) || !['person','event','person_relationship','person_event','event_causality'].includes(subject || '')) return <p>无效的引用地址。</p>;
  return <div className="max-w-3xl mx-auto space-y-6">
    <Link className="text-teal-700" to={subject === 'person' ? `/people/${id}` : subject === 'event' ? `/events/${id}` : '/graph'}>← {subject === 'person' || subject === 'event' ? '返回条目' : '返回图谱'}</Link>
    <h1 className="text-3xl font-semibold">原文与出处</h1>
    <p className="text-slate-500">每条说法保留独立引用编号；有异议时可附原文提交勘误。</p>
    <Evidence subject={subject as ClaimSubject} id={id} />
  </div>;
}
