import { createGateway } from "./gateway.ts";

const required = (name: string) => {
  const value = Deno.env.get(name);
  if (!value) throw new Error(`Missing ${name}`);
  return value;
};
const supabaseUrl = required("SUPABASE_URL");
const serviceKey = required("SUPABASE_SERVICE_ROLE_KEY");
const publicKey = required("SUPABASE_ANON_KEY");
Deno.serve(createGateway({
  upstream: required("HISTREE_ECS_API_URL"),
  secret: required("HISTREE_GATEWAY_SECRET"),
  origins:
    (Deno.env.get("HISTREE_ALLOWED_ORIGINS") || "https://greed-216.github.io")
      .split(",").map((s) => s.trim()).filter(Boolean),
  localDevelopment: Deno.env.get("HISTREE_LOCAL_DEV") === "true",
  allowAnonymous: Deno.env.get("HISTREE_ALLOW_ANONYMOUS") !== "false",
}, {
  fetch,
  async verifyUser(token, signal) {
    const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: { apikey: publicKey, Authorization: `Bearer ${token}` },
      signal,
    });
    if (!response.ok) return null;
    return (await response.json()).id || null;
  },
  async consumeQuota(actor, operation, signal) {
    const response = await fetch(
      `${supabaseUrl}/rest/v1/rpc/consume_ai_gateway_quota`,
      {
        method: "POST",
        headers: {
          apikey: serviceKey,
          Authorization: `Bearer ${serviceKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ p_actor: actor, p_operation: operation }),
        signal,
      },
    );
    if (!response.ok) throw new Error("Quota unavailable");
    return await response.json() === true;
  },
}));
