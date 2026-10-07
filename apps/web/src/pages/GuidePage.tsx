import { lazy, Suspense, useState } from "react";
import type { GraphResponse } from "@histree/shared-types";
import { Link, useParams } from "react-router-dom";
import data from "../data/history-guides.json";
const GraphView = lazy(() =>
  import("./GraphPage").then((m) => ({ default: m.GraphView })),
);
function yearLabel(years: number[]) {
  return years[0] === years[1] ? `${years[0]}年` : `${years[0]}—${years[1]}年`;
}
type GuideEvent = (typeof data.zhou.chapters)[number]["events"][number];
export function GuideCards() {
  return (
    <section className="guide-home" aria-labelledby="guide-heading">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow">先看全貌，再读细节</p>
          <h2 id="guide-heading" className="font-serif text-3xl mt-2">
            沿着主线，读懂一段历史
          </h2>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-5 mt-6">
        <Link to="/learn" className="guide-cover">
          <span className="eyebrow">时代总览 · 六个阶段</span>
          <h3>五代，为什么不断更替？</h3>
          <p>把唐末到后周放在同一条主线上，也看看中原之外正在发生什么。</p>
          <span>从全貌开始 →</span>
        </Link>
        <Link to="/learn/later-zhou" className="guide-cover guide-cover-zhou">
          <span className="eyebrow">连续导读 · 六个章节</span>
          <h3>读懂后周</h3>
          <p>从郭威建国到柴荣北征，沿着战争、治理和继承理解950—959年。</p>
          <span>开始第一段历史 →</span>
        </Link>
      </div>
    </section>
  );
}
function EventReadings({ events }: { events: GuideEvent[] }) {
  return (
    <ol className="guide-events">
      {events.map((event, index) => (
        <li key={event.id}>
          <span className="guide-event-number">
            {String(index + 1).padStart(2, "0")}
          </span>
          <div>
            <p className="eyebrow">
              {event.year == null ? "时间未定" : `${event.year}年`}
            </p>
            <h3 className="font-serif text-xl mt-2">
              <Link to={`/events/${event.id}`}>{event.title} ↗</Link>
            </h3>
            {event.description !== `${event.title}。` && (
              <p className="leading-7 text-stone-600 mt-3">
                {event.description}
              </p>
            )}
            <details className="guide-evidence">
              <summary>原文与出处 · {event.evidence.length} 条引用</summary>
              {event.evidence.map((ref) => (
                <div
                  key={ref.id}
                  className="mt-4 border-t border-stone-200 pt-4"
                >
                  <Link
                    to={`/sources/${ref.sourceId}`}
                    className="text-teal-800"
                  >
                    {ref.title}
                  </Link>
                  <p className="text-xs text-stone-500 mt-2 leading-6">
                    {ref.citation}
                  </p>
                  <blockquote className="leading-8 mt-2">
                    {ref.quote}
                  </blockquote>
                  <a
                    className="text-sm text-teal-800 underline"
                    href={ref.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    查看固定版本原文 ↗
                  </a>
                  <p className="text-xs text-stone-500 mt-2">
                    引用编号：{ref.id}
                  </p>
                </div>
              ))}
            </details>
          </div>
        </li>
      ))}
    </ol>
  );
}
export function GuidePage() {
  const { chapter } = useParams();
  const chapters = data.zhou.chapters;
  const index = chapter ? chapters.findIndex((c) => c.slug === chapter) : -1;
  if (chapter && index < 0)
    return (
      <div className="reading-card">
        <h1>没有找到这一章</h1>
        <Link to="/learn/later-zhou">返回后周目录 →</Link>
      </div>
    );
  const current = chapters[index];
  return (
    <div className="guide-page space-y-8 pb-10">
      <Link to="/learn" className="text-teal-800 text-sm">
        ← 五代历史总览
      </Link>
      <header className="guide-header">
        <p className="eyebrow">
          历史导读 ·{" "}
          {current ? `第 ${index + 1} / ${chapters.length} 章` : "950—959"}
        </p>
        <h1>{current ? current.title : data.zhou.title}</h1>
        <p>{current ? current.question : data.zhou.description}</p>
      </header>
      {!current ? (
        <>
          <p className="guide-coverage">{data.zhou.coverage}</p>
          <Link
            className="guide-primary-link"
            to={`/learn/later-zhou/${chapters[0].slug}`}
          >
            从第一章开始 →
          </Link>
          <p className="text-sm text-stone-500">
            章节兼顾时间与主题；治理一章跨年，与各场战争的进程并行。
          </p>
          <nav aria-label="后周导读目录" className="guide-chapters">
            {chapters.map((c, i) => (
              <Link key={c.slug} to={`/learn/later-zhou/${c.slug}`}>
                <span className="eyebrow">
                  {String(i + 1).padStart(2, "0")} · {yearLabel(c.years)}
                </span>
                <h2>{c.title}</h2>
                <p>{c.question}</p>
                <span className="text-teal-800">阅读这一章 →</span>
              </Link>
            ))}
          </nav>
        </>
      ) : (
        <div className="guide-layout">
          <article className="space-y-8">
            <section className="guide-prose">
              <p className="eyebrow">开始时的局势</p>
              <h2>先把问题放回当时</h2>
              <p>{current.context}</p>
            </section>
            <section>
              <p className="eyebrow">沿着史事阅读</p>
              <h2 className="font-serif text-2xl mt-2 mb-5">本章关键事件</h2>
              <EventReadings events={current.events} />
              <Link
                className="text-sm text-teal-800"
                to={`/timeline?year=${current.years[0]}`}
              >
                展开当年全部已录入事件 →
              </Link>
            </section>
            <section className="guide-prose guide-conclusion">
              <p className="eyebrow">读到这里，局势怎样变了？</p>
              <h2>本章小结</h2>
              <p>{current.change}</p>
              <p className="guide-question">
                带着这个问题继续读：{current.followup}
              </p>
              <p className="text-sm text-stone-500">
                导读是对以上史事的编辑概括；具体记载与异说请展开各事件的出处。
              </p>
            </section>
            <section className="reading-card">
              <p className="eyebrow">人物与上下文</p>
              <h2 className="font-serif text-2xl mt-2">这一章先认识谁？</h2>
              <div className="flex flex-wrap gap-3 mt-5">
                {current.people.map((p) => (
                  <Link
                    key={p.id}
                    className="guide-person"
                    to={`/people/${p.id}`}
                  >
                    {p.name} ↗
                  </Link>
                ))}
              </div>
              <ChapterGraph chapter={current} />
            </section>
            <nav aria-label="章节翻页" className="guide-pager">
              {index > 0 ? (
                <Link to={`/learn/later-zhou/${chapters[index - 1].slug}`}>
                  ← 上一章：{chapters[index - 1].title}
                </Link>
              ) : (
                <Link to="/learn/later-zhou">← 导读目录</Link>
              )}
              {index < chapters.length - 1 ? (
                <Link to={`/learn/later-zhou/${chapters[index + 1].slug}`}>
                  下一章：{chapters[index + 1].title} →
                </Link>
              ) : (
                <Link to="/learn">读完了，回到时代总览 →</Link>
              )}
            </nav>
          </article>
          <aside>
            <nav className="guide-side" aria-label="章节目录">
              <Link to="/learn/later-zhou" className="eyebrow">
                后周 · 阅读目录
              </Link>
              {chapters.map((c, i) => (
                <Link
                  aria-current={i === index ? "page" : undefined}
                  key={c.slug}
                  to={`/learn/later-zhou/${c.slug}`}
                >
                  {String(i + 1).padStart(2, "0")} {c.title}
                </Link>
              ))}
              <p className="text-xs text-stone-500 mt-4">
                本章涉及：{current.angles.join("、")}
              </p>
            </nav>
          </aside>
        </div>
      )}
    </div>
  );
}
export function HistoryOverviewPage() {
  return (
    <div className="guide-page space-y-8 pb-10">
      <header className="guide-header">
        <p className="eyebrow">历史导读 · 时代总览</p>
        <h1>{data.overview.title}</h1>
        <p>{data.overview.description}</p>
      </header>
      <p className="guide-coverage">{data.overview.coverage}</p>
      <section className="guide-prose">
        <h2>先分清“五代”和“十国”</h2>
        <p>
          这里的五代指中原先后出现的后梁、后唐、后晋、后汉、后周。“十国”帮助我们观察同时存在于其他地区的政权。阅读中原王朝的更替时，也要追踪各地延续的历史，避免把每次皇位更替误认为天下已经统一。
        </p>
        <p className="text-sm text-stone-500">
          下方按中原主线划分阶段；同一年可以同时属于新旧政权的交接。
        </p>
      </section>
      <nav aria-label="时代阶段" className="guide-stages">
        {data.overview.stages.map((s, i) => (
          <section key={s.slug}>
            <span className="guide-stage-number">
              {String(i + 1).padStart(2, "0")}
            </span>
            <div>
              <p className="eyebrow">{s.period}</p>
              <h2>{s.title}</h2>
              <p>{s.body}</p>
              <div className="flex flex-wrap gap-4 mt-4">
                <Link
                  className="text-teal-800"
                  to={
                    s.slug === "zhou"
                      ? "/learn/later-zhou"
                      : s.slug === "liang"
                        ? "/topics/later-liang-907-923"
                        : `/timeline?year=${s.years[0]}`
                  }
                >
                  {s.slug === "zhou"
                    ? "进入六章导读"
                    : s.slug === "liang"
                      ? "阅读后梁专题"
                      : "查看这一阶段的编年条目"}{" "}
                  →
                </Link>
                <details>
                  <summary className="text-sm text-stone-500 cursor-pointer">
                    关键史事与依据
                  </summary>
                  <EventReadings events={s.events} />
                </details>
              </div>
            </div>
          </section>
        ))}
      </nav>
      <section className="reading-card">
        <p className="eyebrow">从不同角度继续读</p>
        <h2 className="font-serif text-2xl mt-3">同一段历史，可以有不同入口</h2>
        <div className="grid md:grid-cols-3 gap-5 mt-5">
          <Link to="/learn/later-zhou">
            <h3 className="font-semibold">按时期读 →</h3>
            <p className="text-sm text-stone-600 mt-2">
              后周已有完整六章导读，先建立连续脉络。
            </p>
          </Link>
          <Link to="/search?q=南唐">
            <h3 className="font-semibold">按政权查 →</h3>
            <p className="text-sm text-stone-600 mt-2">
              查阅南唐相关条目，和同期中原史事对照；连续导读待补。
            </p>
          </Link>
          <Link to="/learn/later-zhou/huainan">
            <h3 className="font-semibold">带着问题读 →</h3>
            <p className="text-sm text-stone-600 mt-2">
              南唐为什么交出江北？从淮南战争这一章开始。
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
}

function ChapterGraph({
  chapter,
}: {
  chapter: (typeof data.zhou.chapters)[number];
}) {
  const [open, setOpen] = useState(false);
  return (
    <details className="mt-6" onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary className="cursor-pointer text-teal-800">
        展开{yearLabel(chapter.years)}人物与事件图谱
      </summary>
      {open && (
        <>
          <p className="text-sm text-stone-500 my-4">
            默认展示本章精选事件与人物的已录入关系；双击节点可进入更广的关系图。
          </p>
          <Suspense fallback={<p>正在加载图谱…</p>}>
            <GraphView
              initialGraph={chapter.graph as unknown as GraphResponse}
              initialId={chapter.people[0].id}
              initialMode="events"
              initialFrom={String(chapter.years[0])}
              initialTo={String(chapter.years[1])}
            />
          </Suspense>
        </>
      )}
    </details>
  );
}
