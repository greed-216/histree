import { relationshipPresentation } from "../lib/graph";
import { entryTitle, entryPath, safeUrl } from "../lib/reading";
import { Link, useParams } from "react-router-dom";
import type { GraphResponse, Topic, Event } from "@histree/shared-types";
import { useResource } from "../hooks/useResource";
import { Evidence, LoadState, Timeline } from "../components/Reading";
import {
  edgeTypeLabel,
  formatDisplayRange,
  referenceTypeLabel,
} from "../lib/content";
export function EntryPage() {
  const { id } = useParams();
  const graph = useResource<GraphResponse>(`/graph/${id}`);
  const topics = useResource<Topic[]>("/topics");
  if (graph.loading || graph.error) return <LoadState {...graph} />;
  if (!graph.data) return null;
  const { center: node, nodes, edges } = graph.data;
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
        {topics.data
          ?.filter((t) => t.sections.some((s) => s.node_ids.includes(node.id)))
          .map((t) => (
            <Link key={t.id} to={`/topics/${t.slug}`}>
              专题：{t.title}
            </Link>
          ))}
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
                  formatDisplayRange(node.birth_year, node.death_year),
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
          <section id="overview" className="scroll-mt-24">
            <h2 className="reading-heading">概述</h2>
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
                      <details className="mt-4 text-sm">
                        <summary className="cursor-pointer text-teal-700">
                          查看这条关系的依据
                        </summary>
                        <div className="mt-4">
                          <Evidence subject={edge.subject_table} id={edge.id} />
                        </div>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
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
