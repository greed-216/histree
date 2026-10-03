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
  const res = await fetch(`${base}/ask/guess/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new GuessRequestError(
      data.message || `游戏请求失败（${res.status}）`,
      res.status,
    );
  return data;
}
export async function guessStatus(signal: AbortSignal): Promise<boolean> {
  if (!base) return false;
  const res = await fetch(`${base}/ask/guess/status`, { signal });
  if (!res.ok) return false;
  return Boolean((await res.json()).available);
}
