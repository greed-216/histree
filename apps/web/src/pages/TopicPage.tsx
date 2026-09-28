import { Link, useParams } from "react-router-dom";
import type { Topic, Person, Event } from "@histree/shared-types";
import { useResource } from "../hooks/useResource";
import { EntryCard, LoadState } from "../components/Reading";
import { TopicExplorer } from "../components/TopicExplorer";
export function TopicPage() {
  const { slug } = useParams();
  const topic = useResource<Topic>(`/topics/${slug}`);
  const people = useResource<Person[]>("/people");
  const events = useResource<Event[]>("/event");
  if (topic.loading || topic.error) return <LoadState {...topic} />;
  if (!topic.data) return null;
  const data = topic.data;
  const nodes = [...(people.data ?? []), ...(events.data ?? [])];
  const ids = new Set(data.sections.flatMap((s) => s.node_ids));
  return (
    <div className="space-y-10 pb-12">
      <Link to="/" className="text-sm text-teal-700">
        ← 专题探索
      </Link>
      <header className="max-w-3xl">
        <p className="eyebrow mt-6">专题阅读 / {data.sections.length} 个章节</p>
        <h1 className="font-serif text-4xl md:text-5xl mt-4">{data.title}</h1>
        <p className="text-lg leading-8 text-slate-600 mt-6">
          {data.description}
        </p>
      </header>
      {events.data && <TopicExplorer key={data.id} events={[...ids].flatMap(id => events.data!.filter(e => e.id === id))} people={people.data ?? []} />}
      <div className="grid lg:grid-cols-[1fr_260px] gap-12">
        <div className="space-y-12">
          <LoadState {...people} />
          <LoadState {...events} />
          {data.sections.map((section, index) => (
            <section
              id={`chapter-${index}`}
              className="scroll-mt-28"
              key={index}
            >
              <p className="eyebrow">
                {String(index + 1).padStart(2, "0")} / 阅读线索
              </p>
              <h2 className="font-serif text-2xl mt-2">{section.heading}</h2>
              <p className="leading-8 text-slate-600 whitespace-pre-line mt-4">
                {section.body}
              </p>
              <div className="grid sm:grid-cols-2 gap-4 mt-6">
                {section.node_ids.map((id) => {
                  const node = nodes.find((n) => n.id === id);
                  return node ? <EntryCard key={id} node={node} /> : null;
                })}
              </div>
              {!people.loading &&
                !events.loading &&
                !people.error &&
                !events.error &&
                section.node_ids.some(
                  (id) => !nodes.some((n) => n.id === id),
                ) && (
                  <p className="text-sm text-slate-500 mt-3">
                    部分关联条目正在修订，发布后即可阅读。
                  </p>
                )}
            </section>
          ))}
        </div>
        <aside className="space-y-8">
          <nav className="reading-card">
            <p className="eyebrow mb-4">阅读目录</p>
            {data.sections.map((s, i) => (
              <a
                href={`#chapter-${i}`}
                key={i}
                className="block py-2 text-sm hover:text-teal-700"
              >
                {i + 1}. {s.heading}
              </a>
            ))}
          </nav>

        </aside>
      </div>
    </div>
  );
}
