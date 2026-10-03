import { createGateway, type GatewayDependencies } from "./gateway.ts";
const check = (value: unknown, message = "assertion failed") => {
  if (!value) throw new Error(message);
};
const secret = "a".repeat(64);
function fixture(allowAnonymous = true) {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const quotas: Array<[string, string]> = [];
  const deps: GatewayDependencies = {
    verifyUser: async (token) =>
      token === "valid-user" ? "12345678-1234-1234-1234-123456789abc" : null,
    consumeQuota: async (actor, operation) => {
      quotas.push([actor, operation]);
      return true;
    },
    fetch: (async (url: string | URL | Request, init: RequestInit) => {
      calls.push({ url: String(url), init });
      return Response.json({ available: true });
    }) as typeof fetch,
  };
  const handler = createGateway({
    upstream: "https://compute.test/api/v1",
    secret,
    origins: ["https://greed-216.github.io"],
    allowAnonymous,
  }, deps);
  const request = (path: string, init: RequestInit = {}) =>
    handler(
      new Request(
        `https://project.supabase.co/functions/v1/ai-gateway${path}`,
        init,
      ),
    );
  return { deps, calls, quotas, request };
}
async function session(f: ReturnType<typeof fixture>) {
  const r = await f.request("/session", { method: "POST" });
  check(r.ok);
  return (await r.json()).token as string;
}
Deno.test("route allowlist, origins, preflight and method checks do not reach ECS", async () => {
  const f = fixture();
  check(
    (await f.request("/ask", {
      method: "OPTIONS",
      headers: { origin: "https://greed-216.github.io" },
    })).status === 204,
  );
  check(
    (await f.request("/ask/status", {
      headers: { origin: "https://evil.test" },
    })).status === 403,
  );
  check((await f.request("/../admin")).status === 404);
  check(
    (await f.request("/ask/status?target=https://evil.test")).status === 404,
  );
  check((await f.request("/ask")).status === 405);
  check(f.calls.length === 0);
});
Deno.test("signed anonymous sessions are separate and forged or expired tokens are refused", async () => {
  const f = fixture(), a = await session(f), b = await session(f);
  check(a !== b);
  const post = (token: string) =>
    f.request("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-histree-anonymous": token,
      },
      body: '{"question":"hello"}',
    });
  const ok = await post(a);
  check(ok.ok);
  await ok.text();
  const h = new Headers(f.calls[0].init.headers);
  check(h.get("x-histree-actor") === `anon:${a.split(".")[0]}`);
  check(
    (await post(a.slice(0, -1) + (a.endsWith("0") ? "1" : "0"))).status === 401,
  );
  check((await post(a.replace(a.split(".")[1], "1000000000"))).status === 401);
  check((await post("anonymous")).status === 401);
  check(f.calls.length === 1);
});
Deno.test("user JWTs are verified; client-supplied actor and service headers are discarded", async () => {
  const f = fixture();
  const request = (token: string) =>
    f.request("/ask/guess/act", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "x-histree-actor": "user:attacker",
        "x-histree-gateway-key": "forged",
        "x-forwarded-for": "forged",
      },
      body: '{"action":"state"}',
    });
  const r = await request("valid-user");
  check(r.ok);
  await r.text();
  const h = new Headers(f.calls[0].init.headers);
  check(h.get("x-histree-gateway-key") === secret);
  check(
    h.get("x-histree-actor") === "user:12345678-1234-1234-1234-123456789abc",
  );
  check(!h.has("authorization") && !h.has("x-forwarded-for"));
  check((await request("bad-user")).status === 401);
  check(f.quotas.length === 1);
});
Deno.test("authenticated-only switch and quotas fail closed, with bounded request bodies", async () => {
  const closed = fixture(false);
  check((await closed.request("/session", { method: "POST" })).status === 401);
  const f = fixture(), token = await session(f);
  const post = (body: string) =>
    f.request("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-histree-anonymous": token,
      },
      body,
    });
  check((await post("x".repeat(17000))).status === 413);
  check((await post("broken")).status === 400);
  f.deps.consumeQuota = async () => false;
  check((await post("{}")).status === 429);
  f.deps.consumeQuota = async () => {
    throw new Error("db unavailable");
  };
  check((await post("{}")).status === 503);
  check(f.calls.length === 0);
});
Deno.test("NDJSON is streamed before completion and downstream cancellation cancels upstream", async () => {
  const f = fixture();
  let source!: ReadableStreamDefaultController<Uint8Array>;
  let cancelled = false;
  f.deps.fetch = (async () =>
    new Response(
      new ReadableStream<Uint8Array>({
        start(c) {
          source = c;
          c.enqueue(new TextEncoder().encode('{"type":"status"}\n'));
        },
        cancel() {
          cancelled = true;
        },
      }),
      { headers: { "Content-Type": "application/x-ndjson" } },
    )) as typeof fetch;
  const r = await f.request("/ask/status");
  const reader = r.body!.getReader();
  check(
    new TextDecoder().decode((await reader.read()).value).includes("status"),
  );
  check(!cancelled);
  await reader.cancel();
  check(cancelled);
  void source;
});
Deno.test("upstream status survives and redirects cannot leak the service secret", async () => {
  const f = fixture();
  f.deps.fetch = (async (_url, init) => {
    check(init?.redirect === "error");
    return Response.json({ message: "busy" }, { status: 429 });
  }) as typeof fetch;
  const r = await f.request("/ask/status");
  check(r.status === 429);
  check((await r.json()).message === "busy");
});
