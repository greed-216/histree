import { useEffect, useState } from "react";
import { splitEvidenceNote, evidencePath, correctionUrl } from "../lib/evidence";
import { Link, useLocation, useNavigate } from "react-router-dom";
import type { Event, EvidenceClaim, ClaimSubject, PageResult } from "@histree/shared-types";
import { formatDisplayRange } from "../lib/content";
import { InfiniteScroll } from './InfiniteScroll';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { entryTitle, entryPath, safeUrl } from "../lib/reading";
import type { Entry } from "../lib/reading";
export function LoadState({
  loading,
  error,
  retry,
}: {
  loading: boolean;
  error?: string;
  retry: () => void;
}) {
  if (loading)
    return (
      <p className="py-16 text-center text-slate-500" role="status">
        正在整理这段历史…
      </p>
    );
  if (error)
    return (
      <div
        role="alert"
        className="p-6 border border-rose-200 rounded-xl bg-rose-50"
      >
        <p>内容暂时无法加载，请稍后重试。</p>
        <button className="mt-3 underline" onClick={retry}>
          重新加载
        </button>
      </div>
    );
  return null;
}
export function EntryCard({ node }: { node: Entry }) {
  return (
    <Link to={entryPath(node)} className="reading-card block group">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center shrink-0 overflow-hidden text-lg text-stone-600">
          {node.image_url ? (
            <img
              src={node.image_url}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            entryTitle(node).slice(0, 1)
          )}
        </div>
        <div>
          <p className="eyebrow">
            {node.type === "person"
              ? node.era || "人物"
              : formatDisplayRange(node.start_year, node.end_year)}
          </p>
          <h3 className="text-xl font-semibold mt-1 group-hover:text-teal-700">
            {entryTitle(node)}
          </h3>
        </div>
      </div>
      <p className="mt-4 text-sm leading-7 text-slate-600 line-clamp-3">
        {node.description || "条目内容正在整理。"}
      </p>
      <span className="block mt-4 text-sm text-teal-700">阅读条目 ↗</span>
    </Link>
  );
}
export function Evidence({
  subject,
  id,
}: {
  subject: ClaimSubject;
  id: string;
}) {
  const location=useLocation();const navigate=useNavigate();
  const pinned=/^#claim-[0-9a-f-]{36}$/i.test(location.hash)?location.hash.slice(7):'';
  const params=new URLSearchParams({subject,subject_id:id});
  if(pinned)params.set('claim',pinned);
  const result = useInfiniteResource<PageResult<EvidenceClaim>>(`/catalog/fact_claim?${params}`);
  return (
    <div className="space-y-4">
      <LoadState {...result} />
      {result.data?.items.length === 0 && (
        <p className="text-sm text-slate-500">这部分的具体出处尚待整理。</p>
      )}
      {result.data?.items.map((claim) => <EvidenceCard key={claim.id} claim={claim} />)}
      {pinned?<button className="text-sm underline" onClick={()=>{navigate({pathname:location.pathname,search:location.search,hash:''},{replace:true});}}>查看全部依据</button>:<InfiniteScroll {...result} count={result.data?.items.length} label="史料依据"/>}
    </div>
  );
}
export function EvidenceCard({ claim }: { claim: EvidenceClaim }) {
  const { quote, review } = splitEvidenceNote(claim.note);
  const anchor = `claim-${claim.id}`;
  const path = evidencePath(claim);
  const permalink = `${window.location.origin}${import.meta.env.BASE_URL.replace(/\/$/, '')}${path}`;
  const selected = window.location.hash === `#${anchor}`;
  useEffect(() => {
    if (selected) document.getElementById(anchor)?.scrollIntoView({ block: 'start' });
  }, [anchor, selected]);
  return <article id={anchor} className="border-l-2 border-teal-600 pl-4 py-2 scroll-mt-28">
    <p className="leading-7 font-medium">{claim.claim_text}</p>
    <p className="text-sm text-slate-600 mt-2">
      {claim.source ? <Link className="text-teal-700 underline" to={`/sources/${claim.source.id}`}>《{claim.source.title}》</Link> : '来源待补充'}
      {claim.source?.author && ` · ${claim.source.author}`} · {claim.citation || '定位待补充'}
    </p>
    {claim.source?.edition && <p className="text-xs text-slate-500 mt-1">版本：{claim.source.edition}</p>}
    {review && <p className="text-sm text-slate-600 mt-3 leading-6">核对说明：{review}</p>}
    {quote && <details open={selected || undefined} className="mt-3 rounded-lg bg-stone-100 p-3">
      <summary className="cursor-pointer text-sm text-teal-800">查看所引原文</summary>
      <blockquote className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{quote}</blockquote>
    </details>}
    <div className="flex flex-wrap gap-4 text-sm text-teal-700 mt-3">
      <Link className="underline" to={path}>此条引用的固定链接</Link>
      {safeUrl(claim.source?.url) && !claim.source?.url?.includes('isyd.net') && <a className="underline" href={safeUrl(claim.source?.url)} target="_blank" rel="noreferrer">查看参考原文 ↗</a>}
      <a className="underline" href={correctionUrl(claim, permalink)} target="_blank" rel="noreferrer">提交勘误（GitHub）↗</a>
    </div>
    <p className="text-xs text-slate-400 mt-2 break-all">引用编号：{claim.id}</p>
  </article>;
}
export function Timeline({ events }: { events: Event[] }) {
  const sorted = [...events].sort(
    (a, b) => (a.start_year ?? Infinity) - (b.start_year ?? Infinity),
  );
  return (
    <ol className="ml-2 border-l border-stone-300 space-y-8">
      {sorted.map((event) => (
        <li key={event.id} className="pl-6 relative">
          <span className="absolute -left-1.5 top-2 w-3 h-3 rounded-full bg-teal-700 border-2 border-white" />
          <p className="eyebrow">
            {formatDisplayRange(event.start_year, event.end_year)}
          </p>
          <Link
            to={entryPath(event)}
            className="block text-lg font-semibold mt-1 hover:text-teal-700"
          >
            {event.title} ↗
          </Link>
          {event.phases?.map((phase, index) => (
            <div className="mt-3 text-sm leading-7" key={index}>
              <span className="text-slate-500">
                {formatDisplayRange(phase.start_year, phase.end_year)}
              </span>
              <p className="font-medium">{phase.title}</p>
              <p className="text-slate-600">{phase.description}</p>
            </div>
          ))}
        </li>
      ))}
    </ol>
  );
}

export function LazyEvidence({subject,id}:{subject:ClaimSubject;id:string}) {
 const [open,setOpen]=useState(false);
 return <details className="mt-4 text-sm" onToggle={e=>setOpen(e.currentTarget.open)}><summary className="cursor-pointer text-teal-700">查看这条关系的依据</summary>{open&&<div className="mt-4"><Evidence subject={subject} id={id}/></div>}</details>;
}
