import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  clueRequest,
  clueStatus,
  GuessRequestError,
  type ClueState,
} from "../lib/guess";
import { guessEras } from "../lib/guessOptions";

const storageKey = "histree-guess-clue-token";
const primary =
  "rounded-lg bg-teal-800 text-white px-5 py-3 disabled:opacity-40";
export function ClueGuessGame() {
  const [difficulty, setDifficulty] = useState<"easy" | "hard">("easy");
  const [era, setEra] = useState(0);
  const [game, setGame] = useState<ClueState>();
  const [token, setToken] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const [action, setAction] = useState("");
  const abort = useRef<AbortController | null>(null);
  const composition = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    abort.current = controller;
    void clueStatus(controller.signal)
      .then(setAvailable)
      .catch(() => {
        if (!controller.signal.aborted) setAvailable(false);
      });
    let saved = "";
    try {
      saved = sessionStorage.getItem(storageKey) || "";
    } catch {
      /* optional */
    }
    if (saved) {
      setBusy(true);
      void clueRequest(
        "act",
        { token: saved, action: "state" },
        controller.signal,
      )
        .then((state) => {
          setGame(state);
          setToken(saved);
          setDifficulty(state.filters.difficulty);
          const index = guessEras.findIndex(
            (e) =>
              e.from === String(state.filters.from ?? "") &&
              e.to === String(state.filters.to ?? ""),
          );
          setEra(Math.max(0, index));
        })
        .catch((err) => {
          if (!controller.signal.aborted) {
            setError(err instanceof Error ? err.message : "无法恢复这一局");
            if (
              err instanceof GuessRequestError &&
              [401, 403, 410].includes(err.status)
            )
              try {
                sessionStorage.removeItem(storageKey);
              } catch {
                /* optional */
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
  async function request(
    path: "start" | "act" | "feedback",
    body: unknown,
    label: string,
  ) {
    if (busy) return;
    const controller = new AbortController();
    abort.current = controller;
    setBusy(true);
    setError("");
    setAction(label);
    try {
      const state = await clueRequest(path, body, controller.signal);
      setGame(state);
      if (label === "guess" || path === "start") setText("");
      if (state.token) {
        setToken(state.token);
        try {
          sessionStorage.setItem(storageKey, state.token);
        } catch {
          /* optional */
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : "请求未完成，请重试");
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
        setAction("");
      }
    }
  }
  const setup = (
    <form
      className="reading-card space-y-5"
      onSubmit={(e) => {
        e.preventDefault();
        const selected = guessEras[era];
        void request(
          "start",
          {
            difficulty,
            ...(selected.from ? { from: Number(selected.from) } : {}),
            ...(selected.to ? { to: Number(selected.to) } : {}),
          },
          "start",
        );
      }}
    >
      <fieldset disabled={busy}>
        <legend className="font-medium mb-3">想猜哪一类人物？</legend>
        <div className="grid sm:grid-cols-2 gap-3">
          {(
            [
              ["easy", "简单", "从较熟悉的人物猜起"],
              ["hard", "困难", "人物范围更广，试试你能认出谁"],
            ] as const
          ).map(([value, label, description]) => (
            <button
              key={value}
              type="button"
              aria-pressed={difficulty === value}
              onClick={() => setDifficulty(value)}
              className={`rounded-xl border p-4 text-left ${difficulty === value ? "border-teal-700 bg-teal-50" : "border-stone-200"}`}
            >
              <span className="block font-medium">{label}</span>
              <span className="text-xs text-stone-500">{description}</span>
            </button>
          ))}
        </div>
      </fieldset>
      <fieldset disabled={busy}>
        <legend className="font-medium mb-3">哪个时代？</legend>
        <div className="flex flex-wrap gap-2">
          {guessEras.map((e, i) => (
            <button
              key={e.label}
              type="button"
              aria-pressed={era === i}
              onClick={() => setEra(i)}
              className={`rounded-full border px-4 py-2 text-sm ${era === i ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 text-stone-600"}`}
            >
              {e.label}
            </button>
          ))}
        </div>
      </fieldset>
      <button className={primary} disabled={busy || !available}>
        {game ? "再猜一个人物" : "给我第一条线索"}
      </button>
    </form>
  );
  const active = game && !game.outcome;
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="reading-card bg-gradient-to-br! from-teal-50 to-stone-50">
        <p className="eyebrow">几条线索，认出一个人</p>
        <h1 className="font-serif text-3xl md:text-4xl mt-3">猜猜我是谁</h1>
        <p className="mt-4 text-stone-600 leading-7">
          先看一条，想到名字就猜。还没把握？再看一条，由你决定什么时候揭开更多提示。
        </p>
        <details className="mt-3 text-sm text-stone-500 leading-7">
          <summary className="cursor-pointer">怎么玩</summary>
          <p>
            人物与提问模式共用人物库，难度反馈分别记录。每人有 6
            条线索，猜错不会自动结束，也不会自动放开提示。猜中后会展示全部线索和相关故事；也可以主动结束并揭晓。
          </p>
          <p>
            线索涵盖人物的经历、作品、成就与典故，不限于本站已录入的史料。简单人物提前准备；困难人物首次遇到时可能需要等待生成，之后可以复用。会话保留一小时，刷新可恢复，服务重启后需重新开局。
          </p>
        </details>
      </header>
      {!game && setup}
      <div
        aria-live="polite"
        aria-busy={busy}
        className="text-sm text-teal-800"
      >
        {busy
          ? action === "start" && difficulty === "hard"
            ? "正在抽选人物；首次遇到的人物可能需要准备线索，请稍候…"
            : action === "hint"
              ? "正在打开下一条线索…"
              : action === "guess"
                ? "正在核对名字…"
                : "正在打开这一局…"
          : available === null
            ? "正在检查游戏服务…"
            : !available
              ? "线索题库暂未就绪。"
              : ""}
      </div>
      {error && (
        <p
          role="alert"
          className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-900"
        >
          {error}
        </p>
      )}
      {game && (
        <section className="reading-card space-y-6" aria-label="线索游戏进度">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif text-2xl">
              {game.outcome === "won"
                ? `你用 ${game.unlocked} 条线索猜中了！`
                : game.outcome
                  ? "答案揭晓"
                  : "这个人是谁？"}
            </h2>
            <span className="text-sm text-stone-500">
              {game.filters.difficulty === "easy" ? "简单" : "困难"} · 已看{" "}
              {game.unlocked}/{game.total} 条
            </span>
          </div>
          <ol className="space-y-3" aria-label="人物线索">
            {game.clues.map((_, i) => (
              <li
                key={i}
                className="rounded-xl border border-stone-200 bg-stone-50 p-4 md:p-5"
              >
                <div className="flex items-start gap-4">
                  <span className="font-serif text-xl leading-7 text-teal-700/60">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className="leading-7 flex-1">{game.clues[i]}</div>
                </div>
              </li>
            ))}
          </ol>
          {active && game.unlocked < game.total && (
            <p className="text-sm text-stone-400">
              还有 {game.total - game.unlocked} 条线索尚未解锁。
            </p>
          )}
          {active && (
            <>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!composition.current && text.trim())
                    void request(
                      "act",
                      { token, action: "guess", text: text.trim() },
                      "guess",
                    );
                }}
                className="space-y-3"
              >
                <label
                  htmlFor="clue-name"
                  className="block text-sm text-stone-600"
                >
                  想到是谁了吗？
                </label>
                <div className="flex gap-3">
                  <input
                    id="clue-name"
                    autoComplete="off"
                    maxLength={100}
                    disabled={busy}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onCompositionStart={() => {
                      composition.current = true;
                    }}
                    onCompositionEnd={() => {
                      composition.current = false;
                    }}
                    onKeyDown={(e) => {
                      if (
                        e.key === "Enter" &&
                        (e.nativeEvent.isComposing || composition.current)
                      )
                        e.preventDefault();
                    }}
                    placeholder="输入人物姓名或别名"
                    className="reading-input min-w-0 flex-1"
                  />
                  <button className={primary} disabled={busy || !text.trim()}>
                    猜一下
                  </button>
                </div>
              </form>
              {game.guesses.length > 0 && !game.guesses.at(-1)?.correct && (
                <p role="status" className="text-sm text-stone-600">
                  “{game.guesses.at(-1)?.text}
                  ”还没猜中。继续想想，或者再看一条。
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <button
                  type="button"
                  disabled={busy || game.unlocked === game.total}
                  className="rounded-lg border border-teal-700 px-5 py-3 text-teal-800 disabled:opacity-40"
                  onClick={() =>
                    void request(
                      "act",
                      {
                        token,
                        action: "hint",
                        expectedUnlocked: game.unlocked,
                      },
                      "hint",
                    )
                  }
                >
                  {game.unlocked === game.total
                    ? "全部线索已打开"
                    : `再看一条 · 第 ${game.unlocked + 1} 条`}
                </button>
                <button
                  type="button"
                  className="text-sm text-stone-500 underline disabled:opacity-40"
                  disabled={busy}
                  onClick={() =>
                    void request("act", { token, action: "state" }, "state")
                  }
                >
                  恢复当前进度
                </button>
              </div>
              <details className="text-sm text-stone-500">
                <summary className="cursor-pointer">
                  还没想到，想看看答案？
                </summary>
                <p className="mt-2">
                  揭晓后本局结束，可以查看其余线索和人物故事。
                </p>
                <button
                  type="button"
                  disabled={busy}
                  className="mt-2 underline text-amber-800"
                  onClick={() =>
                    void request("act", { token, action: "reveal" }, "reveal")
                  }
                >
                  结束并揭晓答案
                </button>
              </details>
            </>
          )}
          {game.person && (
            <section
              className="rounded-xl bg-teal-50 p-5 space-y-4"
              aria-label="人物揭晓"
            >
              <p className="eyebrow">
                {game.outcome === "won" ? "你认出了这段历史" : "从线索走向了解"}
              </p>
              <h3 className="font-serif text-3xl">{game.person.name}</h3>
              <p className="text-sm leading-7 text-stone-600">
                {game.person.description}
              </p>
              {game.person.id && (
                <div className="flex flex-wrap gap-4 text-sm text-teal-800">
                  <Link className="underline" to={`/people/${game.person.id}`}>
                    阅读人物资料 →
                  </Link>
                  <Link
                    className="underline"
                    to={`/evidence/person/${game.person.id}`}
                  >
                    本站已录入史料 →
                  </Link>
                </div>
              )}
              <details className="text-sm leading-7">
                <summary className="cursor-pointer">看看线索里的故事</summary>
                <p className="mt-2 text-stone-500">
                  历史通识线索，含 AI 整理内容。传说与文学形象会单独说明。
                </p>
                {game.evidence?.map((e, i) => (
                  <article
                    key={i}
                    className="border-t border-teal-100 pt-3 mt-3"
                  >
                    <p className="font-medium">
                      线索 {i + 1} · {e.title}
                    </p>
                    <p className="whitespace-pre-wrap text-stone-600">
                      {e.explanation}
                    </p>
                  </article>
                ))}
              </details>
            </section>
          )}
          {game.ratingEligible && (
            <section
              aria-label="难度评价"
              className="rounded-xl border border-stone-200 p-5 space-y-3"
            >
              <h3 className="font-medium">这个人物好猜吗？</h3>
              <p className="text-sm text-stone-500">
                参考本局的“
                {game.filters.difficulty === "easy" ? "简单" : "困难"}
                ”，你的感觉是：
              </p>
              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["easy", "太简单了"],
                    ["right", "刚刚好"],
                    ["hard", "太难了"],
                  ] as const
                ).map(([rating, label]) => (
                  <button
                    key={rating}
                    type="button"
                    disabled={busy || !!game.rating}
                    aria-pressed={game.rating === rating}
                    className={`rounded-full border px-4 py-2 text-sm disabled:cursor-default ${game.rating === rating ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 text-stone-600 disabled:opacity-50"}`}
                    onClick={() =>
                      void request("feedback", { token, rating }, "feedback")
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>
              {game.rating && (
                <p role="status" className="text-sm text-teal-800">
                  已收到，谢谢！评价会用于调整后续题目的难度。
                </p>
              )}
            </section>
          )}
          {game.guesses.length > 0 && (
            <details className="text-sm text-stone-500">
              <summary className="cursor-pointer">
                我猜过的名字（{game.guesses.length}）
              </summary>
              <ul className="mt-2 space-y-1">
                {game.guesses.map((g, i) => (
                  <li key={i}>
                    {g.text} · {g.correct ? "猜对了" : "还没猜中"}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
      )}
      {game?.outcome && setup}
    </div>
  );
}
