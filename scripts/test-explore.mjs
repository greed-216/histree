import {tmpdir} from 'node:os';
import {join} from 'node:path';
import { PGlite } from "@electric-sql/pglite";
import { pg_trgm } from "@electric-sql/pglite/contrib/pg_trgm";
import { readdir, readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const db = new PGlite({ extensions: { pg_trgm } });
await db.exec(`CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY);
 CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
 CREATE ROLE service_role; CREATE ROLE anon; CREATE ROLE authenticated; GRANT USAGE ON SCHEMA public,auth TO anon,authenticated;`);
for (const file of (
  await readdir(new URL("../supabase/migrations/", import.meta.url))
)
  .filter((f) => f.endsWith(".sql"))
  .sort())
  await db.exec(
    await readFile(
      new URL(`../supabase/migrations/${file}`, import.meta.url),
      "utf8",
    ),
  );
await db.exec(`GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon,authenticated;
 INSERT INTO person(id,name,aliases,era,tags,description,status)
 SELECT md5('person-'||i)::uuid,'测试人物'||lpad(i::text,4,'0'), ARRAY['别名'||i], '虚构时代',ARRAY['检索标签'],repeat('简介',500),'published' FROM generate_series(1,1500) i;
 UPDATE person SET name='百分%下划_线',aliases=ARRAY['百分别名'] WHERE id=md5('person-1500')::uuid;
 INSERT INTO person(id,name,aliases,status) VALUES(md5('draft')::uuid,'草稿人物',ARRAY['隐藏别名'],'draft');
 INSERT INTO event(id,title,start_year,end_year,status) VALUES(md5('event-1')::uuid,'测试战役',900,905,'published'),(md5('event-2')::uuid,'测试事件',910,910,'published');
 INSERT INTO topic(slug,title,description,status) VALUES('fixture-topic','测试专题','虚构专题内容','published');
 INSERT INTO person_relationship(id,person_a,person_b,relation_type,status)
 SELECT md5('star-'||i)::uuid,md5('person-1')::uuid,md5('person-'||i)::uuid,'兄弟','published' FROM generate_series(2,160) i;
 INSERT INTO person_relationship(id,person_a,person_b,relation_type,status) VALUES
 (md5('chain-1')::uuid,md5('person-1000')::uuid,md5('person-1001')::uuid,'父亲','published'),
 (md5('chain-2')::uuid,md5('person-1001')::uuid,md5('person-1002')::uuid,'父亲','published'),
 (md5('draft-edge')::uuid,md5('person-1000')::uuid,md5('draft')::uuid,'兄弟','published');
 INSERT INTO person_event(person_id,event_id,role,status) VALUES
 (md5('person-1000')::uuid,md5('event-1')::uuid,'参与','published'),
 (md5('person-1000')::uuid,md5('event-2')::uuid,'参与','published'),
 (md5('person-1001')::uuid,md5('event-1')::uuid,'参与','published');
 INSERT INTO person_relationship(id,person_a,person_b,relation_type,status)
 SELECT md5('dense-'||a||'-'||b)::uuid,md5('person-'||a)::uuid,md5('person-'||b)::uuid,'兄弟','published'
 FROM generate_series(1200,1230) a CROSS JOIN generate_series(1200,1230) b WHERE a<b;
 ANALYZE; SET ROLE anon;`);
const scalar = async (sql, args = []) =>
  Object.values((await db.query(sql, args)).rows[0])[0];
const search = (q = "", kind = "all", page = 0, limit = 20) =>
  scalar("SELECT public.search_entries($1,$2,$3,$4)", [q, kind, page, limit]);
const graph = (id, mode = "people", depth = 1, from = null, to = null) =>
  scalar("SELECT public.graph_slice($1::uuid,$2,$3,$4,$5)", [
    id,
    mode,
    depth,
    from,
    to,
  ]);
const id = (n) => scalar("SELECT md5($1)::uuid", [n]);
const p1000 = await id("person-1000"),
  p1001 = await id("person-1001"),
  p1002 = await id("person-1002"),
  draft = await id("draft");
assert.equal(
  (await search("别名1499")).items[0].name,
  "测试人物1499",
  "Search must reach records beyond the default REST 1000-row limit",
);
assert.equal((await search("%")).items.length, 1, "Percent is a literal");
assert.equal((await search("_")).items.length, 1, "Underscore is a literal");
assert.equal((await search("\\")).items.length, 0, "Backslash is a literal");
assert.equal((await search("隐藏别名")).items.length, 0);
assert.equal((await search("测试战役", "event")).items[0].type, "event");
assert.equal((await search("测试专题", "topic")).items[0].type, "topic");
assert.equal((await search("检索标签", "person")).items.length, 20);
assert.equal(
  (await search("别名149")).items[0].name,
  "测试人物0149",
  "Exact alias ranks above partial alias",
);
const ids = new Set();
let page = 0;
for (;;) {
  const result = await search("", "person", page++);
  assert.ok(result.items.length <= 20);
  for (const item of result.items) {
    assert.ok(!ids.has(item.id), "Pagination must not duplicate IDs");
    ids.add(item.id);
  }
  if (!result.has_more) break;
}
assert.equal(ids.size, 1500);
assert.equal(page, 75);
const first = await graph(p1000),
  second = await graph(p1000, "people", 2);
assert.deepEqual(
  new Set(first.nodes.map((n) => n.id)),
  new Set([p1000, p1001]),
);
assert.deepEqual(
  new Set(second.nodes.map((n) => n.id)),
  new Set([p1000, p1001, p1002]),
);
assert.equal(first.edges[0].source, p1000, "Direction is preserved");
assert.equal(first.edges[0].subject_table, "person_relationship");
const eventGraph = await graph(p1000, "events", 2);
assert.ok(eventGraph.nodes.some((n) => n.id === p1001));
assert.ok(eventGraph.edges.every((e) => e.subject_table === "person_event"));
const limited = await graph(await id("person-1"), "people", 2);
assert.equal(limited.nodes.length, 120);
assert.equal(limited.truncated, true);
assert.ok(limited.edges.length <= 300);
const visible = new Set(limited.nodes.map((n) => n.id));
assert.ok(
  limited.edges.every((e) => visible.has(e.source) && visible.has(e.target)),
);
assert.ok(
  JSON.stringify(limited).length < 200000,
  "Graph uses summary fields rather than biographies",
);
assert.equal(
  (await graph(p1000, "events", 1, 906, 909)).nodes.length,
  1,
  "Year filter applies before expansion",
);
const dense = await graph(await id("person-1200"), "people", 2);
assert.equal(dense.edges.length, 300);
assert.equal(dense.truncated, true);
assert.equal(await graph(draft), null);
assert.equal(await scalar("SELECT public.entry_detail($1)", [draft]), null);
assert.equal(
  (await scalar("SELECT public.entry_detail($1)", [p1000])).description.length,
  1000,
  "Selected detail retains full text",
);
await assert.rejects(search("x", "invalid"));
await assert.rejects(search("x", "all", -1));
await assert.rejects(search("x".repeat(201)));
await assert.rejects(graph(p1000, "people", 3));
await assert.rejects(graph(p1000, "events", 1, 910, 900));
// Even an editor with RLS privileges receives only published data from public RPCs.
await db.exec(
  `RESET ROLE; INSERT INTO auth.users VALUES('${draft}'); INSERT INTO user_roles(user_id,role) VALUES('${draft}','admin'); SET ROLE authenticated; SELECT set_config('request.jwt.claim.sub','${draft}',false);`,
);
assert.equal((await search("隐藏别名")).items.length, 0);
assert.equal(await graph(draft), null);
await db.exec(
  `RESET ROLE; SELECT set_config('request.jwt.claim.sub','',false); SET ROLE anon;`,
);
// All directory, section, evidence, and admin reads are bounded and complete.
await db.exec(`RESET ROLE;
 UPDATE topic SET sections=jsonb_build_array(jsonb_build_object('heading','关联条目','body','虚构测试','node_ids',jsonb_build_array('${p1002}','${p1000}','${p1001}'))) WHERE slug='fixture-topic';
 INSERT INTO source(id,title,source_type) VALUES(md5('source-fixture')::uuid,'测试出处','primary');
 INSERT INTO fact_claim(id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status)
 SELECT md5('claim-'||i)::uuid,'person',md5('person-1000')::uuid,'biography','测试依据'||i,md5('source-fixture')::uuid,'卷一 段'||i,'原文：虚构原文；核对说明：测试','published' FROM generate_series(1,1205) i;
 UPDATE fact_claim SET note=NULL WHERE id=md5('claim-1205')::uuid;
 INSERT INTO fact_claim(subject_table,subject_id,field_path,claim_text,source_id,citation,status) VALUES('person_relationship',md5('draft-edge')::uuid,'description','隐藏关系引用',md5('source-fixture')::uuid,'卷一','published');
 SET ROLE anon;`);
const content = async (table, opts = {}) => {
  const args = { p_table: table, ...opts };
  const keys = Object.keys(args);
  return scalar(
    `SELECT public.content_page(${keys.map((k, i) => `${k} => $${i + 1}`).join(",")})`,
    Object.values(args),
  );
};
let catalogue = new Set();
for (let page = 0; ; page++) {
  const rows = await content("person", { p_page: page });
  assert.ok(rows.items.length <= 20);
  assert.ok(
    rows.items.every((n) => !("biography" in n) && n.description.length <= 600),
  );
  rows.items.forEach((n) => {
    assert.ok(!catalogue.has(n.id));
    catalogue.add(n.id);
  });
  if (!rows.has_more) break;
}
assert.equal(catalogue.size, 1500);
assert.equal(
  (await content("person", { p_query: "别名1499" })).items[0].name,
  "测试人物1499",
);
assert.deepEqual(
  (
    await content("nodes", { p_topic: "fixture-topic", p_section: 0 })
  ).items.map((n) => n.id),
  [p1002, p1000, p1001],
);
assert.equal((await content("topic")).items[0].section_count, 1);
assert.ok(!("sections" in (await content("topic")).items[0]));
assert.equal(
  (await content("event", { p_from: 906, p_to: 909 })).items.length,
  0,
);
const claimIds = new Set();
for (let page = 0; ; page++) {
  const rows = await content("fact_claim", {
    p_subject: "person",
    p_subject_id: p1000,
    p_page: page,
    p_limit: 50,
  });
  assert.ok(rows.items.length <= 50);
  rows.items.forEach((n) => {
    assert.ok(!claimIds.has(n.id));
    claimIds.add(n.id);
    assert.equal(n.source.title, "测试出处");
  });
  if (!rows.has_more) break;
}
assert.equal(claimIds.size, 1205);
assert.equal(
  (await content("fact_claim", { p_claim: await id("claim-1205") })).items
    .length,
  1,
  "Pinned citations remain accessible beyond page one",
);
await assert.rejects(content("person", { p_admin: true }));
await assert.rejects(content("user_roles"));
await assert.rejects(content("source"));
const context = await scalar("SELECT public.entry_context($1)", [
  await id("person-1"),
]);
assert.equal(context.edges.length, 20);
assert.equal(context.has_more, true);
assert.equal(context.nodes.length, 21);
await db.exec(
  `RESET ROLE; SET ROLE authenticated; SELECT set_config('request.jwt.claim.sub','${draft}',false);`,
);
assert.equal(
  (await content("person", { p_admin: false, p_ids: [draft] })).items.length,
  0,
);
assert.equal(
  (await content("person", { p_admin: true, p_ids: [draft] })).items.length,
  1,
);
assert.equal(
  (await content("person_relationship", { p_ids: [await id("draft-edge")] }))
    .items.length,
  0,
);
assert.equal(
  (await content("fact_claim", { p_query: "隐藏关系引用" })).items.length,
  0,
);
await db.exec(
  `RESET ROLE; SELECT set_config('request.jwt.claim.sub','',false); SET ROLE anon;`,
);
// Ask uses RPC reads only; the citation ledger includes just the evidence actually retrieved.
const { createRemoteLibrary } =
  await import("../apps/api/dsh/remote-library.mjs");
const { validateAnswer } = await import("../apps/api/dsh/retrieval.mjs");
const { mkdtemp, rm } = await import("node:fs/promises");
const dir = await mkdtemp(join(tmpdir(),"histree-remote-test-"));
const ledger = `${dir}/retrieved`;
const realFetch = globalThis.fetch;
const remoteCalls = [];
globalThis.fetch = async (url, options) => {
  const name = new URL(url).pathname.split("/").at(-1);
  const args = JSON.parse(options.body);
  remoteCalls.push(name);
  const keys = Object.keys(args);
  const value = await scalar(
    `SELECT public.${name}(${keys.map((k, i) => `${k} => $${i + 1}`).join(",")})`,
    Object.values(args),
  );
  return new Response(JSON.stringify(value), { status: 200 });
};
try {
  const library = await createRemoteLibrary(
    { url: "http://localhost:54321", anonKey: "fixture" },
    ledger,
  );
  const found = await library.search({ keywords: ["别名1499"] });
  assert.ok(JSON.stringify(found).includes("1499"));
  assert.equal((await library.entry({ kind: "person", id: p1000 })).id, p1000);
  const topicId = (await content("topic")).items[0].id;
  assert.equal(
    (await library.entry({ kind: "topic", id: topicId })).sections.length,
    1,
  );
  const rels = await library.relations({ id: await id("person-1"), depth: 2 });
  assert.ok(rels.edges.length <= 40);
  assert.equal(rels.truncated, true);
  const [one, two] = await Promise.all([
    library.evidence({ kind: "person", id: p1000 }),
    library.evidence({ kind: "person", id: p1000, offset: 10 }),
  ]);
  assert.equal(one.items.length, 10);
  assert.equal(two.items.length, 10);
  assert.equal(one.nextOffset, 10);
  const saved = JSON.parse(await readFile(`${ledger}.json`, "utf8"));
  assert.equal(saved.length, 20);
  const key = one.items[0].key;
  assert.equal(
    validateAnswer(
      JSON.stringify({ answer: `测试 [${key}]`, insufficientEvidence: false }),
      { byKey: new Map(saved.map((c) => [c.key, c])) },
      new Set([key]),
    ).citations.length,
    1,
  );
  assert.throws(() =>
    validateAnswer(
      JSON.stringify({ answer: "测试 [C9999]", insufficientEvidence: false }),
      { byKey: new Map(saved.map((c) => [c.key, c])) },
      new Set([key]),
    ),
  );
  assert.ok(
    remoteCalls.every((n) =>
      [
        "ask_search",
        "entry_detail",
        "topic_detail",
        "entry_context",
        "content_page",
      ].includes(n),
    ),
  );
} finally {
  globalThis.fetch = realFetch;
  await rm(dir, { recursive: true, force: true });
}
console.log(
  "PASS: paged catalogues and 1205 citations, section ordering, admin selection, endpoint draft isolation, bounded entry context, on-demand Ask retrieval and concurrent citation ledger validation.",
);

const ts = createRequire(new URL("../apps/web/package.json", import.meta.url))(
  "typescript",
);
const source = await readFile(
  new URL("../packages/shared-types/src/explore.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
  },
});
const { exploreRequest } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
assert.equal(exploreRequest("/people"), null);
assert.deepEqual(exploreRequest("/search?q=李%25&kind=person&page=1").args, {
  p_query: "李%",
  p_kind: "person",
  p_page: 1,
  p_limit: 20,
});
for (const path of [
  "/search?kind=invalid",
  "/search?page=NaN",
  "/search?limit=999",
  "/graph-slice/invalid",
  `/graph-slice/${p1000}?from=20&to=10`,
  `/graph-slice/${p1000}?depth=3`,
])
  assert.throws(() => exploreRequest(path));
