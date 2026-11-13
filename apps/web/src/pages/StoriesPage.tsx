import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { StoryArtwork } from "../components/StoryArtwork";
import { stories, storyBySlug, type IllustratedStory } from "../lib/stories";
import "../styles/stories.css";

export function StoriesPage() {
  return <div className="stories-page">
    <header className="stories-heading">
      <p className="stories-eyebrow">翻开一本小人书</p>
      <h1>说故事</h1>
      <p>翻几页，看一段有意思的旧时故事。</p>
    </header>
    <div className="stories-shelf">
      {stories.map((story) => <article className="story-card" key={story.slug}>
        <Link to={`/stories/${story.slug}`} className="story-card-cover" aria-label={`翻开《${story.title}》`}>
          <StoryArtwork image={story.image} panel={story.panels[0]} />
        </Link>
        <div className="story-card-copy">
          <p className="stories-eyebrow">{story.panels.length} 格连环画 · 约 {story.readingMinutes} 分钟</p>
          <h2><Link to={`/stories/${story.slug}`}>{story.title}</Link></h2>
          <p>{story.description}</p>
          <Link className="story-open" to={`/stories/${story.slug}`}>翻开故事 <span aria-hidden="true">→</span></Link>
        </div>
      </article>)}
    </div>
  </div>;
}

function StoryReader({ story }: { story: IllustratedStory }) {
  const [page, setPage] = useState(0);
  const heading = useRef<HTMLElement>(null);
  const touch = useRef<{ x: number; y: number } | null>(null);
  const count = story.panels.length;
  const total = count + 3;
  const panel = page >= 1 && page <= count ? story.panels[page - 1] : undefined;
  const last = page === total - 1;
  const chapter = page === 0 ? "introduction" : panel ? "comic" : last ? "meaning" : "afterword";
  const chapters = [
    { id: "introduction", label: "开场", page: 0 },
    { id: "comic", label: "连环画", page: 1 },
    { id: "afterword", label: "后记", page: count + 1 },
    { id: "meaning", label: "寓意", page: count + 2 },
  ];
  const nextLabel = page === 0 ? "翻开连环画 →" : page === count ? "看故事后记 →" : page === count + 1 ? "看故事寓意 →" : "下一格 →";
  const nextStory = stories.length > 1 ? stories[(stories.indexOf(story) + 1) % stories.length] : undefined;
  const move = useCallback((direction: number) => setPage((value) => Math.max(0, Math.min(total - 1, value + direction))), [total]);

  useLayoutEffect(() => {
    const top = heading.current?.getBoundingClientRect().top;
    const headerBottom = document.querySelector('.site-header')?.getBoundingClientRect().bottom ?? 0;
    if (top !== undefined && top < headerBottom + 12) window.scrollBy(0, top - headerBottom - 12);
  }, [page]);

  useEffect(() => {
    const previousTitle = document.title;
    document.title = `${story.title} · 说故事 · Histree`;
    return () => { document.title = previousTitle; };
  }, [story.title]);

  useEffect(() => {
    function keydown(event: KeyboardEvent) {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
        (event.target instanceof Element && event.target.closest("input,textarea,select,[contenteditable],dialog"))) return;
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        move(event.key === "ArrowRight" ? 1 : -1);
      }
    }
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [move]);

  return <div className="story-reader" data-story={story.slug}>
    <div className="story-reader-topline">
      <Link to="/stories">← 说故事</Link>
      <a href={story.image.url} target="_blank" rel="noopener noreferrer">看整页 ↗</a>
    </div>
    <header ref={heading} className="story-reader-heading">
      <h1>{story.title}</h1>
      <p aria-live="polite">第 {page + 1} / {total} 页</p>
    </header>
    <nav className="story-chapters" aria-label="故事章节">
      {chapters.map((item) => <button key={item.id} type="button"
        aria-current={chapter === item.id ? "step" : undefined}
        onClick={() => setPage(item.page)}>{item.label}</button>)}
    </nav>
    <div className="story-reading-surface" data-page={page + 1} data-chapter={chapter}
      onTouchCancel={() => { touch.current = null; }}
      onTouchStart={(event) => { const point = event.touches[0]; touch.current = point ? { x: point.clientX, y: point.clientY } : null; }}
      onTouchEnd={(event) => {
        const start = touch.current, end = event.changedTouches[0];
        touch.current = null;
        if (!start || !end) return;
        const dx = end.clientX - start.x, dy = end.clientY - start.y;
        if (Math.abs(dx) > 60 && Math.abs(dy) < Math.abs(dx) / 2) move(dx < 0 ? 1 : -1);
      }}>
      {panel ? <figure className="story-book" data-panel={panel.number}>
        <StoryArtwork image={story.image} panel={panel} />
        <figcaption aria-live="polite" aria-atomic="true">
          <span className="story-panel-number" aria-hidden="true">{panel.number}</span>
          <p>{panel.caption}</p>
        </figcaption>
      </figure> : <section className={`story-prose-page story-prose-${chapter}`} aria-labelledby="story-page-title">
        <p className="stories-eyebrow">{page === 0 ? "故事开场" : last ? "读完这一篇" : "故事后记"}</p>
        <h2 id="story-page-title">{page === 0 ? story.introduction.title : last ? story.afterword.takeaway.title : story.afterword.title}</h2>
        {page === 0 ? <>
          <p className="story-prose-copy">{story.introduction.text}</p>
          <p className="story-prose-footer">接下来 · {count} 格连环画</p>
        </> : last ? <>
          <p className="story-prose-copy">{story.afterword.takeaway.text}</p>
          <p className="story-source-note">{story.afterword.sourceNote}</p>
        </> : story.afterword.paragraphs.map((text) => <p className="story-prose-copy" key={text}>{text}</p>)}
      </section>}
    </div>
    <div className="story-reader-controls" aria-label="翻页">
      <button type="button" className="story-previous" disabled={page === 0} onClick={() => move(-1)}>← 上一页</button>
      <span className="story-position" aria-hidden="true">{page + 1} / {total}</span>
      {last
        ? <button type="button" className="story-next" onClick={() => setPage(0)}>再看一遍 ↻</button>
        : <button type="button" className="story-next" onClick={() => move(1)}>{nextLabel}</button>}
    </div>
    {last ? <div className="story-ending">
      {nextStory && <Link to={`/stories/${nextStory.slug}`}>再看一个：{nextStory.title} →</Link>}
      <Link to="/stories">返回说故事</Link>
    </div> : <p className="story-reader-hint">左右滑动，或点击按钮翻页</p>}
  </div>;
}

export function StoryPage() {
  const { slug } = useParams();
  const story = storyBySlug(slug);
  if (!story) return <div className="story-not-found"><h1>这篇故事还没翻到。</h1><Link to="/stories">去看看其他故事 →</Link></div>;
  return <StoryReader key={story.slug} story={story} />;
}
