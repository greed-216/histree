export type GatewayConfig = {
  upstream: string;
  secret: string;
  origins: string[];
  allowAnonymous: boolean;
  localDevelopment?: boolean;
  upstreamHeadersTimeoutMs?: number;
};
export type GatewayDependencies = {
  verifyUser: (token: string, signal: AbortSignal) => Promise<string | null>;
  consumeQuota: (
    actor: string,
    operation: string,
    signal: AbortSignal,
  ) => Promise<boolean>;
  fetch: typeof fetch;
};
const encoder = new TextEncoder();
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const hex = (bytes: ArrayBuffer) =>
  Array.from(new Uint8Array(bytes), (b) => b.toString(16).padStart(2, "0"))
    .join("");

export function createGateway(
  config: GatewayConfig,
  deps: GatewayDependencies,
) {
  const headersTimeoutMs = config.upstreamHeadersTimeoutMs ?? 15000;
  if (
    !Number.isInteger(headersTimeoutMs) || headersTimeoutMs < 1 ||
    headersTimeoutMs > 15000
  ) {
    throw new Error("Invalid upstream headers timeout");
  }
  const upstream = new URL(config.upstream);
  if (
    upstream.protocol !== "https:" &&
    !(upstream.protocol === "http:" && config.localDevelopment &&
      ["localhost", "127.0.0.1", "host.docker.internal"].includes(
        upstream.hostname,
      ))
  ) throw new Error("HTTPS upstream required");
  if (
    upstream.username || upstream.password || upstream.search ||
    upstream.hash || config.secret.length < 32
  ) throw new Error("Invalid gateway configuration");
  const key = crypto.subtle.importKey(
    "raw",
    encoder.encode(config.secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
  const sign = async (payload: string) =>
    hex(
      await crypto.subtle.sign(
        "HMAC",
        await key,
        encoder.encode(`histree-anonymous:${payload}`),
      ),
    );
  const anonymous = async (token: string | null) => {
    if (!token || !/^[a-f0-9]{64}\.[0-9]{10}\.[a-f0-9]{64}$/.test(token)) {
      return null;
    }
    const [id, expiry, signature] = token.split(".");
    if (
      Number(expiry) <= Date.now() / 1000 ||
      Number(expiry) > Date.now() / 1000 + 86460
    ) return null;
    const bytes = Uint8Array.from(
      signature.match(/../g)!,
      (s) => parseInt(s, 16),
    );
    return await crypto.subtle.verify(
        "HMAC",
        await key,
        bytes,
        encoder.encode(`histree-anonymous:${id}.${expiry}`),
      )
      ? `anon:${id}`
      : null;
  };
  return async (request: Request): Promise<Response> => {
    const origin = request.headers.get("origin");
    const headers = new Headers({
      "Cache-Control": "no-store",
      "Vary": "Origin",
      "X-Content-Type-Options": "nosniff",
    });
    const json = (status: number, message: string) =>
      Response.json({ message }, { status, headers });
    if (origin && !config.origins.includes(origin)) {
      return json(403, "不允许此来源访问");
    }
    if (origin) headers.set("Access-Control-Allow-Origin", origin);
    headers.set(
      "Access-Control-Allow-Headers",
      "authorization, apikey, content-type, x-client-info, x-histree-anonymous",
    );
    headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers });
    }
    const url = new URL(request.url);
    const prefix = url.pathname.startsWith("/functions/v1/ai-gateway/")
      ? "/functions/v1/ai-gateway"
      : url.pathname.startsWith("/ai-gateway/")
      ? "/ai-gateway"
      : null;
    if (!prefix) return json(404, "接口不存在");
    const path = url.pathname.slice(prefix.length);
    const routes: Record<string, string> = {
      "/ask": "POST",
      "/ask/status": "GET",
      "/ask/guess/status": "GET",
      "/ask/guess/start": "POST",
      "/ask/guess/act": "POST",
      "/session": "POST",
    };
    if (!Object.hasOwn(routes, path) || url.search) {
      return json(404, "接口不存在");
    }
    if (request.method !== routes[path]) return json(405, "不支持此请求方法");
    const requestId = crypto.randomUUID();
    headers.set("X-Histree-Request-Id", requestId);
    const started = Date.now();
    let stage = "identity";
    let headersTimedOut = false;
    const deadline = AbortSignal.timeout(130000);
    const upstreamAbort = new AbortController();
    const signal = AbortSignal.any([
      request.signal,
      deadline,
      upstreamAbort.signal,
    ]);
    try {
      let actor: string | null = null;
      let body: string | undefined;
      if (request.method === "POST") {
        const authorization = request.headers.get("authorization");
        if (authorization) {
          if (!authorization.startsWith("Bearer ")) {
            return json(401, "登录凭据无效");
          }
          const user = await deps.verifyUser(authorization.slice(7), signal);
          if (!user || !uuid.test(user)) {
            return json(401, "登录已过期，请重新登录");
          }
          actor = `user:${user}`;
        }
        if (path === "/session") {
          if (!config.allowAnonymous) return json(401, "请先登录");
          const id = hex(crypto.getRandomValues(new Uint8Array(32)).buffer);
          stage = "quota";
          if (!await deps.consumeQuota(`anon:${id}`, "session", signal)) {
            return json(429, "当前访问较多，请稍后再试");
          }
          const expires = Math.floor(Date.now() / 1000) + 86400;
          const payload = `${id}.${expires}`;
          return Response.json({
            token: `${payload}.${await sign(payload)}`,
            expires,
          }, { headers });
        }
        if (!actor && config.allowAnonymous) {
          actor = await anonymous(request.headers.get("x-histree-anonymous"));
        }
        if (!actor) {
          return json(
            401,
            config.allowAnonymous ? "匿名会话已过期，请刷新后重试" : "请先登录",
          );
        }
        if (
          !(request.headers.get("content-type") || "").toLowerCase().startsWith(
            "application/json",
          )
        ) return json(415, "请使用 JSON 请求");
        const reader = request.body?.getReader();
        if (!reader) return json(400, "请求不能为空");
        const chunks: Uint8Array[] = [];
        let size = 0;
        const cancelBody = () => {
          void reader.cancel().catch(() => {});
        };
        signal.addEventListener("abort", cancelBody, { once: true });
        try {
          for (;;) {
            signal.throwIfAborted();
            const { done, value } = await reader.read();
            if (done) break;
            size += value.byteLength;
            if (size > 16384) {
              await reader.cancel();
              return json(413, "请求过长");
            }
            chunks.push(value);
          }
        } finally {
          signal.removeEventListener("abort", cancelBody);
          reader.releaseLock();
        }
        signal.throwIfAborted();
        const bytes = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) {
          bytes.set(chunk, offset);
          offset += chunk.length;
        }
        body = new TextDecoder().decode(bytes);
        let parsed: unknown;
        try {
          parsed = JSON.parse(body);
        } catch {
          return json(400, "JSON 格式错误");
        }
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          return json(400, "无效请求");
        }
        stage = "quota";
        if (
          !await deps.consumeQuota(
            actor,
            path === "/ask" ? "ask" : "guess",
            signal,
          )
        ) return json(429, "已达到调用限额，请稍后再试");
      }
      // Construct headers from scratch: browser credentials and identity headers never reach ECS.
      const upstreamHeaders = new Headers({
        "x-histree-gateway-key": config.secret,
        "x-histree-request-id": requestId,
      });
      if (actor) upstreamHeaders.set("x-histree-actor", actor);
      if (body !== undefined) {
        upstreamHeaders.set("Content-Type", "application/json");
      }
      stage = "upstream";
      console.log(
        JSON.stringify({
          event: "upstream_start",
          requestId,
          path,
          bytes: body === undefined ? 0 : encoder.encode(body).byteLength,
        }),
      );
      const headersAbort = new AbortController();
      const headersTimer = setTimeout(() => {
        headersTimedOut = true;
        headersAbort.abort(
          new DOMException(
            "Upstream response headers timed out",
            "TimeoutError",
          ),
        );
      }, headersTimeoutMs);
      let response: Response;
      try {
        response = await deps.fetch(
          `${config.upstream.replace(/\/$/, "")}${path}`,
          {
            method: request.method,
            headers: upstreamHeaders,
            body,
            signal: AbortSignal.any([signal, headersAbort.signal]),
            redirect: "error",
          },
        );
      } finally {
        // Once headers arrive, keep the full streaming deadline instead.
        clearTimeout(headersTimer);
      }
      console.log(
        JSON.stringify({
          event: "upstream_headers",
          requestId,
          path,
          status: response.status,
          elapsedMs: Date.now() - started,
        }),
      );
      headers.set(
        "Content-Type",
        response.headers.get("content-type") || "application/json",
      );
      headers.set("X-Accel-Buffering", "no");
      // Pass through the stream; no buffering and no retries of paid operations.
      const reader = response.body?.getReader();
      if (!reader) {
        return new Response(null, { status: response.status, headers });
      }
      const abort = () => {
        void reader.cancel().catch(() => {});
      };
      signal.addEventListener("abort", abort, { once: true });
      const stream = new ReadableStream<Uint8Array>({
        async pull(out) {
          try {
            if (signal.aborted) throw signal.reason || new Error("Cancelled");
            const { done, value } = await reader.read();
            if (done) {
              signal.removeEventListener("abort", abort);
              reader.releaseLock();
              out.close();
            } else out.enqueue(value);
          } catch (error) {
            signal.removeEventListener("abort", abort);
            out.error(error);
          }
        },
        async cancel(reason) {
          signal.removeEventListener("abort", abort);
          upstreamAbort.abort(reason);
          await reader.cancel(reason);
        },
      });
      return new Response(stream, { status: response.status, headers });
    } catch (error) {
      console.error(
        JSON.stringify({
          event: "gateway_error",
          requestId,
          path,
          stage,
          error: error instanceof Error ? error.name : "unknown",
          deadline: deadline.aborted,
          headersTimedOut,
          elapsedMs: Date.now() - started,
        }),
      );
      return json(
        deadline.aborted || headersTimedOut ? 504 : 503,
        deadline.aborted || headersTimedOut
          ? "等待回复超时，请稍后重试"
          : "服务暂时无法连接，请稍后重试",
      );
    }
  };
}
