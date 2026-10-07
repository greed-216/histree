import { GuideCards } from './GuidePage';
import { MAPS_ENABLED } from '../lib/features';
import { Link } from "react-router-dom";
import type { TopicSummary, PageResult } from "@histree/shared-types";
import { InfiniteScroll } from '../components/InfiniteScroll';
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { LoadState } from "../components/Reading";
export function ExplorePage() {
  const topics = useInfiniteResource<PageResult<TopicSummary>>("/catalog/topic");
  return (
    <div className="space-y-12 pb-12">
      <section className="reading-hero relative overflow-hidden rounded-3xl px-7 py-12 md:px-14 md:py-20">
        <div className="relative z-10 max-w-2xl">
          <p className="eyebrow text-teal-200!">HISTREE / 历史之树</p>
          <h1 className="mt-6 text-4xl md:text-6xl leading-tight font-serif">
            从一个问题，
            <br />
            走进一段历史。
          </h1>
          <p className="mt-6 text-teal-50/80 leading-8 max-w-lg">
            读人物的选择，看事件的脉络。沿着关系探索，在史料中寻找依据。
          </p>
          <form
            action={`${import.meta.env.BASE_URL}search`}
            className="mt-8 flex gap-2 max-w-lg"
          >
            <label htmlFor="home-search" className="sr-only">
              搜索历史人物、事件或专题
            </label>
            <input
              id="home-search"
              name="q"
              placeholder="搜索人物、事件、专题…"
              className="min-w-0 flex-1 bg-white text-slate-800 rounded-xl px-4 py-3"
            />
            <button className="rounded-xl px-5 py-3 bg-amber-100 text-stone-900 font-medium">
              搜索
            </button>
          </form>
        </div>
        <div
          aria-hidden="true"
          className="absolute -right-12 -bottom-24 text-[280px] font-serif text-white/5 select-none"
        >
          史
        </div>
      </section>
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
          <p className="text-slate-500">专题资料正在整理，审核完成后将在这里发布。</p>
        )}
        <InfiniteScroll {...topics} count={topics.data?.items.length} label="专题"/>
      </section>
      <section className={`grid sm:grid-cols-2 ${MAPS_ENABLED ? 'lg:grid-cols-4' : 'lg:grid-cols-3'} gap-6 border-t border-stone-200 pt-8`}>
        {[
          ["01", "读懂人物", "从生平、选择与关系理解人物。", "/people"],
          ["02", "梳理事件", "把事件放回时间与参与者之中。", "/events"],
          ["03", "关系图谱", "展开人物与事件的关系，点击节点继续探索。", "/graph"],
          ...(MAPS_ENABLED ? [["04", "历史地图", "对照古地名与时间，查看事件定位进度。", "/map"]] : []),
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
