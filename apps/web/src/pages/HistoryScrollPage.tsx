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
        <h1>从《资治通鉴》开篇到清末</h1>
        <p>前403年—1912年，按年代比例连续展开。横向滚动查看细节。</p>
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
            <svg
              key={panel.id}
              role="img"
              aria-label="从《资治通鉴》开篇到清末的一幅连续历史活动长卷"
              viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
              width={totalWidth * scrollPeriodShare(panel.from_year, panel.to_year)}
              height={historyScroll.logical_canvas.height}
              style={{flexShrink:0}}
              preserveAspectRatio="none"
              overflow="hidden"
            >
              <image href={`${import.meta.env.BASE_URL}timeline-scroll/${panel.file}`}
                width={panel.width} height={panel.height} />
            </svg>
          ))}
        </div>
      </div>
      <p className="text-sm text-stone-500 leading-7">
        {historyScroll.artwork_note} 五段连续扩图裁去重叠后组成一张长图，实际像素为
        {totalWidth}×{historyScroll.logical_canvas.height}。
      </p>
      {historyScroll.scene_notes.length > 0 && <section className="reading-card" aria-labelledby="scroll-scene-heading">
        <h2 id="scroll-scene-heading" className="font-serif text-xl">画卷中的活动主题</h2>
        <p className="text-sm text-stone-500 leading-7 mt-2">
          从左向右寻找这些场景。人物通过所参与的活动融入画面；以下姓名说明构图参考，不用于辨认容貌或确认某次现场。
        </p>
        <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-5 mt-5">
          {historyScroll.scene_notes.map((scene) => (
            <div key={scene.period}>
              <dt className="font-medium text-stone-800">{scene.period} · {scene.figures.join("、")}</dt>
              <dd className="text-sm text-stone-600 leading-7 mt-1">{scene.activity}</dd>
            </div>
          ))}
        </dl>
      </section>}
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
