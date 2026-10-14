import { hasGuideForNode } from '../lib/historyGuides';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { EntryAssistant } from '../components/EntryAssistant';
import '../styles/event-reading-context.css';
import { relationshipPresentation } from "../lib/graph";
import { entryTitle, entryPath, safeUrl } from "../lib/reading";
import { Link, useLocation, useParams } from "react-router-dom";
import type { EntryContext, TopicSummary, PageResult, Event } from "@histree/shared-types";
import { useInfiniteResource, uniqueRows } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { Evidence, LazyEvidence, LoadState, Timeline, type EvidenceSummary } from "../components/Reading";
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

function revealReadingSection(id: string) {
  const section = document.getElementById(id);
  if (section instanceof HTMLDetailsElement) section.open = true;
  section?.scrollIntoView({ block: 'start' });
}

function ReadingSection({ id, title, compact, children, action, preview }: { id: string; title: string; compact: boolean; children: ReactNode; action?: ReactNode; preview?: ReactNode }) {
  const location = useLocation();
  const disclosure = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const section = disclosure.current;
    if (!section) return;
    const reveal = () => {
      if (window.location.hash === `#${id}`) {
        section.open = true;
        section.scrollIntoView({ block: 'start' });
      }
    };
    reveal();
    window.addEventListener('hashchange', reveal);
    return () => window.removeEventListener('hashchange', reveal);
  }, [id, location.key, location.hash]);
  if (compact) return <details id={id} ref={disclosure} className="entry-reading-disclosure">
    <summary><span className="entry-disclosure-heading">{title}{preview && <small>{preview}</small>}</span><span className="entry-disclosure-action">展开查看</span></summary>
    <div>{action && <div className="mb-5">{action}</div>}{children}</div>
  </details>;
  return <section id={id} className="scroll-mt-24">{action ? <div className="flex justify-between items-center mb-5">
    <h2 className="reading-heading mb-0!">{title}</h2>{action}
  </div> : <h2 className="reading-heading">{title}</h2>}{children}</section>;
}

