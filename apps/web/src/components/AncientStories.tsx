import type { Event, PageResult } from "@histree/shared-types";
import { Link } from "react-router-dom";
import type { useResource } from "../hooks/useResource";
import { ancientStoryChapter, ancientStoryEvents, ancientStorySource } from "../lib/ancientStories";
import type { AncientChapter } from "../lib/historyScroll";
import { LoadState } from "./Reading";

type StoriesResult = ReturnType<typeof useResource<PageResult<Event>>>;
type Props = { chapter: AncientChapter; result: StoriesResult };

export function AncientStoriesPreview({ chapter, result }: Props) {
  const stories = ancientStoryEvents(chapter.id, result.data?.items);
  return (
    <>
      <p className="timeline-era-intro">{ancientStoryChapter(chapter.id)?.intro}</p>
      <LoadState {...result} />
      <ol className="timeline-era-preview-stories">
        {stories.slice(0, 3).map((story) => (
          <li key={story.event.id}>
            <span>{story.time_label}</span>
            <Link to={`/events/${story.event.id}`}>{story.event.title} ↗</Link>
          </li>
        ))}
      </ol>
      {!result.loading && !result.error && !stories.length && (
        <p>这一时代暂无可显示的重点史事。</p>
      )}
    </>
  );
}

export function AncientStoriesReading({ chapter, result }: Props) {
  const stories = ancientStoryEvents(chapter.id, result.data?.items);
  return (
    <section id="timeline-era-stories" className="timeline-era-reading min-h-[420px]" aria-label="时代史事" aria-busy={result.loading}>
      <div className="flex flex-wrap justify-between gap-3 mb-4">
        <h2 className="reading-heading mb-0">这一时期发生了什么</h2>
        <span className="text-sm text-stone-500">{chapter.label} · 重点史事</span>
      </div>
      <p className="timeline-note">按叙事先后选读，顺序不代表确切年代。</p>
      {chapter.id === "five-emperors" && <p className="timeline-note">据《史记》传世文献叙事选读。</p>}
      <LoadState {...result} />
      {!result.loading && !result.error && !stories.length && (
        <p className="reading-card">这一时代暂无可显示的重点史事。</p>
      )}
      <ol className="timeline-era-stories">
        {stories.map((story, index) => (
          <li key={story.event.id}>
            <span className="timeline-era-story-number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
            <article className="reading-card timeline-era-story">
              <p className="eyebrow">{story.time_label}</p>
              <h3><Link to={`/events/${story.event.id}`}>{story.event.title}</Link></h3>
              <p className="timeline-era-story-description">{story.event.description}</p>
              <div className="timeline-era-story-links">
                <Link to={`/events/${story.event.id}`}>阅读全文与出处 →</Link>
                <Link to={ancientStorySource(story)}>{story.source.label}原文 ↗</Link>
              </div>
            </article>
          </li>
        ))}
      </ol>
      <p className="timeline-note">{chapter.id === "western-zhou-early" ? "往后进入共和元年（前841年），画卷开始按年展开。" : "继续向右浏览，可进入下一个时代。"}</p>
    </section>
  );
}
