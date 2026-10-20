import { useSearchParams } from "react-router-dom";
import { ClueGuessGame } from "./ClueGuessGame";
import { QuestionGuessGame } from "./QuestionGuessGame";

export function GuessGame() {
  const [params, setParams] = useSearchParams();
  const mode = params.get("play") === "questions" ? "questions" : "clues";
  return (
    <div className="space-y-5">
      <nav className="mx-auto max-w-4xl flex gap-2" aria-label="猜人物玩法">
        {(
          [
            ["clues", "线索模式"],
            ["questions", "提问模式"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            aria-pressed={mode === value}
            onClick={() =>
              setParams((p) => {
                const next = new URLSearchParams(p);
                next.set("play", value);
                return next;
              })
            }
            className={`rounded-full border px-5 py-2 text-sm ${mode === value ? "border-teal-800 bg-teal-800 text-white" : "border-stone-200 bg-white text-stone-600"}`}
          >
            {label}
          </button>
        ))}
      </nav>
      {mode === "clues" ? <ClueGuessGame /> : <QuestionGuessGame />}
    </div>
  );
}
