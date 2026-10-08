import { chromium } from "playwright";
import assert from "node:assert/strict";
const base = process.env.E2E_WEB_URL || "http://127.0.0.1:5186/histree/";
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const errors = [];
try {
  for (const viewport of [
    { width: 1280, height: 1000 },
    { width: 390, height: 844 },
  ]) {
    const ctx = await browser.newContext({ viewport });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(e.message));
    let state;
    let lastFilters;
    let revealCalls = 0;
    let expireNext = false;
    let failNext = false;
    const token = "a".repeat(64);
    await ctx.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin === new URL(base).origin && !url.pathname.startsWith("/api/v1/ask")) return route.continue();
      const reply = (body) =>
        route.fulfill({
          contentType: "application/json",
          body: JSON.stringify(body),
        });
      if (url.pathname.endsWith("/ask/session"))
        return reply({
          token: "test-anonymous-session",
          expires: Math.floor(Date.now() / 1000) + 86400,
        });
      if (
        url.pathname.includes("/ask/guess/") &&
        route.request().method() === "POST"
      )
        assert.equal(
          route.request().headers()["x-histree-anonymous"],
          "test-anonymous-session",
        );
      if (
        url.pathname.endsWith("/ask/guess/status") ||
        url.pathname.endsWith("/ask/status")
      )
        return reply({ available: true });
      if (url.pathname.endsWith("/ask/guess/start")) {
        lastFilters = route.request().postDataJSON();
        state = {
          filters: lastFilters,
          turns: [],
          hints: [],
          remaining: 30,
          outcome: null,
        };
        return reply({ token, ...state });
      }
      if (url.pathname.endsWith("/ask/guess/act")) {
        const body = route.request().postDataJSON();
        assert.equal(body.token, token);
        if (failNext) {
          failNext = false;
          await new Promise((resolve) => setTimeout(resolve, 500));
          return route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ message: "裁判暂时失败，请重试。" }),
          });
        }
        if (expireNext) {
          expireNext = false;
          return route.fulfill({
            status: 410,
            contentType: "application/json",
            body: JSON.stringify({ message: "游戏已过期，请重新开局。" }),
          });
        }
        if (
          body.action === "question" &&
          !["朱温", "朱全忠"].includes(body.text)
        ) {
          if (body.text.includes("哪个朝代"))
            return reply({
              ...state,
              notice:
                "请问一个是非问题，或提出一个人物名字；不能直接索要答案或候选名单。",
            });
          state.turns.push({ text: body.text, answer: "是", kind: "question" });
          state.remaining--;
        }
        if (body.action === "hint") state.hints.push("我曾在五代时期活动。");
        if (
          body.action === "guess" ||
          (body.action === "question" && ["朱温", "朱全忠"].includes(body.text))
        ) {
          const correct = ["朱温", "朱全忠"].includes(body.text);
          state.turns.push({
            text: body.text,
            answer: correct ? "猜对了" : "不是",
            kind: "guess",
          });
          state.remaining--;
          if (correct) state.outcome = "won";
        }
        if (body.action === "reveal") {
          revealCalls++;
          state.outcome = "revealed";
        }
        if (state.outcome) {
          state.person = {
            id: "p1",
            name: "朱温",
            description: "测试人物资料",
          };
          state.evidence = [
            {
              id: "c1",
              title: "测试史书",
              claim: "测试事实",
              note: "原文：测试引文",
              location: "测试卷",
            },
          ];
        }
        return reply(state);
      }
      return route.abort();
    });
    await page.goto(`${base}ask?mode=guess`);
    await page.getByRole("button", { name: "极难", exact: false }).click();
    await page.getByLabel("年代起点").fill("800");
    await page.getByLabel("年代终点").fill("960");
    await page.getByLabel("身份", { exact: true }).fill("将领");
    await page.getByLabel("性别", { exact: true }).selectOption("male");
    await page.getByLabel("自定义限定", { exact: true }).fill("与后唐有交集");
    await page.getByRole("button", { name: "随机开局" }).click();
    await page.getByRole("heading", { name: "我是谁？" }).waitFor();
    assert.deepEqual(lastFilters, {
      difficulty: 5,
      from: 800,
      to: 960,
      identity: "将领",
      gender: "male",
      custom: "与后唐有交集",
    });
    assert.equal(
      await page.getByRole("link", { name: "阅读人物资料 →" }).count(),
      0,
    );
    await page
      .getByLabel("问题或人物名字", { exact: true })
      .fill("你是哪个朝代的？");
    await page.getByRole("button", { name: "提交", exact: true }).click();
    await page
      .getByRole("status")
      .filter({ hasText: "请问一个是非问题" })
      .waitFor();
    assert.equal(state.turns.length, 0);
    assert.equal(
      await page.getByLabel("问题或人物名字", { exact: true }).inputValue(),
      "你是哪个朝代的？",
    );
    await page.getByText("本次操作未计入次数", { exact: true }).waitFor();
    const visibleFeedback = async (locator) => {
      await page.waitForFunction(
        (text) => {
          const element = [
            ...document.querySelectorAll('[role="status"], [role="alert"]'),
          ].find((e) =>
            e.textContent.replace(/\s/g, "").includes(text.replace(/\s/g, "")),
          );
          if (!element) return false;
          const rect = element.getBoundingClientRect();
          return rect.top >= 0 && rect.bottom <= innerHeight;
        },
        await locator.innerText(),
      );
    };
    await visibleFeedback(
      page.getByRole("status").filter({ hasText: "本次操作未计入次数" }),
    );
    for (let i = 1; i <= 9; i++) {
      await page
        .getByLabel("问题或人物名字", { exact: true })
        .fill(i === 9 ? "是姓李么？" : `第${i}个是非问题`);
      await page.getByRole("button", { name: "提交", exact: true }).click();
      await page.waitForFunction(
        (n) => document.querySelectorAll('[role="log"] > div').length === n,
        i,
      );
    }
    assert.equal(state.remaining, 21);
    await page
      .getByLabel("问题或人物名字", { exact: true })
      .fill("你是哪个朝代的？");
    await page.getByRole("button", { name: "提交", exact: true }).click();
    await page.getByText("本次操作未计入次数", { exact: true }).waitFor();
    await visibleFeedback(
      page.getByRole("status").filter({ hasText: "本次操作未计入次数" }),
    );
    assert.equal(state.turns.length, 9);
    failNext = true;
    await page
      .getByLabel("问题或人物名字", { exact: true })
      .fill("你是皇帝吗？");
    await page.getByRole("button", { name: "提交", exact: true }).click();
    await page
      .getByRole("button", { name: "正在处理…", exact: true })
      .waitFor();
    await page.getByRole("status").filter({ hasText: "正在核对" }).waitFor();
    await page.getByRole("alert").filter({ hasText: "裁判暂时失败" }).waitFor();
    await visibleFeedback(page.getByRole("alert"));
    assert.equal(
      await page.getByLabel("问题或人物名字", { exact: true }).inputValue(),
      "你是皇帝吗？",
    );
    assert.equal(state.turns.length, 9);
    await page
      .getByLabel("问题或人物名字", { exact: true })
      .fill("你生活在五代吗？");
    await page.getByRole("button", { name: "提交", exact: true }).click();
    await page
      .getByRole("log")
      .getByText("是", { exact: true })
      .last()
      .waitFor();
    await page.getByRole("button", { name: "领取提示 1" }).click();
    await page.getByText("提示 1：我曾在五代时期活动。").waitFor();
    await page.reload();
    await page
      .getByRole("log")
      .getByText("你生活在五代吗？", { exact: false })
      .waitFor();
    assert.equal(
      await page.getByRole("button", { name: "猜姓名", exact: true }).count(),
      0,
    );
    await page.getByLabel("问题或人物名字", { exact: true }).fill("朱全忠");
    await page.getByRole("button", { name: "提交" }).click();
    await page.getByRole("heading", { name: "你猜对了！" }).waitFor();
    assert.equal(
      await page
        .getByRole("link", { name: "阅读人物资料 →" })
        .getAttribute("href"),
      "/histree/people/p1",
    );
    assert.equal(
      await page
        .getByRole("link", { name: "查看人物图谱 →" })
        .getAttribute("href"),
      "/histree/graph/p1",
    );
    assert.equal(revealCalls, 0);
    await page.getByText("回看本局可用史料（1 条）").click();
    await page.getByText("原文：测试引文", { exact: true }).waitFor();
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      "mobile horizontal overflow",
    );
    await page.screenshot({
      path: `/tmp/histree-guess-${viewport.width}.png`,
      fullPage: true,
    });
    await page.getByRole("button", { name: "再开一局" }).click();
    await page.getByRole("heading", { name: "我是谁？" }).waitFor();
    expireNext = true;
    await page.getByRole("button", { name: "领取提示 1" }).click();
    await page
      .getByRole("alert")
      .getByText("游戏已过期，请重新开局。")
      .waitFor();
    await page.getByRole("button", { name: "随机开局" }).waitFor();
    assert.equal(
      await page.evaluate(() => sessionStorage.getItem("histree-guess-token")),
      null,
    );
    await ctx.close();
  }
  assert.deepEqual(errors, []);
  console.log(
    "Guess UI passed: desktop/mobile filters, refusal, question, hint, refresh, win, source and graph links; no premature reveal or overflow",
  );
} finally {
  await browser.close();
}
