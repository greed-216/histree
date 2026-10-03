import { chromium } from "playwright";
import assert from "node:assert/strict";
const base = process.env.E2E_WEB_URL || "http://127.0.0.1:5187/histree/";
const browser = await chromium.launch({ headless: true, channel: "chrome" });
try {
  const page = await browser.newPage();
  const errors = [];
  const questions = [];
  let sessions = 0;
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", async (route) => {
    const request = route.request(),
      url = new URL(request.url());
    if (url.origin === new URL(base).origin) return route.continue();
    assert.equal(
      url.origin,
      "https://gateway-test.supabase.co",
      "AI must never contact the compute host",
    );
    assert.ok(url.pathname.startsWith("/functions/v1/ai-gateway/"));
    const json = (data) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(data),
      });
    if (url.pathname.endsWith("/session")) {
      sessions++;
      return json({
        token: `anonymous-test-${sessions}`,
        expires: Math.floor(Date.now() / 1000) + 86400,
      });
    }
    if (url.pathname.endsWith("/status")) return json({ available: true });
    assert.equal(
      request.headers()["x-histree-anonymous"],
      `anonymous-test-${sessions}`,
    );
    assert.equal(request.headers()["x-histree-gateway-key"], undefined);
    const body = request.postDataJSON();
    questions.push(body);
    if (questions.length === 3)
      return route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ message: "匿名会话已过期" }),
      });
    return route.fulfill({
      contentType: "application/x-ndjson",
      body:
        [
          { type: "conversation", conversation: "a".repeat(64) },
          { type: "status", message: "正在读取史料" },
          {
            type: "result",
            answer: `网关测试回答${questions.length}`,
            insufficientEvidence: true,
            citations: [],
          },
        ]
          .map((x) => JSON.stringify(x))
          .join("\n") + "\n",
    });
  });
  await page.goto(base + "ask");
  const input = page.getByRole("textbox");
  await input.fill("朱温是谁？");
  await page
    .locator("form")
    .getByRole("button", { name: "查阅史料", exact: true })
    .click();
  await page.getByText("网关测试回答1", { exact: true }).waitFor();
  await input.fill("还有哪些史料？");
  await page
    .locator("form")
    .getByRole("button", { name: "查阅史料", exact: true })
    .click();
  await page.getByText("网关测试回答2", { exact: true }).waitFor();
  assert.equal(questions[1].conversation, "a".repeat(64));
  assert.equal(sessions, 1);
  await input.fill("测试过期会话");
  await page
    .locator("form")
    .getByRole("button", { name: "查阅史料", exact: true })
    .click();
  await page.getByRole("alert").filter({ hasText: "匿名会话已过期" }).waitFor();
  assert.equal(questions.length, 3, "failed operation must not be replayed");
  assert.equal(
    await page.evaluate(() =>
      localStorage.getItem("histree-anonymous-session-v1"),
    ),
    null,
  );
  await page.reload();
  await page.getByRole("textbox").fill("重新开始");
  await page
    .locator("form")
    .getByRole("button", { name: "查阅史料", exact: true })
    .click();
  await page.getByText("网关测试回答4", { exact: true }).waitFor();
  assert.equal(sessions, 2);
  assert.deepEqual(errors, []);
  console.log(
    "Browser gateway: Supabase-only requests, anonymous session reuse, NDJSON result and followup passed",
  );
} finally {
  await browser.close();
}
