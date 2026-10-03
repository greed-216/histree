import { supabase, supabaseAnonKey, supabaseUrl } from "../supabaseClient";

// Browsers know only the Supabase business entry point, never the compute host.
const base = supabaseUrl
  ? `${supabaseUrl.replace(/\/$/, "")}/functions/v1/ai-gateway`
  : "";
export const aiGatewayConfigured = Boolean(base && supabaseAnonKey);
const storageKey = "histree-anonymous-session-v1";
let anonymous: { token: string; expires: number } | undefined;
let pending: Promise<string> | undefined;

async function anonymousToken() {
  if (!anonymous) {
    try {
      anonymous =
        JSON.parse(localStorage.getItem(storageKey) || "null") || undefined;
    } catch {
      /* Storage may be unavailable. */
    }
  }
  if (
    anonymous &&
    typeof anonymous.token === "string" &&
    anonymous.expires > Date.now() / 1000 + 60
  )
    return anonymous.token;
  if (!pending) {
    pending = (async () => {
      const response = await fetch(`${base}/session`, {
        method: "POST",
        headers: { apikey: supabaseAnonKey! },
        signal: AbortSignal.timeout(15000),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.message || "匿名会话未能建立，请稍后重试");
      if (typeof data.token !== "string" || !Number.isFinite(data.expires))
        throw new Error("匿名会话未能建立");
      anonymous = { token: data.token, expires: data.expires };
      try {
        localStorage.setItem(storageKey, JSON.stringify(anonymous));
      } catch {
        /* Keep the in-memory session. */
      }
      return anonymous.token;
    })().finally(() => {
      pending = undefined;
    });
  }
  return pending;
}
export async function aiGatewayFetch(path: string, options: RequestInit = {}) {
  if (!aiGatewayConfigured) throw new Error("AI 服务尚未配置");
  const headers = new Headers({ apikey: supabaseAnonKey! });
  if (options.body !== undefined)
    headers.set("Content-Type", "application/json");
  if ((options.method || "GET").toUpperCase() === "POST") {
    options.signal?.throwIfAborted();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token)
      headers.set("Authorization", `Bearer ${session.access_token}`);
    else headers.set("x-histree-anonymous", await anonymousToken());
    options.signal?.throwIfAborted();
  }
  // No automatic retries: a disconnected model request may already have incurred cost.
  return fetch(`${base}${path}`, { ...options, headers });
}
