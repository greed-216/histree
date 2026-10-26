import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import "../styles/timeline-ancient.css";
import { HistoryScrollBackdrop } from "../components/HistoryScrollBackdrop";
import { ancientChapters, historyScroll, scrollPeriodShare, scrollStart } from "../lib/historyScroll";
import { ordinal } from "../lib/timelineViewport";
export function HistoryScrollPage() {
  const gallery=useRef<HTMLDivElement>(null);
  const [visible,setVisible]=useState({from:scrollStart,to:scrollStart+300});
  function updateVisible(){
    const element=gallery.current;if(!element)return;
    setVisible({from:scrollStart+element.scrollLeft/historyScroll.pixels_per_elapsed_year,
      to:scrollStart+(element.scrollLeft+element.clientWidth)/historyScroll.pixels_per_elapsed_year});
  }
  useEffect(()=>{const observer=new ResizeObserver(updateVisible);if(gallery.current)observer.observe(gallery.current);return()=>observer.disconnect();},[]);
  const totalWidth = (ordinal(historyScroll.to_year)-scrollStart)*historyScroll.pixels_per_elapsed_year;
  const canvasHeight = 720*920/totalWidth;
  return <div className="space-y-6 pb-10">
    <Link className="text-teal-800" to="/">← 回到首页</Link>
    <header className="explore-heading"><p className="eyebrow">历史画卷 · 底图预览</p><h1>从神话时代，到清末山河</h1>
      <p>前841年以前按时代章节展开，之后按年展开。横向滚动查看整幅画卷。</p></header>
    <div ref={gallery} onScroll={updateVisible} className="scroll-gallery" tabIndex={0} aria-label="完整历史长卷，可横向滚动">
      <svg width={totalWidth} height="720" viewBox={`40 96 920 ${canvasHeight}`} role="img" aria-label="神话时代、夏商西周与年度画卷连续衔接的完整长卷">
        <HistoryScrollBackdrop from={scrollStart} to={ordinal(historyScroll.to_year)} height={canvasHeight} rounded={false} pixelsPerSvgUnit={totalWidth/920} loadFrom={visible.from} loadTo={visible.to}/>
      </svg>
    </div>
    <p className="text-sm text-stone-500 leading-7">{historyScroll.artwork_note} 多幅画面在山水重叠区衔接；既有战国至清末的底图文件保留，年度画面沿用原比例。时代章节的画幅宽度只用于组织阅读，不表示具体年数。</p>
    <section className="reading-card"><h2 className="font-serif text-xl">前841年以前：按时代进入</h2>
      <div className="timeline-era-themes">{ancientChapters.map(chapter=><Link key={chapter.id} to={`/timeline?era=${chapter.id}`}>{chapter.label} · {chapter.theme} →</Link>)}</div>
      <p className="text-sm text-stone-500">神话时代突出尧、舜、禹的文献叙事；夏商西周以生活、生产和礼仪场景展开。有明确依据的具体时间在条目中保留，画面本身不为未定年叙事补造年份。</p>
    </section>
    <section className="reading-card"><h2 className="font-serif text-xl">两个衔接点</h2>
      <p className="text-sm text-stone-600 leading-7 mt-2">前841年是从时代章节切换为年度刻度的位置，仍处于西周。前403年是新增画面接回旧卷的位置，两者均不以画中关隘或突然换景表达。</p>
      <Link className="timeline-detail-link" to="/timeline?year=-841">从前841年开始浏览 →</Link>
    </section>
    <section className="reading-card" aria-labelledby="scroll-scene-heading"><h2 id="scroll-scene-heading" className="font-serif text-xl">画卷中的活动主题</h2>
      <p className="text-sm text-stone-500 leading-7 mt-2">姓名说明构图参考，不用于辨认容貌或确认某次现场。</p>
      <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-5 mt-5">{historyScroll.scene_notes.map(scene=><div key={scene.period}>
        <dt className="font-medium text-stone-800">{scene.period}{scene.figures.length>0?` · ${scene.figures.join("、")}`:""}</dt>
        <dd className="text-sm text-stone-600 leading-7 mt-1">{scene.activity}</dd></div>)}</dl>
    </section>
    <div className="grid sm:grid-cols-3 gap-4">{historyScroll.periods.map(period=><div className="reading-card" key={period.label}>
      <p className="font-serif text-lg">{period.label}</p><p className="text-sm text-stone-500 mt-2">约占整幅画卷{(scrollPeriodShare(period.from_year,period.to_year)*100).toFixed(1)}%</p></div>)}</div>
    <p className="text-xs text-stone-500">分期用于浏览导航；不同政权可能并存。春秋、战国导航采用前475年分界，旧底图仍在前403年接续；分期不表示史料已全部录入。元、清画幅分界沿用1279年、1644年。</p>
  </div>;
}
