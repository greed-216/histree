import type {
  ClaimSubject,
  Event,
  EvidenceClaim,
  PageResult,
} from "@histree/shared-types";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { formatDisplayRange } from "../lib/content";
import { splitEvidenceNote } from "../lib/evidence";
import type { Entry } from "../lib/reading";
import { entryPath, entryTitle } from "../lib/reading";
import {
  sourceCitation,
  sourceReadingPath,
  sourceTitle,
} from "../lib/source-reading";
import { FeedbackButton } from "./FeedbackButton";
import { InfiniteScroll } from "./InfiniteScroll";
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
export interface EvidenceSummary {
  id: string;
  count: number;
  hasMore: boolean;
  loading: boolean;
  error?: string;
  sources: string[];
}

export function Evidence({
  subject,
  id,
  onSummary,
}: {
  subject: ClaimSubject;
  id: string;
  onSummary?: (summary: EvidenceSummary) => void;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const pinned = /^#claim-[0-9a-f-]{36}$/i.test(location.hash)
    ? location.hash.slice(7)
    : "";
  const params = new URLSearchParams({ subject, subject_id: id });
  if (pinned) params.set("claim", pinned);
  const result = useInfiniteResource<PageResult<EvidenceClaim>>(
    `/catalog/fact_claim?${params}`,
  );
  useEffect(() => {
    if (!onSummary) return;
    const sources = [
      ...new Set(
        (result.data?.items ?? []).flatMap((claim) => {
          if (!claim.source?.title) return [];
          const [book, ...parts] = claim.source.title.split("·");
          const volume = /卷(?:第)?[〇零一二三四五六七八九十百千\d]+/.exec(
            claim.citation || "",
          )?.[0];
          const location = parts.slice(0, 2).join("·") || volume;
          return [
            `《${book.replace(/[《》]/g, "")}》${location ? ` · ${location}` : ""}`,
          ];
        }),
      ),
    ];
    onSummary({
      id,
      count: result.data?.items.length ?? 0,
      hasMore: result.hasMore,
      loading: result.loading,
      error: result.error,
      sources,
    });
  }, [
    id,
    onSummary,
    result.data,
    result.hasMore,
    result.loading,
    result.error,
  ]);
  return (
    <div className="space-y-4">
      <LoadState {...result} />
      {result.data?.items.length === 0 && (
        <p className="text-sm text-slate-500">这部分的具体出处尚待整理。</p>
      )}
      {result.data?.items.map((claim) => (
        <EvidenceCard key={claim.id} claim={claim} />
      ))}
      {pinned ? (
        <button
          className="text-sm underline"
          onClick={() => {
            navigate(
              {
                pathname: location.pathname,
                search: location.search,
                hash: "",
              },
              { replace: true },
            );
          }}
        >
          查看全部依据
        </button>
      ) : (
        <InfiniteScroll
          {...result}
          count={result.data?.items.length}
          label="史料依据"
        />
      )}
    </div>
  );
}
export function EvidenceCard({ claim }: { claim: EvidenceClaim }) {
  const { quote, review } = claim.evidence ?? splitEvidenceNote(claim.note);
  const anchor = `claim-${claim.id}`;
  const selected = window.location.hash === `#${anchor}`;
  useEffect(() => {
    if (selected)
      document.getElementById(anchor)?.scrollIntoView({ block: "start" });
  }, [anchor, selected]);
  return (
    <article
      id={anchor}
      className="border-l-2 border-teal-600 pl-4 py-2 scroll-mt-28"
    >
      <p className="leading-7 font-medium">{claim.claim_text}</p>
      <p className="text-sm text-slate-600 mt-2">
        {claim.source ? (
          <Link
            className="text-teal-700 underline"
            to={`/sources/${claim.source.id}`}
          >
            《{sourceTitle(claim.source.title).replace(/[《》]/g, "")}》
          </Link>
        ) : (
          "来源待补充"
        )}
        {claim.source?.author && ` · ${claim.source.author}`} ·{" "}
        {sourceCitation(claim.citation) || "定位待补充"}
      </p>
      {review && (
        <details className="text-sm text-slate-500 mt-3 leading-6">
          <summary className="cursor-pointer">补充说明</summary>
          <p className="mt-2">{review}</p>
        </details>
      )}
      {quote && (
        <details
          open={selected || undefined}
          className="mt-3 rounded-lg bg-stone-100 p-3"
        >
          <summary className="cursor-pointer text-sm text-teal-800">
            查看所引原文
          </summary>
          <blockquote className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {quote}
          </blockquote>
        </details>
      )}
      <div className="flex flex-wrap gap-4 text-sm text-teal-700 mt-3">
        {claim.source && (
          <Link
            className="underline"
            to={sourceReadingPath(claim.source.id, claim.id)}
          >
            阅读原文 →
          </Link>
        )}
        <FeedbackButton
          claimId={claim.id}
          sourceId={claim.source?.id}
          context={claim.claim_text}
        />
      </div>
    </article>
  );
}
export function Timeline({
  events,
  condensed = false,
  roles = {},
}: {
  events: Event[];
  condensed?: boolean;
  roles?: Record<string, string>;
}) {
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
          {condensed && roles[event.id] && roles[event.id] !== "参与" && (
            <p className="person-event-role">在这件事中 · {roles[event.id]}</p>
          )}
          {condensed &&
            event.description &&
            event.description
              .split(/\r?\n\s*\r?\n/)[0]
              .replace(/[，。；、：\s]/g, "") !==
              event.title.replace(/[，。；、：\s]/g, "") && (
              <p className="person-event-excerpt">
                {event.description.split(/\r?\n\s*\r?\n/)[0].slice(0, 160)}
                {event.description.split(/\r?\n\s*\r?\n/)[0].length > 160
                  ? "…"
                  : ""}
              </p>
            )}
          {!condensed &&
            event.phases?.map((phase, index) => (
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

export function LazyEvidence({
  subject,
  id,
}: {
  subject: ClaimSubject;
  id: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <details
      className="mt-4 text-sm"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary className="cursor-pointer text-teal-700">
        查看这条关系的依据
      </summary>
      {open && (
        <div className="mt-4">
          <Evidence subject={subject} id={id} />
        </div>
      )}
    </details>
  );
}
