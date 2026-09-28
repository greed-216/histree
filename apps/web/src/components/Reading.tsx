import { Link } from "react-router-dom";
import type { Event, EvidenceClaim, ClaimSubject } from "@histree/shared-types";
import { formatDisplayRange } from "../lib/content";
import { useResource } from "../hooks/useResource";
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
  const result = useResource<EvidenceClaim[]>(`/evidence/${subject}/${id}`);
  return (
    <div className="space-y-4">
      <LoadState {...result} />
      {result.data?.length === 0 && (
        <p className="text-sm text-slate-500">这部分的具体出处尚待整理。</p>
      )}
      {result.data?.map((claim) => (
        <div key={claim.id} className="border-l-2 border-teal-600 pl-4 py-1">
          <p className="leading-7">{claim.claim_text}</p>
          <p className="text-sm text-slate-600 mt-2">
            {claim.source ? (
              <>
                《{claim.source.title}》
                {claim.source.author ? ` · ${claim.source.author}` : ""}
              </>
            ) : (
              "来源待补充"
            )}{" "}
            · {claim.citation || "定位待补充"}
          </p>
          {claim.source?.edition && (
            <p className="text-xs text-slate-500 mt-1">
              版本：{claim.source.edition}
            </p>
          )}
          {claim.note && (
            <p className="text-sm text-slate-500 mt-2">{claim.note}</p>
          )}
          {safeUrl(claim.source?.url) && (
            <a
              className="text-sm text-teal-700 underline"
              href={safeUrl(claim.source?.url)}
              target="_blank"
              rel="noreferrer"
            >
              阅读来源 ↗
            </a>
          )}
        </div>
      ))}
    </div>
  );
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
