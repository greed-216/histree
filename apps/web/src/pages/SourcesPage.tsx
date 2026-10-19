import { Link, Navigate, useLocation, useParams, useSearchParams } from 'react-router-dom';
import type { Source, EvidenceClaim, ClaimSubject } from '@histree/shared-types';
import { useInfiniteResource, uniqueRows } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { Evidence, EvidenceCard, LoadState } from '../components/Reading';
import { useResource } from '../hooks/useResource';
import { SourceOriginal } from '../components/SourceOriginal';
import { splitEvidenceNote } from '../lib/evidence';
import { sourceReadingPath, sourceTitle } from '../lib/source-reading';
import { FeedbackButton } from '../components/FeedbackButton';
import { libraryPath } from '../lib/library';
import type { LibraryLocation } from '../lib/library';
type SourceClaims = { source: Source; claims: EvidenceClaim[]; count: number };
const sourcePages = {
  merge: (before: SourceClaims, next: SourceClaims) => ({ ...next, claims: uniqueRows([...before.claims, ...next.claims]) }),
  hasMore: (data: SourceClaims, page: number) => (page + 1) * 50 < data.count,
};
export function SourcePage() {
  const { id } = useParams();
  return id === 'read' ? <ResolveSource /> : <SourceReader key={id} id={id || ''} />;
}
function ResolveSource() {
  const [params] = useSearchParams();
  const archive = params.get('archive') || '';
  const result = useResource<{ source_id: string } | null>(`/source-texts/resolve?archive=${encodeURIComponent(archive)}`);
  if (result.data) return <Navigate replace to={sourceReadingPath(result.data.source_id, params.get('claim') || undefined)} />;
  return <div className="max-w-3xl mx-auto space-y-6"><Link className="text-teal-700" to="/">← 返回探索</Link><h1 className="text-3xl font-semibold">原文片段</h1><LoadState {...result}/>
    {!result.loading && !result.error && <p>此来源的原文片段尚未入库。</p>}
    <FeedbackButton label="提交反馈" />
  </div>;
}
function SourceReader({ id }: { id: string }) {
  const [params] = useSearchParams();
  const location = useLocation();
  const claimId = params.get('claim');
  const selected = useResource<{ items: EvidenceClaim[] }>(claimId && /^[0-9a-f-]{36}$/i.test(claimId)
    ? `/catalog/fact_claim?source=${id}&claim=${claimId}` : undefined);
  const result = useInfiniteResource<SourceClaims>(`/sources/${id}`, sourcePages);
  const destination = useResource<LibraryLocation | null>(`/sources/${id}/location`);
  const data = result.data;
  const title = data && sourceTitle(data.source.title);
  const claim = selected.data?.items.find(c => c.id === claimId && c.source_id === id);
  const quote = claim ? splitEvidenceNote(claim.note).quote : '';
  if (params.get('read') === '1' && destination.loading) return <LoadState {...destination} />;
  if (params.get('read') === '1' && destination.data) return <Navigate replace to={libraryPath(destination.data, claimId || undefined)} />;
  return <div className="max-w-3xl mx-auto space-y-6">
    <Link to="/" className="text-teal-700">← 首页</Link><LoadState {...result} />
    {data && <>
      <header><p className="eyebrow">史料原文与引用</p><h1 className="text-3xl font-semibold mt-2 break-words">{title}</h1>
        {data.source.author && <p className="mt-3 text-slate-600">{data.source.author}</p>}
      </header>
      <SourceOriginal id={id} archive={data.source.url} quote={quote} citation={claim?.citation || data.claims[0]?.citation} selected={location.hash === '#original'} selectionLoading={Boolean(claimId) && selected.loading} />
      {destination.data && <Link className="text-teal-700" to={libraryPath(destination.data, claimId || undefined)}>在书中连续阅读 →</Link>}
      <FeedbackButton sourceId={id} context={title} />
      <h2 className="text-xl font-semibold">本网站引用此来源的说法（{data.count} 条）</h2>
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
    <p className="text-slate-500">阅读原文与出处，发现问题可以直接提交勘误。</p>
    <Evidence subject={subject as ClaimSubject} id={id} />
  </div>;
}
