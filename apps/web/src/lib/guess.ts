import { aiGatewayConfigured, aiGatewayFetch } from "./aiGateway";
export type GuessFilters = {
  difficulty: "easy" | "hard" | number;
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
  ratingEligible?: boolean;
  rating?: "easy" | "right" | "hard" | null;
  person?: { id: string | null; name: string; description?: string };
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
export async function guessRequest(
  path: "start" | "act" | "feedback",
  body: unknown,
  signal: AbortSignal,
): Promise<GuessState> {
  if (!aiGatewayConfigured) throw new Error("猜人物服务尚未开放。");
  const timeout = AbortSignal.timeout(140000);
  let res: Response;
  try {
    res = await aiGatewayFetch(`/ask/guess/${path}`, {
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
  if (!aiGatewayConfigured) return false;
  const res = await aiGatewayFetch("/ask/guess/status", { signal });
  if (!res.ok) return false;
  return Boolean((await res.json()).available);
}

export type ClueState = {
  token?: string;
  filters: { difficulty: "easy" | "hard"; from?: number; to?: number };
  clues: string[];
  unlocked: number;
  total: number;
  guesses: Array<{ text: string; correct: boolean }>;
  outcome: "won" | "revealed" | null;
  ratingEligible?: boolean;
  rating?: "easy" | "right" | "hard" | null;
  person?: { id: string | null; name: string; description?: string };
  evidence?: Array<{
    clue: string;
    explanation: string;
    kind: "general_knowledge";
    title: string;
  }>;
};
export async function clueRequest(
  path: "start" | "act" | "feedback",
  body: unknown,
  signal: AbortSignal,
  onProgress?: (message: string) => void,
): Promise<ClueState> {
  const timeout = AbortSignal.timeout(140000);
  let res: Response;
  try {
    res = await aiGatewayFetch(`/ask/guess/clues/${path}`, {
      method: "POST",
      headers:
        path === "start" ? { Accept: "application/x-ndjson" } : undefined,
      body: JSON.stringify(body),
      signal: AbortSignal.any([signal, timeout]),
    });
  } catch (error) {
    if (timeout.aborted && !signal.aborted)
      throw new Error("准备线索超时，请稍后重试；已完成的准备会保留。");
    throw error;
  }
  let data;
  if (
    res.ok &&
    res.headers.get("content-type")?.includes("application/x-ndjson")
  ) {
    if (!res.body) throw new Error("开局连接未建立，请重试。");
    const reader = res.body.getReader(),
      decoder = new TextDecoder();
    let buffer = "",
      completed = false;
    const consume = (line: string) => {
      if (!line.trim()) return;
      const event = JSON.parse(line);
      if (event.type === "status" && typeof event.message === "string")
        onProgress?.(event.message);
      if (event.type === "error")
        throw new GuessRequestError(event.message, event.status || 503);
      if (event.type === "result") {
        data = event.state;
        completed = true;
      }
    };
    try {
      for (;;) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        if (buffer.length > 100000)
          throw new Error("开局返回内容异常，请重试。");
        let end;
        while ((end = buffer.indexOf("\n")) >= 0) {
          consume(buffer.slice(0, end));
          buffer = buffer.slice(end + 1);
        }
        if (done) {
          consume(buffer);
          break;
        }
      }
      if (!completed)
        throw new Error("开局连接中断，完成的线索会保留，请重试。");
    } finally {
      await reader.cancel().catch(() => {});
      reader.releaseLock();
    }
  } else data = await res.json().catch(() => null);
  if (!res.ok)
    throw new GuessRequestError(
      data?.message || `游戏请求失败（${res.status}）`,
      res.status,
    );
  if (
    !data?.filters ||
    !Array.isArray(data.clues) ||
    !Array.isArray(data.guesses) ||
    !Number.isInteger(data.unlocked) ||
    !Number.isInteger(data.total)
  )
    throw new Error("游戏未返回完整线索，请重试或恢复进度。");
  return data;
}
export async function clueStatus(signal: AbortSignal): Promise<boolean> {
  const res = await aiGatewayFetch("/ask/guess/clues/status", { signal });
  return res.ok && Boolean((await res.json()).available);
}
