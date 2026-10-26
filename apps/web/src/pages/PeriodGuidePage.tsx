import type { Event, PageResult } from "@histree/shared-types";
import { Link, useParams } from "react-router-dom";
import { InfiniteScroll } from "../components/InfiniteScroll";
import { LazyEvidence, LoadState } from "../components/Reading";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { formatDisplayRange } from "../lib/content";
import { periodReadings } from "../lib/periodReadings";
export function PeriodGuidePage() {
  const { period } = useParams();
  const selected = periodReadings.find((p) => p.id === period);
  const result = useInfiniteResource<PageResult<Event>>(
    selected
      ? `/catalog/event?from=${selected.from_year}&to=${selected.to_year}&limit=12&dating=dated`
      : undefined,
  );
  if (!selected)
    return (
      <p className="reading-card">
        这一时期的阅读路径暂不存在。<Link to="/learn">返回导读</Link>
      </p>
    );
  return (
    <div className="guide-page space-y-8">
      <Link to="/learn" className="text-teal-800">
        ← 全部导读
      </Link>
      <header className="guide-header">
        <p className="eyebrow">按时期阅读 · 编年条目</p>
        <h1>{selected.label}</h1>
        <p>{formatDisplayRange(selected.from_year, selected.to_year)}</p>
      </header>
      <section className="reading-card">
        <h2 className="reading-heading">先看时间脉络</h2>
        <p className="leading-7">
          沿时间顺序阅读这一时期已经整理的史事；打开每条记录可核查原文、人物与相关关系。这里列出的是已录入条目，不代表全部历史记载或编辑精选。
        </p>
        <div className="flex flex-wrap gap-4 mt-4">
          <Link
            to={`/timeline?year=${selected.from_year}`}
            className="text-teal-800"
          >
            在画卷中浏览 →
          </Link>
          <Link to="/people" className="text-teal-800">
            查阅人物目录 →
          </Link>
          <Link to="/library" className="text-teal-800">
            按书阅读原文 →
          </Link>
        </div>
      </section>
      <section>
        <h2 className="reading-heading">沿着史事与出处阅读</h2>
        <LoadState {...result} />
        <ol className="space-y-5">
          {result.data?.items.map((event) => (
            <li key={event.id} className="reading-card">
              <p className="eyebrow">
                {formatDisplayRange(event.start_year, event.end_year)}
              </p>
              <h3 className="text-xl font-serif mt-2">
                <Link to={`/events/${event.id}`}>{event.title} →</Link>
              </h3>
              <p className="mt-3 leading-7">{event.description}</p>
              <LazyEvidence subject="event" id={event.id} />
            </li>
          ))}
        </ol>
        {result.data?.items.length === 0 && (
          <p className="reading-card">这一时期的史事选读尚待整理。</p>
        )}
        <InfiniteScroll
          {...result}
          count={result.data?.items.length}
          label="时期史事"
        />
      </section>
    </div>
  );
}
