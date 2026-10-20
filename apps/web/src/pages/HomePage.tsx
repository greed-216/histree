import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowUpRightIcon,
  ChatBubbleLeftRightIcon,
  IdentificationIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import type { TimelineOverview } from "@histree/shared-types";
import { HomeTimeline } from "../components/HomeTimeline";
import { apiFetch } from "../lib/api";
import "../styles/home.css";

export function HomePage() {
  const navigate = useNavigate();
  const [wandering, setWandering] = useState(false);
  const [wanderError, setWanderError] = useState("");
  const wanderRequest = useRef<AbortController | null>(null);
  useEffect(() => () => wanderRequest.current?.abort(), []);

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = String(new FormData(event.currentTarget).get("q") || "").trim();
    navigate(query ? `/search?${new URLSearchParams({ q: query })}` : "/search");
  }

  async function wander() {
    if (wanderRequest.current) return;
    const controller = new AbortController();
    wanderRequest.current = controller;
    setWandering(true);
    setWanderError("");
    try {
      const overview = await apiFetch<TimelineOverview>("/timeline/overview", {
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
      });
      const years = overview.years.filter(row => row.count > 0);
      const year = years[Math.floor(Math.random() * years.length)];
      if (!year) throw new Error("暂时没有可浏览的史事，请稍后再试。");
      navigate(`/timeline?year=${year.year}`);
    } catch {
      if (!controller.signal.aborted) setWanderError("暂时没能找到落脚处，再试一次，或先搜索看看。");
    } finally {
      if (!controller.signal.aborted) setWandering(false);
      wanderRequest.current = null;
    }
  }

  return (
    <div className="home-page">
      <section className="home-portal" aria-labelledby="home-title">
        <p className="home-kicker">HISTREE · 历史之树</p>
        <h1 id="home-title"><span>从一个名字，</span><span>走进一段历史。</span></h1>
        <p className="home-intro">查人物，读史事，循着好奇心发现历史。</p>
        <form role="search" aria-label="搜索历史" className="home-search" onSubmit={search}>
          <MagnifyingGlassIcon className="home-search-icon" aria-hidden="true" />
          <label htmlFor="home-search" className="sr-only">搜索历史人物、事件或专题</label>
          <input id="home-search" type="search" name="q" maxLength={200}
            placeholder="人物、事件，或你感兴趣的线索" enterKeyHint="search" />
          <button type="submit">搜索</button>
        </form>
        <div className="home-shortcuts" aria-label="快捷入口">
          <Link to="/ask?mode=guess">猜一个人物 <ArrowUpRightIcon aria-hidden="true" /></Link>
          <span aria-hidden="true">·</span>
          <Link to="/ask">问问史料 <ArrowUpRightIcon aria-hidden="true" /></Link>
          <span aria-hidden="true">·</span>
          <button type="button" disabled={wandering} onClick={wander}>
            {wandering ? "寻找一段往事…" : "随便走走"} <ArrowUpRightIcon aria-hidden="true" />
          </button>
        </div>
        <p className="home-wander-status" role="status">{wanderError}</p>
      </section>

      <HomeTimeline />

      <section className="home-play" aria-labelledby="home-play-title">
        <div className="home-section-heading">
          <div><p className="home-kicker">换一种方式</p><h2 id="home-play-title">今天，怎么玩历史？</h2></div>
          <p>从一个问题开始，遇见一段故事。</p>
        </div>
        <div className="home-play-grid">
          <Link to="/ask?mode=guess" className="home-play-card home-play-guess">
            <IdentificationIcon className="home-play-icon" aria-hidden="true" />
            <p className="home-card-kind">线索推理</p>
            <h3>猜猜我是谁</h3>
            <p className="home-card-description">从一条线索开始，<br />认出一位历史人物。</p>
            <span className="home-card-action">开始猜人物 <ArrowUpRightIcon aria-hidden="true" /></span>
          </Link>
          <Link to="/ask" className="home-play-card home-play-ask">
            <ChatBubbleLeftRightIcon className="home-play-icon" aria-hidden="true" />
            <p className="home-card-kind">带着好奇心</p>
            <h3>问史料</h3>
            <p className="home-card-description">那件事，史书究竟怎么说？<br />从一个问题出发，沿着出处读下去。</p>
            <span className="home-card-action">问个问题 <ArrowUpRightIcon aria-hidden="true" /></span>
          </Link>
          <article className="home-play-card home-play-upcoming">
            <div className="home-card-top"><SparklesIcon className="home-play-icon" aria-hidden="true" /><span className="home-coming-label">筹备中</span></div>
            <p className="home-card-kind">人物扮演</p>
            <h3>历史人生</h3>
            <p className="home-card-description">你还不知道自己是谁，<br />却要在历史的岔路口，做一次自己的选择。</p>
            <span className="home-card-action">故事，正在酝酿</span>
          </article>
        </div>
      </section>

      <nav className="home-reading-links" aria-label="继续阅读">
        <span>继续循着线索阅读</span>
        <Link to="/people">人物</Link><Link to="/events">事件</Link>
        <Link to="/learn">专题导读</Link><Link to="/graph">关系图谱</Link>
      </nav>
    </div>
  );
}
