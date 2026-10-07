import { hasGuideForNode } from '../lib/historyGuides';
import { relationshipPresentation } from "../lib/graph";
import { entryTitle, entryPath, safeUrl } from "../lib/reading";
import { Link, useParams } from "react-router-dom";
import type { EntryContext, TopicSummary, PageResult, Event } from "@histree/shared-types";
import { useInfiniteResource, uniqueRows } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { Evidence, LazyEvidence, LoadState, Timeline } from "../components/Reading";
import {
  edgeTypeLabel,
  formatDisplayRange,
  referenceTypeLabel,
} from "../lib/content";
const contextPages = {
  merge: (before: EntryContext, next: EntryContext): EntryContext => {
    const edges = new Map([...before.edges, ...next.edges].map(e => [e.id ?? `${e.subject_table}:${e.source}:${e.target}:${e.type}`, e]));
    return { ...next, nodes: uniqueRows([...before.nodes, ...next.nodes]), edges: [...edges.values()] };
  },
};
export function EntryPage() {
  const { id } = useParams();
  const graph = useInfiniteResource<EntryContext>(`/entry-context/${id}`, false, contextPages);
  const topics = useInfiniteResource<PageResult<TopicSummary>>(`/catalog/topic?node=${id}`);
  if (graph.loading || graph.error) return <LoadState {...graph} />;
  if (!graph.data) return null;
  const { center: node, nodes, edges } = graph.data;
  const hasZhouGuide = node.type === 'person' && node.id === '697c1a4f-b373-5a78-8b47-330fe349a424';
  const related = edges.filter(
    (e) => e.source === node.id || e.target === node.id,
  );
  const events = nodes.filter((n): n is Event => n.type === "event");
  return (
    <article className="pb-12">
      <nav className="text-sm text-teal-700 flex flex-wrap gap-4 mb-8">
        <Link to={node.type === "person" ? "/people" : "/events"}>
          ← {node.type === "person" ? "历史人物" : "历史事件"}
        </Link>
        {hasGuideForNode(node.id) && <Link to="/learn/later-zhou">后周导读 →</Link>}
        {topics.data?.items.map((t) => (
            <Link key={t.id} to={`/topics/${t.slug}`}>
              专题：{t.title}
            </Link>
          ))}
        {(topics.hasMore || (topics.data?.items.length ?? 0) > 20) && <InfiniteScroll {...topics} count={topics.data?.items.length} label="关联专题"/>}
      </nav>
      <header className="border-b border-stone-200 pb-9 mb-9 flex items-start gap-6">
        <div className="flex-1">
          <p className="eyebrow">
            {node.type === "person"
              ? `${node.era || "历史"} / 人物`
              : `${node.dynasty || "历史"} / 事件`}
          </p>
          <h1 className="font-serif text-4xl md:text-5xl mt-4">
            {entryTitle(node)}
          </h1>
          <p className="mt-4 text-slate-500">
            {node.type === "person"
              ? [
                  node.faction,
                  node.native_place,
                  hasZhouGuide && node.death_year == null ? '生年待补 · 959年去世' : formatDisplayRange(node.birth_year, node.death_year),
                ]
                  .filter(Boolean)
                  .join(" · ")
              : `${formatDisplayRange(node.start_year, node.end_year)}${node.location_name ? ` · ${node.location_name}` : ""}`}
          </p>
          {node.type === "person" && node.aliases?.length ? (
            <p className="text-sm text-slate-500 mt-2">
              别名：{node.aliases.join("、")}
            </p>
          ) : null}
          <Link to={`/ask?kind=${node.type}&id=${node.id}`} className="inline-block mt-4 text-sm text-teal-800 underline">围绕此条目问史料 →</Link>
          <div className="flex flex-wrap gap-2 mt-5">
            {node.tags?.map((tag) => (
              <Link
                key={tag}
                to={`/search?q=${encodeURIComponent(tag)}`}
                className="text-xs bg-stone-100 text-stone-600 px-3 py-1 rounded-full"
              >
                {tag}
              </Link>
            ))}
          </div>
        </div>
        {node.image_url && (
          <img
            src={node.image_url}
            alt={entryTitle(node)}
            className="w-20 h-24 md:w-32 md:h-40 rounded-2xl object-cover"
          />
        )}
      </header>
      <div className="grid lg:grid-cols-[minmax(0,1fr)_280px] gap-12">
        <div className="space-y-10 min-w-0">
          {hasZhouGuide && <section className="guide-prose guide-conclusion">
            <p className="eyebrow">生平导读 · 后周世宗</p><h2>从继承者到后周君主</h2>
            <p>柴荣在954年即位，经历高平之战，随后整顿军队，处理铸钱、寺院和田租等事务。后周在秦凤和淮南方向取得进展，959年北征后，柴荣南返并去世。宗训继位。</p>
            <Link className="text-teal-800 underline" to="/learn/later-zhou">沿六章阅读相关史事与出处 →</Link>
          </section>}
          <section id="overview" className="scroll-mt-24">
            <h2 className="reading-heading">{hasZhouGuide ? "早年身份与史料差异" : "概述"}</h2>
            <p className="reading-prose">
              {node.description || "概述正在整理。"}
            </p>
          </section>
          {node.type === "person" && node.biography && (
            <section>
              <h2 className="reading-heading">生平</h2>
              <p className="reading-prose">{node.biography}</p>
            </section>
          )}
          {node.type === "person" && node.historical_evaluation && (
            <section>
              <h2 className="reading-heading">历史评价</h2>
              <p className="reading-prose">{node.historical_evaluation}</p>
            </section>
          )}
          {node.type === "person" && !!node.family?.length && (
            <section>
              <h2 className="reading-heading">亲属记录</h2>
              {node.family.map((f, i) => (
                <p key={i} className="reading-prose">
                  {f.name} · {f.relation}
                  {f.note && `：${f.note}`}
                </p>
              ))}
            </section>
          )}
          <section id="chronology" className="scroll-mt-24">
            <h2 className="reading-heading">
              {node.type === "person" ? "相关事件时间线" : "事件时间脉络"}
            </h2>
            {events.length ? (
              <Timeline events={events} />
            ) : (
              <p className="text-slate-500 text-sm">相关事件正在整理。</p>
            )}
            <InfiniteScroll {...graph} count={events.length} label={node.type === "person" ? "人物相关事件" : "关联事件"} />
            {graph.hasMore && <p className="text-xs text-stone-500 mt-2">继续加载关联记录，时间线也会补充；当前列表还不是完整生平。</p>}
          </section>
          <section id="relationships" className="scroll-mt-24">
            <div className="flex justify-between items-center mb-5">
              <h2 className="reading-heading mb-0!">关系与上下文</h2>
              <Link to={`/graph/${node.id}`} className="text-sm text-teal-700">
                打开图谱 ↗
              </Link>
            </div>
            {related.length === 0 && (
              <p className="text-sm text-slate-500">关系资料正在整理。</p>
            )}
            <div className="space-y-4">
              {related.map((edge, index) => {
                const from = nodes.find((n) => n.id === edge.source);
                const to = nodes.find((n) => n.id === edge.target);
                if (!from || !to) return null;
                const presentation = relationshipPresentation(edge, nodes, edgeTypeLabel(edge.type));
                return (
                  <div key={edge.id ?? index} className="reading-card">
                    <div className="flex flex-wrap gap-2 items-center text-sm">
                      <Link
                        to={entryPath(from)}
                        className="font-semibold text-teal-800"
                      >
                        {entryTitle(from)}
                      </Link>
                      <span className="text-slate-500">
                        — {edgeTypeLabel(edge.type)} {presentation.symmetric ? "—" : "→"}
                      </span>
                      <Link
                        to={entryPath(to)}
                        className="font-semibold text-teal-800"
                      >
                        {entryTitle(to)}
                      </Link>
                    </div>
                    <p className="mt-2 text-sm font-medium">{relationshipPresentation(edge, nodes, edgeTypeLabel(edge.type), node.id).sentence}</p>
                    <p className="mt-3 text-sm leading-7 text-slate-600">
                      {edge.description || "关系说明正在整理。"}
                    </p>
                    {edge.id && edge.subject_table && (
                      <LazyEvidence subject={edge.subject_table} id={edge.id}/>
                    )}
                  </div>
                );
              })}
            </div>
            <InfiniteScroll {...graph} count={related.length} label="关系与上下文"/>
          </section>
          <section id="evidence" className="scroll-mt-24">
            <h2 className="reading-heading">陈述与出处</h2>
            <p className="text-sm text-slate-500 mb-5">
              以下资料对应具体陈述，便于核对叙述依据。
            </p>
            <Evidence subject={node.type} id={node.id} />
          </section>
          {!!node.references?.length && (
            <section>
              <h2 className="reading-heading">延伸参考</h2>
              <ul className="space-y-4">
                {node.references.map((r, i) => (
                  <li key={i} className="text-sm leading-7">
                    <span className="text-xs text-slate-500 mr-2">
                      {referenceTypeLabel(r.reference_type)}
                    </span>
                    {safeUrl(r.url) ? (
                      <a
                        href={safeUrl(r.url)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-teal-700 underline"
                      >
                        {r.title} ↗
                      </a>
                    ) : (
                      r.title
                    )}
                    {r.note && <p className="text-slate-500">{r.note}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
        <aside>
          <div className="reading-card lg:sticky lg:top-24">
            <p className="eyebrow mb-4">本页阅读</p>
            {[
              ["overview", "概述"],
              ["chronology", "时间脉络"],
              ["relationships", "关系与上下文"],
              ["evidence", "陈述与出处"],
            ].map(([anchor, label]) => (
              <a
                className="block text-sm py-2 hover:text-teal-700"
                key={anchor}
                href={`#${anchor}`}
              >
                {label}
              </a>
            ))}
            <Link
              to={`/graph/${node.id}`}
              className="block text-center bg-teal-800 text-white rounded-xl py-3 mt-6 text-sm"
            >
              在图谱中探索 →
            </Link>
          </div>
        </aside>
      </div>
    </article>
  );
}
