import { Component, Suspense, lazy, useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

const TimelineExplorer = lazy(() => import("./TimelineExplorer").then(module => ({ default: module.TimelineExplorer })));

function TimelinePlaceholder() {
  return <div className="home-timeline-placeholder" role="status">
    <div className="home-placeholder-bands" aria-hidden="true"><span /><span /><span /><span /><span /></div>
    <div className="home-placeholder-painting"><span>画卷即将展开</span><p>先搜索一个名字，或往下看看别的玩法。</p></div>
  </div>;
}

class TimelineBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <div className="home-timeline-failed" role="alert">
      <p>画卷暂时没能展开，你仍可以搜索或体验下方玩法。</p>
      <button type="button" onClick={() => window.location.reload()}>重新加载画卷</button>
    </div> : this.props.children;
  }
}

export function HomeTimeline() {
  const slot = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!slot.current) return;
    if (!("IntersectionObserver" in window)) {
      const frame = requestAnimationFrame(() => setReady(true));
      return () => cancelAnimationFrame(frame);
    }
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        setReady(true);
        observer.disconnect();
      }
    }, { rootMargin: "240px 0px" });
    observer.observe(slot.current);
    return () => observer.disconnect();
  }, []);

  return <section className="home-timeline" aria-labelledby="home-timeline-title">
    <div className="home-section-heading">
      <div><p className="home-kicker">沿时间，走进历史</p><h2 id="home-timeline-title">历史画卷</h2></div>
      <Link to="/timeline">进入完整画卷 <span aria-hidden="true">↗</span></Link>
    </div>
    <div ref={slot} className="home-timeline-slot">
      {ready ? <TimelineBoundary><Suspense fallback={<TimelinePlaceholder />}><TimelineExplorer compact loadingFallback={<TimelinePlaceholder />} /></Suspense></TimelineBoundary> : <TimelinePlaceholder />}
    </div>
  </section>;
}
