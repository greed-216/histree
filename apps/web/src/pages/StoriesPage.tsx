import { useCallback, useEffect, useRef, useState } from "react";
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
  const [index, setIndex] = useState(0);
  const touch = useRef<{ x: number; y: number } | null>(null);
  const count = story.panels.length;
  const panel = story.panels[index];
  const last = index === count - 1;
  const nextStory = stories.length > 1 ? stories[(stories.indexOf(story) + 1) % stories.length] : undefined;
  const move = useCallback((direction: number) => setIndex((value) => Math.max(0, Math.min(count - 1, value + direction))), [count]);

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
    <header className="story-reader-heading">
      <h1>{story.title}</h1>
      <p>第 {index + 1} / {count} 格</p>
    </header>
    <figure className="story-book" data-panel={panel.number}
      onTouchCancel={() => { touch.current = null; }}
      onTouchStart={(event) => { const point = event.touches[0]; touch.current = point ? { x: point.clientX, y: point.clientY } : null; }}
      onTouchEnd={(event) => {
        const start = touch.current, end = event.changedTouches[0];
        touch.current = null;
        if (!start || !end) return;
        const dx = end.clientX - start.x, dy = end.clientY - start.y;
        if (Math.abs(dx) > 60 && Math.abs(dy) < Math.abs(dx) / 2) move(dx < 0 ? 1 : -1);
      }}>
      <StoryArtwork image={story.image} panel={panel} />
      <figcaption aria-live="polite" aria-atomic="true">
        <span className="story-panel-number" aria-hidden="true">{panel.number}</span>
        <p>{panel.caption}</p>
      </figcaption>
    </figure>
    <div className="story-reader-controls" aria-label="翻页">
      <button type="button" className="story-previous" disabled={index === 0} onClick={() => move(-1)}>← 上一格</button>
      <span className="story-position" aria-hidden="true">{index + 1} / {count}</span>
      {last
        ? <button type="button" className="story-next" onClick={() => setIndex(0)}>再看一遍 ↻</button>
        : <button type="button" className="story-next" onClick={() => move(1)}>下一格 →</button>}
    </div>
    {last ? <div className="story-ending">
      <p>故事讲完了。</p>
      {nextStory && <Link to={`/stories/${nextStory.slug}`}>再看一个：{nextStory.title} →</Link>}
      <Link to="/stories">返回说故事</Link>
    </div> : <p className="story-reader-hint">左右滑动，或点击下一格</p>}
  </div>;
}

export function StoryPage() {
  const { slug } = useParams();
  const story = storyBySlug(slug);
  if (!story) return <div className="story-not-found"><h1>这篇故事还没翻到。</h1><Link to="/stories">去看看其他故事 →</Link></div>;
  return <StoryReader key={story.slug} story={story} />;
}
