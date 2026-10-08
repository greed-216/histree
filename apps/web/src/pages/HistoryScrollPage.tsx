import { Link } from "react-router-dom";
import { historyScroll, scrollPeriodShare } from "../lib/historyScroll";
export function HistoryScrollPage() {
  const totalWidth = historyScroll.logical_canvas.width;
  return (
    <div className="space-y-6 pb-10">
      <Link className="text-teal-800" to="/">
        ← 回到首页
      </Link>
      <header className="explore-heading">
        <p className="eyebrow">历史画卷 · 底图预览</p>
        <h1>从春秋战国到清末</h1>
        <p>前770年—1912年，按年代比例连续展开。横向滚动查看细节。</p>
      </header>
      <div
        className="scroll-gallery"
        tabIndex={0}
        aria-label="完整历史长卷，可横向滚动"
      >
        <div
          className="scroll-gallery-canvas"
          style={{
            width: totalWidth,
            height: historyScroll.logical_canvas.height,
          }}
        >
          {historyScroll.panels.map((panel) => (
            <img
              key={panel.id}
              src={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
              alt={
                panel.id === "scroll-01"
                  ? "春秋战国至东汉早期的文化意象"
                  : panel.id === "scroll-02"
                    ? "东汉后期至宋初的文化意象"
                    : "宋、元、明、清至清末的文化意象"
              }
              style={{
                width:
                  totalWidth *
                  scrollPeriodShare(panel.from_year, panel.to_year),
                height: historyScroll.logical_canvas.height,
              }}
            />
          ))}
        </div>
      </div>
      <p className="text-sm text-stone-500 leading-7">
        {historyScroll.artwork_note} 三幅生图原件组成约9:1长卷，网页展示尺寸为
        {totalWidth}×{historyScroll.logical_canvas.height}。
      </p>
      <div className="grid sm:grid-cols-3 gap-4">
        {historyScroll.periods.map((period) => (
          <div className="reading-card" key={period.label}>
            <p className="font-serif text-lg">{period.label}</p>
            <p className="text-sm text-stone-500 mt-2">
              约占长卷{" "}
              {(
                scrollPeriodShare(period.from_year, period.to_year) * 100
              ).toFixed(1)}
              %
            </p>
          </div>
        ))}
      </div>
      <p className="text-xs text-stone-500">
        分期按中原主线作大体划分；不同政权可能并存。元从统一南宋后、清从入关后计算画幅。
      </p>
    </div>
  );
}