export function EntryPage() {
  const { id } = useParams();
  const article = useRef<HTMLElement>(null);
  const [evidenceSummary, setEvidenceSummary] = useState<EvidenceSummary | null>(null);
  const graph = useInfiniteResource<EntryContext>(`/entry-context/${id}`, contextPages);
  const topics = useInfiniteResource<PageResult<TopicSummary>>(`/catalog/topic?node=${id}`);
  if (graph.loading || graph.error) return <LoadState {...graph} />;
  if (!graph.data) return null;
  const { center: node, nodes, edges } = graph.data;
  const isEvent = node.type === 'event';
  const hasZhouGuide = node.type === 'person' && node.id === '697c1a4f-b373-5a78-8b47-330fe349a424';
  const related = edges.filter(
    (e) => e.source === node.id || e.target === node.id,
  );
  const people = nodes.filter(n => n.type === 'person' && related.some(edge => edge.source === n.id || edge.target === n.id));
  const sourceInfo = evidenceSummary?.id === node.id ? evidenceSummary : null;
  const events = nodes.filter((n): n is Event => n.type === "event");
  return (
    <article className={isEvent ? 'entry-reading-page pb-12' : 'pb-12'} ref={article}>
      <nav className="text-sm text-teal-700 flex flex-wrap gap-4 mb-8">
        <Link to={node.type === "person" ? "/people" : "/events"}>
          ← {node.type === "person" ? "历史人物" : "历史事件"}
        </Link>
        {hasGuideForNode(node.id) && <Link to="/learn/five-dynasties/later-zhou">后周导读 →</Link>}
        {topics.data?.items.map((t) => (
            <Link key={t.id} to={`/topics/${t.slug}`}>
              专题：{t.title}
            </Link>
          ))}
        {(topics.hasMore || (topics.data?.items.length ?? 0) > 20) && <InfiniteScroll {...topics} count={topics.data?.items.length} label="关联专题"/>}
      </nav>
      <header className="entry-hero border-b border-stone-200 pb-9 mb-9 flex items-start gap-6">
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
          {!isEvent && <Link to={`/ask?kind=${node.type}&id=${node.id}`} className="inline-block mt-4 text-sm text-teal-800 underline">围绕此条目问史料 →</Link>}
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
      {isEvent && <nav className="entry-reading-nav" aria-label="本页阅读">
        <a href="#overview">事件叙述</a><a href="#evidence" onClick={() => revealReadingSection('evidence')}>史料依据</a>
        <Link to={`/graph/${node.id}`}>图谱 ↗</Link>
      </nav>}
      <div className={isEvent ? 'entry-reading-layout' : 'grid lg:grid-cols-[minmax(0,1fr)_280px] gap-12'}>
        <div className="space-y-10 min-w-0">
          {hasZhouGuide && <section className="guide-prose guide-conclusion">
            <p className="eyebrow">生平导读 · 后周世宗</p><h2>从继承者到后周君主</h2>
            <p>柴荣在954年即位，经历高平之战，随后整顿军队，处理铸钱、寺院和田租等事务。后周在秦凤和淮南方向取得进展，959年北征后，柴荣南返并去世。宗训继位。</p>
            <Link className="text-teal-800 underline" to="/learn/five-dynasties/later-zhou">沿六章阅读相关史事与出处 →</Link>
          </section>}
          <section id="overview" className={isEvent ? 'event-narrative' : 'scroll-mt-24'} aria-label={isEvent ? '事件叙述' : undefined}>
            {!isEvent && <h2 className="reading-heading">{hasZhouGuide ? "早年身份与史料差异" : "概述"}</h2>}
            {isEvent ? (node.description || '事件说明正在整理。').split(/\r?\n\s*\r?\n/).filter(Boolean).map((paragraph, index) => <p key={index}>{paragraph}</p>) : <p className="reading-prose">{node.description || "概述正在整理。"}</p>}
          </section>
          {isEvent && people.length > 0 && <nav className="event-people" aria-label="相关人物">
            <span>相关人物</span>
            {people.slice(0, 10).map(person => <Link key={person.id} to={entryPath(person)}>{entryTitle(person)}</Link>)}
            {people.length > 10 && <a href="#relationships" onClick={() => revealReadingSection('relationships')}>更多人物 ↓</a>}
          </nav>}
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
          {!isEvent && <ReadingSection id="chronology" title={node.type === "person" ? "相关事件时间线" : "事件时间脉络"} compact={false}>
            {events.length ? (
              <Timeline events={events} />
            ) : (
              <p className="text-slate-500 text-sm">相关事件正在整理。</p>
            )}
            <InfiniteScroll {...graph} count={events.length} label={node.type === "person" ? "人物相关事件" : "关联事件"} />
            {graph.hasMore && <p className="text-xs text-stone-500 mt-2">继续加载关联记录，时间线也会补充；当前列表还不是完整生平。</p>}
          </ReadingSection>}
          {node.type === 'event' && Boolean(node.phases?.length) && <ReadingSection id="chronology" title="过程记录" compact>
            <ol className="event-phase-records">
              {node.phases?.map((phase, index) => <li key={index}>
                {(phase.start_year != null || phase.end_year != null) && formatDisplayRange(phase.start_year, phase.end_year) !== formatDisplayRange(node.start_year, node.end_year) && <p className="eyebrow">{formatDisplayRange(phase.start_year, phase.end_year)}</p>}
                <h3>{phase.title}</h3><p>{phase.description}</p>
              </li>)}
            </ol>
          </ReadingSection>}
          {(!isEvent || related.length > 0 || graph.hasMore) && <ReadingSection id="relationships" title={isEvent ? '相关人物与记录' : '关系与上下文'} compact={isEvent} action={<Link to={`/graph/${node.id}`} className="text-sm text-teal-700">打开图谱 ↗</Link>}>
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
          </ReadingSection>}
          <ReadingSection id="evidence" title={isEvent ? '史料依据' : '陈述与出处'} compact={isEvent} preview={isEvent && <>
            {!sourceInfo || sourceInfo.loading ? '正在读取出处…' : sourceInfo.error ? '出处暂时无法读取' : <>
              <span>{sourceInfo.count === 0 ? '具体出处尚待整理' : sourceInfo.hasMore ? `已加载 ${sourceInfo.count} 条引用，展开可继续查阅` : `${sourceInfo.count} 条引用`}</span>
              {sourceInfo.sources.length > 0 && <span className="entry-source-names">{sourceInfo.sources.slice(0, 2).join('；')}{sourceInfo.sources.length > 2 ? ' 等' : ''}</span>}
            </>}
          </>}>
            <p className="text-sm text-slate-500 mb-5">
              以下资料对应具体陈述，便于核对叙述依据。
            </p>
            <Evidence subject={node.type} id={node.id} onSummary={isEvent ? setEvidenceSummary : undefined} />
          </ReadingSection>
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
        {!isEvent && <aside>
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
        </aside>}
      </div>
      {node.type === 'event' && <EntryAssistant key={node.id} entryId={node.id} title={entryTitle(node)} article={article} headerOnMobile={isEvent} />}
    </article>
  );
}
