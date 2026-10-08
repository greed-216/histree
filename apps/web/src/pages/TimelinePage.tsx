import { TimelineExplorer } from "../components/TimelineExplorer";

export function TimelinePage() {
  return (
    <div className="timeline-page space-y-6">
      <header className="explore-heading">
        <p className="eyebrow">HISTREE · 时间探索</p>
        <h1>让历史，沿时间展开</h1>
        <p>拖动时间图，浏览历史；放大查看史事，点击年份停下来读。</p>
      </header>
      <TimelineExplorer />
    </div>
  );
}
