import { guessEras as eras } from "../lib/guessOptions";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  guessRequest,
  guessStatus,
  GuessRequestError,
  type GuessState,
} from "../lib/guess";
const difficulties = [
  { value: "easy", label: "简单", description: "从较熟悉的人物和代表事迹猜起" },
  {
    value: "hard",
    label: "困难",
    description: "人物范围更广，沿着细节寻找线索",
  },
] as const;

function difficultyLabel(value: GuessState["filters"]["difficulty"]) {
  if (value === "easy") return "简单";
  if (value === "hard") return "困难";
  return ["简单", "一般", "较难", "困难", "极难"][value - 1] || "困难";
}
const storageKey = "histree-guess-token";
const button =
  "rounded-lg bg-teal-800 text-white px-5 py-2 disabled:opacity-40";
export function QuestionGuessGame() {
  const [difficulty, setDifficulty] = useState<"easy" | "hard">("easy");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [customYears, setCustomYears] = useState(false);
  const [identity, setIdentity] = useState("");
  const [gender, setGender] = useState("any");
  const [custom, setCustom] = useState("");
  const [game, setGame] = useState<GuessState>();
  const [token, setToken] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [starting, setStarting] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!busy || !starting) return;
    const started = Date.now();
    const timer = window.setInterval(
      () => setElapsed(Math.floor((Date.now() - started) / 1000)),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [busy, starting]);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const abort = useRef<AbortController | null>(null);
  const log = useRef<HTMLDivElement | null>(null);
  const feedback = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    abort.current = controller;
    guessStatus(controller.signal)
      .then(setAvailable)
      .catch(() => {
        if (!controller.signal.aborted) setAvailable(false);
      });
    let saved = "";
    try {
      saved = sessionStorage.getItem(storageKey) || "";
    } catch {
      /* optional persistence */
    }
    if (saved) {
      setBusy(true);
      guessRequest("act", { token: saved, action: "state" }, controller.signal)
        .then((state) => {
          setGame(state);
          setToken(saved);
          const value = state.filters.difficulty;
          setDifficulty(
            value === "easy" || (typeof value === "number" && value <= 2)
              ? "easy"
              : "hard",
          );
          setCustomYears(
            !eras.some(
              (era) =>
                era.from === String(state.filters.from ?? "") &&
                era.to === String(state.filters.to ?? ""),
            ),
          );
          setFrom(
            state.filters.from === undefined ? "" : String(state.filters.from),
          );
          setTo(state.filters.to === undefined ? "" : String(state.filters.to));
          setIdentity(state.filters.identity);
          setGender(state.filters.gender);
          setCustom(state.filters.custom);
        })
        .catch((err) => {
          if (!controller.signal.aborted) {
            setError(err instanceof Error ? err.message : "无法恢复游戏。");
            if (
              err instanceof GuessRequestError &&
              [401, 403, 410].includes(err.status)
            ) {
              try {
                sessionStorage.removeItem(storageKey);
              } catch {
                /* optional */
              }
            }
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setBusy(false);
        });
    }
    return () => {
      controller.abort();
      abort.current?.abort();
    };
  }, []);
  useEffect(() => {
    log.current?.scrollTo({
      top: log.current.scrollHeight,
      behavior: "smooth",
    });
  }, [game?.turns.length]);
  useEffect(() => {
    if (notice || error) {
      feedback.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [notice, error]);
  async function request(path: "start" | "act" | "feedback", body: unknown) {
    if (busy) return;
    const controller = new AbortController();
    abort.current = controller;
    setBusy(true);
    setStarting(path === "start");
    setElapsed(0);
    setError("");
    setNotice("");
    try {
      const state = await guessRequest(path, body, controller.signal);
      if (state.token) {
        setToken(state.token);
        try {
          sessionStorage.setItem(storageKey, state.token);
        } catch {
          /* optional */
        }
      }
      setGame(state);
      setNotice(state.notice || "");
      if (!state.notice) setText("");
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : "请求未完成，请重试。");
        if (
          err instanceof GuessRequestError &&
          [401, 403, 410].includes(err.status)
        ) {
          setGame(undefined);
          setToken("");
          try {
            sessionStorage.removeItem(storageKey);
          } catch {
            /* optional */
          }
        }
      }
    } finally {
      if (!controller.signal.aborted) {
        setBusy(false);
        setStarting(false);
      }
    }
  }
  const active = game && !game.outcome;
  const feedbackPanel = (
    <div ref={feedback} className="space-y-2" aria-busy={busy}>
      {busy && starting && (
        <div
          role="status"
          className="rounded-xl border border-teal-200 bg-teal-50 p-4 flex gap-3 text-teal-900"
        >
          <span
            className="mt-1 size-5 shrink-0 rounded-full border-2 border-teal-200 border-t-teal-700 motion-safe:animate-spin"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">正在准备这一局的人物资料…</p>
            <p className="mt-2 text-sm text-stone-600">
              首次遇到的人物可能需要补查和核对，完成后会自动进入游戏，无需刷新。
            </p>
            <p className="mt-2 text-xs text-stone-500" aria-live="off">
              已等待 {elapsed} 秒
            </p>
          </div>
        </div>
      )}
      <p role="status" aria-live="polite" className="text-sm text-teal-800">
        {busy
          ? starting
            ? ""
            : "正在核对本局资料，请稍候…"
          : available === null
            ? "正在检查游戏服务…"
            : !available
              ? "猜人物服务暂未就绪。"
              : ""}
      </p>
      {notice && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-7 text-amber-900"
        >
          <p className="font-medium">本次操作未计入次数</p>
          <p>{notice}</p>
        </div>
      )}
      {error && (
        <p
          role="alert"
          className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-7 text-amber-900"
        >
          {error}
        </p>
      )}
    </div>
  );
  const setup = (
    <form
      className="reading-card space-y-5"
      onSubmit={(e) => {
        e.preventDefault();
        void request("start", {
          difficulty,
          ...(from ? { from: Number(from) } : {}),
          ...(to ? { to: Number(to) } : {}),
          identity,
          gender,
          custom,
        });
      }}
    >
      <fieldset disabled={busy}>
        <legend className="font-medium mb-3">选一个难度</legend>
        <div className="grid sm:grid-cols-2 gap-3">
          {difficulties.map(({ value, label, description }) => (
            <button
              type="button"
              key={label}
              aria-pressed={difficulty === value}
              onClick={() => setDifficulty(value)}
              className={`text-left rounded-xl border p-3 ${difficulty === value ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200"}`}
            >
              <span className="block font-medium">{label}</span>
              <span className="block text-xs leading-5 mt-1 text-stone-500">
                {description}
              </span>
            </button>
          ))}
        </div>
      </fieldset>
      <fieldset disabled={busy} className="space-y-3">
        <legend className="font-medium mb-3">想猜哪个时代的人？</legend>
        <div className="flex flex-wrap gap-2">
          {eras.map((era) => (
            <button
              type="button"
              key={era.label}
              aria-pressed={!customYears && from === era.from && to === era.to}
              onClick={() => {
                setFrom(era.from);
                setTo(era.to);
                setCustomYears(false);
              }}
              className={`rounded-full border px-4 py-2 text-sm ${!customYears && from === era.from && to === era.to ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 text-stone-600"}`}
            >
              {era.label}
            </button>
          ))}
          <button
            type="button"
            aria-pressed={customYears}
            onClick={() => setCustomYears(true)}
            className={`rounded-full border px-4 py-2 text-sm ${customYears ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 text-stone-600"}`}
          >
            自选年代
          </button>
        </div>
        {customYears && (
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="text-sm">
              年代起点
              <input
                type="number"
                min={-3000}
                max={2100}
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                placeholder="如 600；公元前用负数"
                className="reading-input w-full mt-2"
              />
            </label>
            <label className="text-sm">
              年代终点
              <input
                type="number"
                min={-3000}
                max={2100}
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="如 960"
                className="reading-input w-full mt-2"
              />
            </label>
          </div>
        )}
        <p className="text-xs leading-6 text-stone-500">
          按已收录的生卒年或活动事件筛选；各时代收录仍在补充。
        </p>
      </fieldset>
      <details className="rounded-xl border border-stone-200 px-4 py-3">
        <summary className="cursor-pointer text-sm text-stone-600">
          高级设置
          {identity || gender !== "any" || custom ? " · 已设限定" : " · 可选"}
        </summary>
        <fieldset disabled={busy} className="grid sm:grid-cols-2 gap-4 mt-4">
          <legend className="sr-only">更多人物限定</legend>
          <label className="text-sm">
            身份
            <input
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
              maxLength={80}
              placeholder="如皇帝、诗人、将领"
              className="reading-input w-full mt-2"
            />
          </label>
          <label className="text-sm">
            性别
            <select
              aria-label="性别"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="reading-input w-full mt-2"
            >
              <option value="any">不限</option>
              <option value="male">男性</option>
              <option value="female">女性</option>
            </select>
          </label>
          <label className="text-sm sm:col-span-2">
            自定义限定
            <textarea
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              maxLength={200}
              placeholder="如：五代十国时期，与后唐有交集的人物"
              className="reading-input w-full mt-2"
            />
          </label>
        </fieldset>
      </details>
      <div className="flex flex-wrap gap-4 items-center">
        <button
          disabled={
            busy || !available || (!!from && !!to && Number(from) > Number(to))
          }
          className={button}
        >
          {game ? "再开一局" : "随机开局"}
        </button>
        <span className="text-sm text-stone-500">开局后限定条件固定</span>
      </div>
    </form>
  );
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="reading-card bg-gradient-to-br! from-teal-50 to-stone-50">
        <p className="eyebrow">一个人 · 三十次机会 · 从问题找到答案</p>
        <h1 className="font-serif text-3xl md:text-4xl mt-3">猜猜我是谁</h1>
        <p className="mt-4 text-stone-600 leading-7">
          一位历史人物正在等你。问“你是唐朝人吗？”这样的是非问题，逐步缩小范围，猜到后直接输入姓名或别名即可。
        </p>
        <details className="mt-3 text-sm text-stone-500 leading-7">
          <summary className="cursor-pointer">玩法与资料范围</summary>
          <p>
            普通回答只有“是”“不是”“不清楚”“是，也不是”。开放式问题会被拒绝且不计次数；提出人物姓名或别名也算一次对答，猜中即结束。每局最多
            30 次，每局可领取 3
            个提示，使用提示也能获胜。史书异说或兼是兼否时回答“是，也不是”；没有记载时回答“不清楚”。
          </p>
          <p>
            与线索模式共用游戏人物库，包括本站尚未录入的知名人物。裁判依据本局准备的史料或通识资料卡作答；没有依据时回答“不清楚”。普通开局直接抽题，年代可按生卒、活动记录或朝代归属筛选。高级限定无法确认时不选入。通识资料会明确标示，结束后可以回看本局依据。
          </p>
          <p>会话保留 1 小时；刷新可恢复，服务重启会失效。</p>
        </details>
      </header>
      {!game && setup}
      {game && (
        <section className="reading-card space-y-5" aria-label="游戏进度">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif text-xl">
              {game.outcome
                ? game.outcome === "won"
                  ? "你猜对了！"
                  : "本局已结束"
                : "我是谁？"}
            </h2>
            <span className="text-sm text-stone-500">
              {difficultyLabel(game.filters.difficulty)} · 剩余 {game.remaining}{" "}
              次 · 提示 {game.hints.length}/3
            </span>
          </div>
          <p className="text-xs text-stone-500">
            本局限定：
            {[
              game.filters.from !== undefined || game.filters.to !== undefined
                ? `${game.filters.from ?? "不限"} 至 ${game.filters.to ?? "不限"} 年`
                : "年代不限",
              game.filters.identity || "身份不限",
              game.filters.gender === "male"
                ? "男性"
                : game.filters.gender === "female"
                  ? "女性"
                  : "性别不限",
              game.filters.custom,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {game.hints.length > 0 && (
            <aside className="rounded-xl bg-amber-50 p-4 text-sm leading-7">
              {game.hints.map((hint, i) => (
                <p key={i}>
                  提示 {i + 1}：{hint}
                </p>
              ))}
            </aside>
          )}
          <div
            ref={log}
            role="log"
            aria-label="提问记录"
            aria-live="polite"
            className="max-h-96 overflow-y-auto space-y-3"
          >
            {game.turns.length === 0 ? (
              <p className="text-stone-500 text-sm py-4">
                试着先从时代或身份问起。
              </p>
            ) : (
              game.turns.map((turn, i) => (
                <div key={i} className="border-b border-stone-100 pb-3">
                  <p className="text-sm text-stone-600">
                    {i + 1}. {turn.text}
                  </p>
                  <p className="mt-1 font-medium text-teal-900">
                    {turn.answer}
                  </p>
                </div>
              ))
            )}
          </div>
          {feedbackPanel}
          {active && (
            <>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void request("act", {
                    token,
                    action: "question",
                    text: text.trim(),
                  });
                }}
                className="space-y-3"
              >
                <label htmlFor="guess-text" className="sr-only">
                  问题或人物名字
                </label>
                <input
                  id="guess-text"
                  autoComplete="off"
                  className="reading-input w-full"
                  value={text}
                  disabled={busy}
                  onChange={(e) => setText(e.target.value)}
                  maxLength={400}
                  placeholder="问一个是非问题，或输入人物名字（如李亚子）…"
                />
                <div className="flex flex-wrap justify-between gap-3">
                  <button className={button} disabled={busy || !text.trim()}>
                    {busy ? "正在处理…" : "提交"}
                  </button>
                  <button
                    type="button"
                    className="text-sm text-amber-800 underline disabled:opacity-40"
                    disabled={busy || game.hints.length >= 3}
                    onClick={() =>
                      void request("act", { token, action: "hint" })
                    }
                  >
                    领取提示{" "}
                    {game.hints.length + 1 > 3 ? "" : game.hints.length + 1}
                  </button>
                </div>
              </form>
              <details className="text-sm text-stone-500">
                <summary className="cursor-pointer">想结束这一局？</summary>
                <p className="mt-2">揭晓后本局结束，可以查看人物和出处。</p>
                <button
                  disabled={busy}
                  className="mt-2 underline text-amber-800"
                  onClick={() =>
                    void request("act", { token, action: "reveal" })
                  }
                >
                  结束并揭晓答案
                </button>
              </details>
            </>
          )}
          {game.person && (
            <div className="rounded-xl bg-teal-50 p-5 space-y-3">
              <p className="eyebrow">
                {game.outcome === "limit"
                  ? "已用完三十次机会 · 答案揭晓"
                  : "从猜测走向了解"}
              </p>
              <h3 className="font-serif text-2xl">{game.person.name}</h3>
              <p className="text-sm leading-7 text-stone-600">
                {game.person.description}
              </p>
              {game.person.id && (
                <div className="flex flex-wrap gap-4 text-sm text-teal-800">
                  <Link className="underline" to={`/people/${game.person.id}`}>
                    阅读人物资料 →
                  </Link>
                  <Link className="underline" to={`/graph/${game.person.id}`}>
                    查看人物图谱 →
                  </Link>
                  <Link
                    className="underline"
                    to={`/evidence/person/${game.person.id}`}
                  >
                    本站已录入史料 →
                  </Link>
                  <Link
                    className="underline"
                    to={`/ask?kind=person&id=${game.person.id}`}
                  >
                    继续问史料 →
                  </Link>
                </div>
              )}
              {game.ratingEligible && (
                <section
                  className="rounded-xl border border-teal-100 bg-white/70 p-4"
                  aria-label="本局难度反馈"
                >
                  <p className="font-medium">这位人物，对你来说难猜吗？</p>
                  <p className="mt-1 text-xs leading-6 text-stone-500">
                    参考你本局选择的“{difficultyLabel(game.filters.difficulty)}
                    ”难度。你的反馈会帮助后续玩家遇到更合适的人物。
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(
                      [
                        ["easy", "太简单了"],
                        ["right", "刚刚好"],
                        ["hard", "有点难"],
                      ] as const
                    ).map(([rating, label]) => (
                      <button
                        type="button"
                        key={rating}
                        disabled={busy || !!game.rating}
                        aria-pressed={game.rating === rating}
                        className={`rounded-full border px-4 py-2 text-sm disabled:cursor-default ${game.rating === rating ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 text-stone-600 disabled:opacity-50"}`}
                        onClick={() =>
                          void request("feedback", { token, rating })
                        }
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  {game.rating && (
                    <p role="status" className="mt-3 text-sm text-teal-800">
                      反馈已收下，谢谢你帮我们校准难度。
                    </p>
                  )}
                </section>
              )}
              <details className="text-sm leading-7">
                <summary className="cursor-pointer">
                  回看本局依据（{game.evidence?.length ?? 0} 条）
                </summary>
                {game.evidence?.map((c) => (
                  <article
                    key={c.id}
                    className="border-t border-teal-100 mt-3 pt-3"
                  >
                    <p className="font-medium">
                      {c.title} · {c.location}
                    </p>
                    <p>{c.claim}</p>
                    <p className="text-stone-600 whitespace-pre-wrap">
                      {c.note}
                    </p>
                  </article>
                ))}
              </details>
            </div>
          )}
        </section>
      )}
      {game?.outcome && setup}
      {!game && feedbackPanel}
    </div>
  );
}
