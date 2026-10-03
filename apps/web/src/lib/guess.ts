export type GuessFilters = {
  difficulty: number;
  from?: number;
  to?: number;
  identity: string;
  gender: string;
  custom: string;
};
export type GuessState = {
  token?: string;
  filters: GuessFilters;
  turns: Array<{ text: string; answer: string; kind: "question" | "guess" }>;
  hints: string[];
  remaining: number;
  outcome: "won" | "revealed" | "limit" | null;
  notice?: string;
  person?: { id: string; name: string; description?: string };
  evidence?: Array<{
    id: string;
    claim: string;
    note?: string;
    title?: string;
    location?: string;
  }>;
};
export class GuessRequestError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}
const base = (
  import.meta.env.VITE_ASK_API_URL ||
  import.meta.env.VITE_API_URL ||
  ""
).replace(/\/$/, "");
export async function guessRequest(
  path: "start" | "act",
  body: unknown,
  signal: AbortSignal,
): Promise<GuessState> {
  if (!base) throw new Error("猜人物服务尚未开放。");
  const timeout = AbortSignal.timeout(160000);
  let res: Response;
  try {
    res = await fetch(`${base}/ask/guess/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.any([signal, timeout]),
    });
  } catch (err) {
    if (timeout.aborted && !signal.aborted)
      throw new Error("等待回复超时，请重试；也可以刷新恢复游戏状态。");
    throw err;
  }
  const data = await res.json().catch(() => null);
  if (!res.ok)
    throw new GuessRequestError(
      data?.message || `游戏请求失败（${res.status}）`,
      res.status,
    );
  if (
    !data?.filters ||
    !Array.isArray(data.turns) ||
    !Array.isArray(data.hints) ||
    typeof data.remaining !== "number"
  )
    throw new Error("游戏服务未返回完整回复，请重试；也可以刷新恢复游戏状态。");
  return data;
}
export async function guessStatus(signal: AbortSignal): Promise<boolean> {
  if (!base) return false;
  const res = await fetch(`${base}/ask/guess/status`, { signal });
  if (!res.ok) return false;
  return Boolean((await res.json()).available);
}
