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
  const [page, setPage] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [notice, setNotice] = useState("");
  const reader = useRef<HTMLDivElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const touch = useRef<{ x: number; y: number } | null>(null);
  const count = story.panels.length;
  const total = count + 3;
  const panel = page >= 1 && page <= count ? story.panels[page - 1] : undefined;
  const last = page === total - 1;
  const chapter = page === 0 ? "introduction" : panel ? "comic" : last ? "meaning" : "afterword";
  const chapters = [
    { id: "introduction", label: "故事开场", page: 0 },
    { id: "comic", label: `连环画 · ${count} 格`, page: 1 },
    { id: "afterword", label: "故事后记", page: count + 1 },
    { id: "meaning", label: "故事寓意", page: count + 2 },
  ];
  const nextLabel = page === 0 ? "翻开故事 →" : page === count ? "看后记 →" : page === count + 1 ? "看寓意 →" : "下一页 →";
  const nextStory = stories.length > 1 ? stories[(stories.indexOf(story) + 1) % stories.length] : undefined;
  const move = useCallback((direction: number) => setPage((value) => Math.max(0, Math.min(total - 1, value + direction))), [total]);

  useEffect(() => {
    const previousTitle = document.title;
    const previousOverflow = document.body.style.overflow;
    document.title = `${story.title} · 说故事 · Histree`;
    document.body.style.overflow = "hidden";
    return () => {
      document.title = previousTitle;
      document.body.style.overflow = previousOverflow;
    };
  }, [story.title]);

  useEffect(() => {
    const update = () => setFullscreen(document.fullscreenElement === reader.current);
    document.addEventListener("fullscreenchange", update);
    return () => document.removeEventListener("fullscreenchange", update);
  }, []);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(""), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOutside = (event: PointerEvent) => {
      if (event.target instanceof Node && !menu.current?.contains(event.target)) setMenuOpen(false);
    };
    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, [menuOpen]);

  useEffect(() => {
    function keydown(event: KeyboardEvent) {
      if (event.key === "Escape") { setMenuOpen(false); return; }
      if (menuOpen || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
        (event.target instanceof Element && event.target.closest("input,textarea,select,[contenteditable],dialog"))) return;
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        move(event.key === "ArrowRight" ? 1 : -1);
      }
    }
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [move, menuOpen]);

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement === reader.current) {
        await document.exitFullscreen();
      } else if (document.fullscreenEnabled && reader.current?.requestFullscreen) {
        await reader.current.requestFullscreen();
      } else {
        setNotice("当前浏览器不支持系统全屏，已使用整屏阅读布局。");
      }
    } catch {
      setNotice("暂时无法进入系统全屏，仍可使用整屏阅读布局。");
    }
  }

  return <div ref={reader} className="story-reader" data-story={story.slug}>
    <header className="story-reader-toolbar">
      <Link to="/stories" className="story-reader-back">← 说故事</Link>
      <h1 title={story.title}>{story.title}</h1>
      <div className="story-reader-tools">
        <div ref={menu} className="story-directory">
          <button type="button" aria-expanded={menuOpen} aria-controls="story-directory" onClick={() => setMenuOpen(!menuOpen)}>目录</button>
          {menuOpen && <nav id="story-directory" className="story-directory-menu" aria-label="故事目录">
            {chapters.map((item) => <button key={item.id} type="button"
              aria-current={chapter === item.id ? "step" : undefined}
              onClick={() => { setPage(item.page); setMenuOpen(false); }}>{item.label}</button>)}
            <a href={story.image.url} target="_blank" rel="noopener noreferrer">看整页原画 ↗</a>
          </nav>}
        </div>
        <button type="button" onClick={() => void toggleFullscreen()} aria-pressed={fullscreen}>{fullscreen ? "退出全屏" : "全屏"}</button>
      </div>
    </header>
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
          {nextStory && <Link className="story-next-story" to={`/stories/${nextStory.slug}`}>再看一个：{nextStory.title} →</Link>}
        </> : story.afterword.paragraphs.map((text) => <p className="story-prose-copy" key={text}>{text}</p>)}
      </section>}
    </div>
    <div className="story-reader-bottom">
      <div className="story-reading-progress" aria-hidden="true"><span style={{ width: `${(page + 1) / total * 100}%` }} /></div>
      <nav className="story-reader-controls" aria-label="翻页">
        <button type="button" className="story-previous" disabled={page === 0} onClick={() => move(-1)}>← 上一页</button>
        <span className="story-position" aria-live="polite" aria-label={`第 ${page + 1} 页，共 ${total} 页`}>{page + 1} / {total}</span>
        {last
          ? <button type="button" className="story-next" onClick={() => setPage(0)}>再看一遍 ↻</button>
          : <button type="button" className="story-next" onClick={() => move(1)}>{nextLabel}</button>}
      </nav>
    </div>
    {notice && <p className="story-reader-notice" role="status">{notice}</p>}
  </div>;
}

export function StoryPage() {
  const { slug } = useParams();
  const story = storyBySlug(slug);
  if (!story) return <div className="story-not-found"><h1>这篇故事还没翻到。</h1><Link to="/stories">去看看其他故事 →</Link></div>;
  return <StoryReader key={story.slug} story={story} />;
}
