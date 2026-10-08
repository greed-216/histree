import { TimelineExplorer } from "../components/TimelineExplorer";
import { GuideCards } from "./GuidePage";
import { MAPS_ENABLED } from "../lib/features";
import { Link } from "react-router-dom";
import type { TopicSummary, PageResult } from "@histree/shared-types";
import { InfiniteScroll } from "../components/InfiniteScroll";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { LoadState } from "../components/Reading";
export function ExplorePage() {
  const topics =
    useInfiniteResource<PageResult<TopicSummary>>("/catalog/topic");
  return (
    <div className="home-explore space-y-8 pb-12">
      <section className="home-time-heading">
        <div>
          <p className="eyebrow">HISTREE / 历史之树</p>
          <h1>沿时间，走进历史</h1>
          <p>拖动画卷，发现史事；点击年份，再循着出处深入阅读。</p>
        </div>
        <form
          action={`${import.meta.env.BASE_URL}search`}
          className="home-time-search"
        >
          <label htmlFor="home-search" className="sr-only">
            搜索历史人物、事件或专题
          </label>
          <input
            id="home-search"
            name="q"
            placeholder="搜索人物、事件、专题…"
          />
          <button type="submit">搜索</button>
        </form>
      </section>
      <TimelineExplorer compact />
      <GuideCards />
      <section>
        <div className="flex items-end justify-between mb-6">
          <div>
            <p className="eyebrow">从这里开始</p>
            <h2 className="text-2xl font-serif mt-2">继续查阅专题</h2>
          </div>
          <Link to="/search" className="text-sm text-teal-700">
            全部条目 ↗
          </Link>
        </div>
        <LoadState {...topics} />
        <div className="grid md:grid-cols-2 gap-6">
          {topics.data?.items.map((topic, index) => (
            <Link
              to={`/topics/${topic.slug}`}
              key={topic.id}
              className="reading-card group relative overflow-hidden"
            >
              <span className="eyebrow">
                专题 {String(index + 1).padStart(2, "0")} ·{" "}
                {topic.section_count} 个阅读章节
              </span>
              <h3 className="font-serif text-3xl mt-5 group-hover:text-teal-700">
                {topic.title}
              </h3>
              <p className="text-slate-600 leading-8 mt-4">
                {topic.description}
              </p>
              <span className="inline-block mt-8 text-teal-700">
                开始阅读 →
              </span>
            </Link>
          ))}
        </div>
        {topics.data?.items.length === 0 && (
          <p className="text-slate-500">
            专题资料正在整理，审核完成后将在这里发布。
          </p>
        )}
        <InfiniteScroll
          {...topics}
          count={topics.data?.items.length}
          label="专题"
        />
      </section>
      <section
        className={`grid sm:grid-cols-2 ${MAPS_ENABLED ? "lg:grid-cols-4" : "lg:grid-cols-3"} gap-6 border-t border-stone-200 pt-8`}
      >
        {[
          ["01", "读懂人物", "从生平、选择与关系理解人物。", "/people"],
          ["02", "梳理事件", "把事件放回时间与参与者之中。", "/events"],
          [
            "03",
            "关系图谱",
            "展开人物与事件的关系，点击节点继续探索。",
            "/graph",
          ],
          ...(MAPS_ENABLED
            ? [
                [
                  "04",
                  "历史地图",
                  "对照古地名与时间，查看事件定位进度。",
                  "/map",
                ],
              ]
            : []),
        ].map(([number, title, body, path]) => (
          <Link key={number} to={path} className="p-2">
            <span className="eyebrow">{number}</span>
            <h3 className="text-lg font-semibold mt-3">{title} ↗</h3>
            <p className="text-sm text-slate-500 leading-7 mt-2">{body}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