const contentSource = await readFile(
  new URL("../packages/shared-types/src/content-query.ts", import.meta.url),
  "utf8",
);
const contentOutput = ts.transpileModule(contentSource, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
  },
}).outputText;
const { contentRequest } = await import(
  `data:text/javascript;base64,${Buffer.from(contentOutput).toString("base64")}`
);
for (const path of [
  "/catalog/person?page=-1",
  "/catalog/user_roles",
  "/catalog/event?from=910&to=900",
  "/catalog/person?ids=bad",
  "/catalog/person?limit=51",
])
  assert.throws(() => contentRequest(path));
console.log(
  "PASS: 1500 records, global alias/tag/topic search, literal metacharacters, stable complete pagination, one/two-hop expansion, direction, bounded subgraphs, year filters, anonymous/editor draft isolation, full selected details, shared request validation.",
);

if (process.env.HISTREE_EXPLORE_BROWSER) {
  const { chromium } = await import("playwright");
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.HISTREE_CHROME_PATH
      ? { executablePath: process.env.HISTREE_CHROME_PATH }
      : {}),
  });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const calls = [];
    await page.route("**/rest/v1/**", async (route) => {
      const requestUrl = new URL(route.request().url());
      const name = requestUrl.pathname.split("/rpc/")[1];
      calls.push(
        name ??
          (requestUrl.pathname.endsWith("/topic") &&
          requestUrl.searchParams.has("slug")
            ? "SCOPED_TOPIC"
            : "TABLE_READ"),
      );
      const args =
        route.request().method() === "POST"
          ? route.request().postDataJSON()
          : {};
      try {
        let body;
        if (name === "search_entries")
          body = await search(
            args.p_query,
            args.p_kind,
            args.p_page,
            args.p_limit,
          );
        else if (name === "graph_slice")
          body = await graph(
            args.p_id,
            args.p_mode,
            args.p_depth,
            args.p_from,
            args.p_to,
          );
        else if (name === "entry_detail")
          body = await scalar("SELECT public.entry_detail($1)", [args.p_id]);
        else if (name === "content_page") {
          const keys = Object.keys(args);
          body = await scalar(
            `SELECT public.content_page(${keys.map((k, i) => `${k} => $${i + 1}`).join(",")})`,
            Object.values(args),
          );
        } else if (name === "entry_context")
          body = await scalar("SELECT public.entry_context($1,$2)", [
            args.p_id,
            args.p_page ?? 0,
          ]);
        else if (
          requestUrl.pathname.endsWith("/topic") &&
          requestUrl.searchParams.has("slug")
        )
          body = (
            await db.query(
              "SELECT to_jsonb(t) doc FROM topic t WHERE slug=$1 AND status='published'",
              [requestUrl.searchParams.get("slug").slice(3)],
            )
          ).rows.map((r) => r.doc);
        else throw new Error("Unexpected full table read");
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(body),
        });
      } catch (e) {
        await route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({ message: e.message }),
        });
      }
    });
    const base = process.env.HISTREE_EXPLORE_BROWSER;
    await page.goto(`${base}graph`);
    await page
      .getByRole("button", { name: "测试人物0001 · 虚构时代", exact: true })
      .waitFor();
    assert.ok(
      calls.length > 0 && calls.every((name) => name === "search_entries"),
      "Graph entry must only fetch search summaries",
    );
    await page
      .getByRole("button", { name: "测试人物0001 · 虚构时代", exact: true })
      .click();
    await page.locator('.history-canvas[data-layout-state="ready"]').waitFor();
    assert.equal(
      await page.locator("[data-node]").count(),
      120,
      "High-degree graphs are capped in the browser too",
    );
    await page.getByText("当前子图最多展示", { exact: false }).waitFor();
    const transforms = await page
      .locator("[data-node]")
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute("transform")));
    assert.ok(transforms.every((t) => t && !t.includes("NaN")));
    await page.getByRole("button", { name: "适应全图", exact: true }).click();
    await page.getByRole("button", { name: "返回查找", exact: true }).click();
    await page
      .getByRole("searchbox", { name: "查找图谱节点" })
      .fill("别名1499");
    await page
      .getByRole("button", { name: "测试人物1499 · 虚构时代", exact: true })
      .click();
    await page
      .getByRole("button", { name: "查看人物：测试人物1499", exact: true })
      .waitFor();
    await page.locator('.history-canvas[data-layout-state="ready"]').waitFor();
    const before = await page.locator("[data-node]").getAttribute("transform");
    await page
      .getByRole("searchbox", { name: "查找图谱节点" })
      .fill("别名1000");
    await page
      .getByRole("button", { name: "测试人物1000 · 虚构时代", exact: true })
      .waitFor();
    assert.equal(
      await page.locator("[data-node]").getAttribute("transform"),
      before,
      "Search input must preserve canvas layout",
    );
    await page
      .getByRole("button", { name: "测试人物1000 · 虚构时代", exact: true })
      .click();
    await page
      .getByRole("button", { name: "查看人物：测试人物1001", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "展开两层关系", exact: true })
      .click();
    await page
      .getByRole("button", { name: "查看人物：测试人物1002", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "查看人物：测试人物1001", exact: true })
      .press("Shift+Enter");
    await page
      .getByRole("button", { name: "测试人物1001", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "展开两层关系", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "← 返回上一级", exact: true })
      .click();
    await page
      .getByRole("button", { name: "查看人物：测试人物1000", exact: true })
      .waitFor();
    await page.getByRole("button", { name: "人物与事件", exact: true }).click();
    await page
      .getByRole("button", { name: "查看事件：测试战役", exact: true })
      .waitFor();
    await page.getByRole("spinbutton", { name: "图谱起始年" }).fill("906");
    await page.getByRole("spinbutton", { name: "图谱结束年" }).fill("909");
    await page.waitForFunction(
      () => document.querySelectorAll("[data-node]").length === 1,
    );
    await page.getByRole("spinbutton", { name: "图谱起始年" }).fill("911");
    await page.getByText("起始年不能晚于结束年。", { exact: true }).waitFor();
    await page.goto(`${base}search?q=${encodeURIComponent("别名1499")}`);
    await page
      .getByRole("heading", { name: "测试人物1499", exact: true })
      .waitFor();
    await page.getByRole("searchbox").fill("检索标签");
    await page
      .getByRole("button", { name: "下一页", exact: true })
      .waitFor({ state: "visible" });
    await page.waitForFunction(() =>
      document.body.textContent.includes("20 条结果"),
    );
    await page.getByRole("button", { name: "下一页", exact: true }).click();
    await page.waitForFunction(() =>
      document.body.textContent.includes("第 2 页"),
    );
    await page.goto(`${base}people`);
    await page.locator(".directory-card").first().waitFor();
    assert.equal(await page.locator(".directory-card").count(), 20);
    await page.getByRole("button", { name: "下一页", exact: true }).click();
    await page.waitForFunction(() =>
      document.body.textContent.includes("第 2 页"),
    );
    assert.ok(new URL(page.url()).searchParams.get("page") === "1");
    await page.goto(`${base}people/${p1000}`);
    await page
      .getByRole("heading", { name: "测试人物1000", exact: true })
      .waitFor();
    await page.locator('[id^="claim-"]').first().waitFor();
    assert.equal(await page.locator('[id^="claim-"]').count(), 20);
    await page
      .getByRole("button", { name: "下一页", exact: true })
      .last()
      .click();
    await page.waitForFunction(() =>
      document.body.textContent.includes("第 2 页"),
    );
    const pinned = await id("claim-1205");
    await page.goto(`${base}evidence/person/${p1000}#claim-${pinned}`);
    await page.locator(`#claim-${pinned}`).waitFor();
    assert.equal(await page.locator('[id^="claim-"]').count(), 1);
    await page
      .getByRole("button", { name: "查看全部依据", exact: true })
      .click();
    await page.waitForFunction(
      () => document.querySelectorAll('[id^="claim-"]').length === 20,
    );
    await page.getByRole('button',{name:'下一页',exact:true}).click();
    await page.waitForFunction(()=>document.body.textContent.includes('第 2 页'));
    const anchor=await page.locator('[id^="claim-"]').first().getAttribute('id');
    await page.getByRole('link',{name:'此条引用的固定链接',exact:true}).first().click();
    await page.waitForFunction(()=>document.querySelectorAll('[id^="claim-"]').length===1);
    assert.equal(await page.locator('[id^="claim-"]').getAttribute('id'),anchor,'Same-page citation links must reset paging and follow the current hash');
    await page.goto(`${base}topics/fixture-topic`);
    await page
      .getByRole("heading", { name: "测试专题", exact: true })
      .waitFor();
    await page.locator("#chapter-0").scrollIntoViewIfNeeded();
    await page.locator("#chapter-0 a").first().waitFor();
    const chapterNames = await page.locator("#chapter-0 h3").allTextContents();
    assert.deepEqual(chapterNames, [
      "测试人物1002",
      "测试人物1000",
      "测试人物1001",
    ]);
    assert.ok(!calls.includes("TABLE_READ"));
    assert.deepEqual(errors, []);
    console.log(
      "PASS: browser catalogue pagination, entry evidence pagination, citation deep links and lazy topic sections.",
    );

    await page.screenshot({
      path: join(tmpdir(),"histree-explore-search.png"),
      fullPage: true,
    });
    console.log(
      "PASS: browser graph entry, global search jump, preserved layout on typing, worker completion, two-hop/drill/back, event view, search pagination; no full table reads or browser errors.",
    );

    if (process.env.HISTREE_ADMIN_BROWSER) {
      await db.exec("RESET ROLE;");
      const ctx = await browser.newContext();
      await ctx.addInitScript(() => {
        if(!location.origin.startsWith('http://127.0.0.1:'))return;
        const enc = (o) => btoa(JSON.stringify(o));
        const token = `${enc({ alg: "HS256", typ: "JWT" })}.${enc({ sub: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", exp: 4102444800 })}.local-test`;
        localStorage.setItem(
          "sb-127-auth-token",
          JSON.stringify({
            access_token: token,
            refresh_token: "local-refresh",
            expires_at: 4102444800,
            expires_in: 3600,
            token_type: "bearer",
            user: {
              id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
              email: "editor@example.test",
            },
          }),
        );
      });
      const adminCalls = [];
      await ctx.route("**/rest/v1/user_roles*", (r) =>
        r.fulfill({
          contentType: "application/json",
          body: JSON.stringify({ role: "admin" }),
        }),
      );
      await ctx.route("**/auth/v1/user", (r) =>
        r.fulfill({
          contentType: "application/json",
          body: JSON.stringify({
            id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            email: "editor@example.test",
          }),
        }),
      );
      await ctx.route("**/api/v1/**", async (route) => {
        const u = new URL(route.request().url());
        const path = u.pathname.replace("/api/v1", "") + u.search;
        assert.ok(
          path.startsWith("/editorial/"),
          "Admin fetches only the active paged resource",
        );
        assert.ok(route.request().headers().authorization);
        const args = contentRequest(path, true);
        adminCalls.push(args);
        const keys = Object.keys(args);
        const result = await scalar(
          `SELECT public.content_page(${keys.map((k, i) => `${k} => $${i + 1}`).join(",")})`,
          Object.values(args),
        );
        await route.fulfill({
          contentType: "application/json",
          body: JSON.stringify(result),
        });
      });
      const ap = await ctx.newPage();
      ap.on("pageerror", (e) => errors.push(e.message));
      await ap.goto(`${process.env.HISTREE_ADMIN_BROWSER}admin`);
      await ap
        .getByRole("heading", { name: "人物管理", exact: true })
        .waitFor();
      await ap.getByRole("button", { name: "下一页", exact: true }).click();
      await ap.waitForFunction(() =>
        document.body.textContent.includes("第 2 页"),
      );
      assert.ok(
        adminCalls.some((c) => c.p_table === "person" && c.p_page === 1),
      );
      await ap.goto(`${process.env.HISTREE_ADMIN_BROWSER}admin/editorial`);
      await ap.getByRole("button", { name: "＋ 新增", exact: true }).click();
      await ap
        .getByRole("searchbox", { name: "搜索关联阅读条目" })
        .fill("别名1499");
      const checkbox = ap.getByRole("checkbox");
      await ap.waitForFunction(
        () => document.querySelectorAll("input[type=checkbox]").length === 1,
      );
      await checkbox.check();
      await ap
        .getByText("已选 1 个条目（保持勾选顺序）", { exact: true })
        .waitFor();
      await ap.getByRole("searchbox", { name: "搜索关联阅读条目" }).fill("");
      await ap.waitForFunction(
        () => document.querySelectorAll("input[type=checkbox]").length === 20,
      );
      await ap
        .getByRole("button", { name: "下一页", exact: true })
        .first()
        .click();
      await ap
        .getByText("已选 1 个条目（保持勾选顺序）", { exact: true })
        .waitFor();
      assert.ok(
        adminCalls.some((c) => c.p_table === "nodes" && c.p_ids?.length === 1),
        "Selected nodes are independently read by stable ID",
      );
      await ap.getByRole("button", { name: "来源库", exact: true }).click();
      await ap.getByRole("button", { name: "＋ 新增", exact: true }).click();
      await ap.getByLabel("来源类型").selectOption("scholarship");
      await ap.getByLabel("书名／资料标题").fill("测试来源");
      await ap.getByRole("button", { name: "陈述与引用", exact: true }).click();
      await ap.getByRole("button", { name: "＋ 新增", exact: true }).click();
      await ap
        .getByRole("searchbox", { name: "搜索具体条目或关系" })
        .fill("别名1499");
      await ap
        .getByRole("group", { name: "具体条目或关系候选" })
        .getByRole("button", { name: "测试人物1499", exact: true })
        .click();
      await ap
        .getByRole("group", { name: "来源候选" })
        .getByRole("button", { name: "测试出处", exact: true })
        .click();
      await ap.getByText("已选：测试出处", { exact: true }).waitFor();
      assert.deepEqual(errors, []);
      await ap.screenshot({
        path: join(tmpdir(),"histree-admin-pagination.png"),
        fullPage: true,
      });
      await ctx.close();
      console.log(
        "PASS: browser admin page isolation, paging, cross-page checkbox preservation, selected ID lookup, source editing and evidence pickers.",
      );
    }
  } finally {
    await browser.close();
  }
}
await db.close();
