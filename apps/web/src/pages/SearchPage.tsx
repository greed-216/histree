import { Link, useSearchParams } from "react-router-dom";
import type { Person, Event, Topic } from "@histree/shared-types";
import { useResource } from "../hooks/useResource";
import { EntryCard, LoadState } from "../components/Reading";
export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const kind = params.get("kind") || "all";
  const people = useResource<Person[]>("/people");
  const events = useResource<Event[]>("/event");
  const topics = useResource<Topic[]>("/topics");
  const match = (values: unknown[]) =>
    values
      .flat()
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase()
      .includes(q.trim().toLocaleLowerCase());
  const nodes = [...(people.data ?? []), ...(events.data ?? [])].filter(
    (n) =>
      (kind === "all" || n.type === kind) &&
      match(
        n.type === "person"
          ? [n.name, n.aliases, n.era, n.faction, n.tags, n.description]
          : [n.title, n.dynasty, n.tags, n.description],
      ),
  );
  const foundTopics = (topics.data ?? []).filter(
    (t) =>
      (kind === "all" || kind === "topic") && match([t.title, t.description]),
  );
  const loading = people.loading || events.loading || topics.loading;
  const error = people.error || events.error || topics.error;
  return (
    <div className="space-y-7">
      <header>
        <p className="eyebrow">寻找历史线索</p>
        <h1 className="text-3xl font-serif mt-3">搜索与浏览</h1>
      </header>
      <label className="block">
        <span className="sr-only">搜索关键词</span>
        <input
          type="search"
          value={q}
          onChange={(e) =>
            setParams({ q: e.target.value, kind }, { replace: true })
          }
          placeholder="姓名、别名、事件、标签…"
          className="reading-input text-lg"
        />
      </label>
      <div className="flex flex-wrap gap-2">
        {[
          ["all", "全部"],
          ["person", "人物"],
          ["event", "事件"],
          ["topic", "专题"],
        ].map(([value, label]) => (
          <button
            key={value}
            aria-pressed={kind === value}
            onClick={() => setParams({ q, kind: value }, { replace: true })}
            className={`px-5 py-2 rounded-full text-sm ${kind === value ? "bg-teal-800 text-white" : "bg-white border border-stone-200"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <LoadState
        loading={loading}
        error={error}
        retry={() => {
          people.retry();
          events.retry();
          topics.retry();
        }}
      />
      {!loading && !error && (
        <>
          <p className="text-sm text-slate-500">
            {nodes.length + foundTopics.length} 条结果{q && ` · “${q}”`}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {foundTopics.map((t) => (
              <Link
                className="reading-card"
                to={`/topics/${t.slug}`}
                key={t.id}
              >
                <p className="eyebrow">专题</p>
                <h2 className="text-xl font-semibold mt-2">{t.title}</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  {t.description}
                </p>
              </Link>
            ))}
            {nodes.map((n) => (
              <EntryCard node={n} key={n.id} />
            ))}
          </div>
          {nodes.length + foundTopics.length === 0 && (
            <p className="py-12 text-center text-slate-500">
              暂时没有匹配的条目，试试别名或更短的关键词。
            </p>
          )}
        </>
      )}
    </div>
  );
}
