/** Full corpus/evidence/dating/directory chain against native disposable MySQL and real Nest HTTP. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtemp, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { applySchema, schemaFiles } from "./mysql-schema.mjs";
import { legacyEvidence } from "../packages/shared-types/dist/index.js";
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
require("reflect-metadata");
const { ConfigService } = require("@nestjs/config"),
  { Module } = require("@nestjs/common"),
  { NestFactory } = require("@nestjs/core");
const { claimFingerprint } = require("./dist/modules/mysql/query-contracts.js");
const { MysqlService } = require("./dist/modules/mysql/mysql.service.js"),
  { LibraryService } = require("./dist/modules/library/library.service.js"),
  {
    LibraryController,
  } = require("./dist/modules/library/library.controller.js");
const { PersonService } = require("./dist/modules/person/person.service.js"),
  { PersonController } = require("./dist/modules/person/person.controller.js"),
  { TimelineService } = require("./dist/modules/timeline/timeline.service.js"),
  {
    TimelineController,
  } = require("./dist/modules/timeline/timeline.controller.js"),
  { ExploreController } = require("./dist/modules/graph/explore.controller.js");
assert(["localhost", "127.0.0.1"].includes(process.env.MYSQL_HOST));
assert.match(process.env.MYSQL_DATABASE ?? "", /^histree_test_[a-z0-9_]+$/);
const db = new MysqlService(new ConfigService(process.env)),
  sha = (value) => createHash("sha256").update(value).digest("hex");
const ids = Array.from({ length: 11 }, () => randomUUID()),
  [
    personA,
    personB,
    personC,
    event,
    source,
    claim,
    eventClaim,
    participation,
    dating,
    hiddenClaim,
    claimRelation,
  ] = ids;
const book = "structure-fixture",
  section = book + "-s0001",
  paragraph = book + "-p000001",
  quote = "\ufeff某甲于九百年至九百一十年之间居此。",
  archive =
    "https://github.com/greed-216/histree/blob/" +
    "a".repeat(40) +
    "/content/fixture/source.txt";
let app,
  checks = 0;
let primaryFailure;
const connection = await db.connectionPool().getConnection();
try {
  await applySchema(connection, schemaFiles.slice(4));
  await db.execute(
    "INSERT INTO library_book VALUES(?, '合成史书', 'fixture-v1', 0, 1, 1, ?,JSON_OBJECT(),'available')",
    [book, sha(quote)],
  );
  await db.execute("INSERT INTO library_asset VALUES(?, 'synthetic.txt',?)", [
    sha("asset"),
    sha(quote),
  ]);
  await db.execute(
    "INSERT INTO library_section VALUES(?,?,0,'卷一',1,'volume',0,JSON_OBJECT())",
    [section, book],
  );
  await db.execute(
    "INSERT INTO library_paragraph VALUES(?,?,?,0,'body',?,?,?,0,?,JSON_ARRAY())",
    [paragraph, book, section, quote, sha(quote), sha("asset"), quote.length],
  );
  await db.execute(
    "INSERT INTO person(id,name,status,era,description) VALUES(?,?,'published','合成时代',?),(?,?,'published','合成时代','人物简介'),(?,?,'published','合成时代','年代未知')",
    [
      personA,
      "甲__structure_fixture__",
      "曾任官职，未与前卷同名者强合。",
      personB,
      "乙__structure_fixture__",
      personC,
      "丙__structure_fixture__",
    ],
  );
  await db.execute(
    "INSERT INTO event(id,title,status) VALUES(?,'合成年代范围','published')",
    [event],
  );
  await db.execute(
    "INSERT INTO source(id,title,source_type,url) VALUES(?,'合成史书','primary',?)",
    [source, archive],
  );
  await db.execute(
    "INSERT INTO source_text(source_id,archive_url_sha256,archive_url,content,content_sha256,archive_blob_sha256,archive_commit) VALUES(?,?,?,?,?,?,?)",
    [
      source,
      sha(archive),
      archive,
      quote,
      sha(quote),
      sha(quote),
      "a".repeat(40),
    ],
  );
  await db.execute(
    "INSERT INTO fact_claim(id,subject_table,subject_id,field_path,claim_text,source_id,status,note) VALUES(?,'person',?,'description','人物事实',?,'published',?),(?,'event',?,'time_original','年代界限',?,'published',?),(?,'person',?,'description','秘密事实',?,'draft','隐藏')",
    [
      claim,
      personA,
      source,
      "原文：" + quote + "；核对说明：身份待考",
      eventClaim,
      event,
      source,
      "原文：" + quote + "；核对说明：范围依原文",
      hiddenClaim,
      personC,
      source,
    ],
  );
  await db.execute("INSERT INTO library_source_link VALUES(?,?,?,?)", [
    source,
    sha(archive),
    sha(quote),
    paragraph,
  ]);
  await db.execute(
    "INSERT INTO event_dating VALUES(?,?,?,?,900,910,'range',NULL,'依据合成原文给出的上下界','reviewed')",
    [
      dating,
      event,
      eventClaim,
      claimFingerprint({
        subject_table: "event",
        subject_id: event,
        claim_text: "年代界限",
        source_id: source,
        note: "原文：" + quote + "；核对说明：范围依原文",
        archive_url: archive,
      }),
    ],
  );
  await db.execute(
    "INSERT INTO library_review_coverage VALUES(?,'fixture-v1',1,1,1,0,1,?,'fixture/audit.json')",
    [book, sha("audit")],
  );
  await db.execute(
    "INSERT INTO library_paragraph_review VALUES(?,?,'deferred','身份仍待考',?)",
    [paragraph, sha(quote), sha("audit")],
  );
  const e = legacyEvidence("原文：" + quote + "；核对说明：身份待考");
  await db.execute("INSERT INTO claim_structure VALUES(?,?,?,?,?)", [
    claim,
    sha("原文：" + quote + "；核对说明：身份待考"),
    e.quote,
    e.review,
    e.review_state,
  ]);
  const [leftBasis] = await db.rows(
    "SELECT c.*,s.url archive_url FROM fact_claim c JOIN source s ON s.id=c.source_id WHERE c.id=?",
    [claim],
  );
  const [rightBasis] = await db.rows(
    "SELECT c.*,s.url archive_url FROM fact_claim c JOIN source s ON s.id=c.source_id WHERE c.id=?",
    [eventClaim],
  );
  await db.execute(
    "INSERT INTO claim_relation VALUES(?,?,?,?,?,'corroborates','reviewed','合成关联记录')",
    [
      claimRelation,
      claim,
      eventClaim,
      claimFingerprint(leftBasis),
      claimFingerprint(rightBasis),
    ],
  );
  const upgradeRoot = await mkdtemp(
    join(tmpdir(), "histree-structure-upgrade-"),
  );
  try {
    const envFile = join(upgradeRoot, "mysql.env"),
      planFile = join(upgradeRoot, "plan.json");
    await writeFile(
      envFile,
      Object.entries(process.env)
        .filter(([key]) => key.startsWith("MYSQL_"))
        .map(([key, value]) => key + "=" + value)
        .join("\n"),
      { mode: 0o600 },
    );
    const runUpgrade = (extra) =>
      spawnSync(
        process.execPath,
        [
          "scripts/upgrade-content-structure.mjs",
          "--mysql-env",
          envFile,
          ...extra,
        ],
        { encoding: "utf8", timeout: 30000 },
      );
    const prepared = runUpgrade(["--output", planFile, "--limit", "5000"]);
    assert.equal(prepared.status, 0, prepared.stderr);
    const plan = JSON.parse(await readFile(planFile, "utf8"));
    plan.claim_structure = plan.claim_structure.filter((row) =>
      [claim, eventClaim].includes(row.claim_id),
    );
    assert.equal(plan.claim_structure.length, 2);
    plan.paragraphs = await db.rows(
      "SELECT * FROM library_paragraph_review WHERE paragraph_id=?",
      [paragraph],
    );
    let bytes = JSON.stringify(plan);
    await writeFile(planFile, bytes);
    const applied = runUpgrade([
      "--apply",
      "--plan",
      planFile,
      "--expected-sha256",
      sha(bytes),
    ]);
    assert.equal(applied.status, 0, applied.stderr);
    assert.equal(
      runUpgrade([
        "--apply",
        "--plan",
        planFile,
        "--expected-sha256",
        sha(bytes),
      ]).status,
      0,
      "Exact replay must be idempotent",
    );
    await db.execute("DELETE FROM claim_structure WHERE claim_id=?", [
      eventClaim,
    ]);
    plan.paragraphs[0].content_sha256 = "0".repeat(64);
    bytes = JSON.stringify(plan);
    await writeFile(planFile, bytes);
    const stale = runUpgrade([
      "--apply",
      "--plan",
      planFile,
      "--expected-sha256",
      sha(bytes),
    ]);
    assert.notEqual(stale.status, 0, "A late paragraph guard must reject");
    assert.equal(
      (
        await db.rows("SELECT * FROM claim_structure WHERE claim_id=?", [
          eventClaim,
        ])
      ).length,
      0,
      "Late rejection must roll back earlier evidence insertion",
    );
    checks += 3;
  } finally {
    await rm(upgradeRoot, { recursive: true, force: true });
  }
  const library = new LibraryService(db);
  assert.equal(
    (await library.section(book, section, { paragraph })).paragraphs[0].content,
    quote,
  );
  checks++;
  assert.equal((await library.sourceLocation(source)).paragraph_id, paragraph);
  assert.equal((await library.links(book, section, paragraph)).items.length, 2);
  assert.equal(
    (await library.links(book, section, paragraph)).items.some(
      (c) => c.claim_id === hiddenClaim,
    ),
    false,
  );
  checks++;
  assert.equal((await library.book(book)).coverage[0].deferred, 1);
  checks++;
  const evidence = (await db.content({ p_table: "fact_claim", p_claim: claim }))
    .items[0];
  assert.equal(evidence.evidence.quote, quote);
  assert.equal(evidence.evidence.origin, "structured");
  assert.equal(evidence.evidence.location.paragraph_id, paragraph);
  assert.equal(
    evidence.evidence.related_claims[0].related_claim_id,
    eventClaim,
  );
  assert.equal(
    (await db.content({ p_table: "fact_claim", p_claim: eventClaim })).items[0]
      .evidence.related_claims[0].related_claim_id,
    claim,
  );
  checks++;
  await db.execute("UPDATE fact_claim SET note=? WHERE id=?", [
    "旧值已更新",
    claim,
  ]);
  assert.equal(
    (await db.content({ p_table: "fact_claim", p_claim: claim })).items[0]
      .evidence.origin,
    "legacy",
  );
  checks++;
  assert.equal(
    (await db.content({ p_table: "fact_claim", p_claim: claim })).items[0]
      .evidence.related_claims.length,
    0,
  );
  await db.execute("UPDATE fact_claim SET note=? WHERE id=?", [
    "原文：" + quote + "；核对说明：身份待考",
    claim,
  ]);
  await db.execute("UPDATE fact_claim SET note=? WHERE id=?", [
    "依据发生变化",
    eventClaim,
  ]);
  assert.equal((await db.entry(event)).datings.length, 0);
  assert.equal(
    (
      await db.content({
        p_table: "event",
        p_dating: "estimated",
        p_from: 905,
        p_to: 906,
      })
    ).items.some((e) => e.id === event),
    false,
  );
  await db.execute("UPDATE fact_claim SET note=? WHERE id=?", [
    "原文：" + quote + "；核对说明：范围依原文",
    eventClaim,
  ]);
  await db.execute(
    "UPDATE event_dating SET latest_year=NULL,precision_kind='relative' WHERE id=?",
    [dating],
  );
  assert(
    (
      await db.content({
        p_table: "event",
        p_dating: "estimated",
        p_from: 905,
        p_to: 906,
      })
    ).items.some((item) => item.id === event),
  );
  await db.execute(
    "UPDATE event_dating SET earliest_year=NULL,precision_kind='unknown' WHERE id=?",
    [dating],
  );
  assert(
    !(await db.content({ p_table: "event", p_dating: "estimated" })).items.some(
      (item) => item.id === event,
    ),
  );
  await db.execute(
    "UPDATE event_dating SET earliest_year=900,latest_year=910,precision_kind='range' WHERE id=?",
    [dating],
  );
  assert.equal((await db.entry(event)).start_year, null);
  assert.equal((await db.entry(event)).datings[0].earliest_year, 900);
  assert.equal(
    (
      await db.content({
        p_table: "event",
        p_dating: "estimated",
        p_from: 905,
        p_to: 906,
      })
    ).items.some((e) => e.id === event),
    true,
  );
  assert.equal(
    (
      await db.content({
        p_table: "event",
        p_dating: "estimated",
        p_from: 920,
        p_to: 930,
      })
    ).items.some((e) => e.id === event),
    false,
  );
  checks++;
  await assert.rejects(
    db.execute("UPDATE event_dating SET earliest_year=0 WHERE id=?", [dating]),
  );
  checks++;
  class FixtureModule {}
  Module({
    controllers: [
      LibraryController,
      PersonController,
      TimelineController,
      ExploreController,
    ],
    providers: [
      { provide: MysqlService, useValue: db },
      { provide: LibraryService, useValue: library },
      { provide: PersonService, useValue: new PersonService(db) },
      { provide: TimelineService, useValue: new TimelineService(db) },
    ],
  })(FixtureModule);
  app = await NestFactory.create(FixtureModule, { logger: false });
  await app.listen(0, "127.0.0.1");
  const base = await app.getUrl();
  const get = async (path) => {
    const r = await fetch(base + "/api/v1" + path);
    assert.equal(r.status, 200, path);
    return r.json();
  };
  assert.equal(
    (
      await get(
        "/library/" + book + "/sections/" + section + "?paragraph=" + paragraph,
      )
    ).paragraphs[0].review.disposition,
    "deferred",
  );
  checks++;
  assert.equal(
    (
      await get(
        "/library/" +
          book +
          "/sections/" +
          section +
          "/links?paragraph=" +
          paragraph,
      )
    ).items.length,
    2,
  );
  checks++;
  const query = "/people?q=__structure_fixture__&limit=1&sort=name",
    first = await get(query),
    second = await get(
      query + "&cursor=" + encodeURIComponent(first.next_cursor),
    );
  assert.equal(first.items.length, 1);
  assert.notEqual(first.items[0].id, second.items[0].id);
  checks++;
  assert.equal(
    (await get("/people?book=" + book)).items.some((p) => p.id === personA),
    true,
  );
  assert.equal(
    (await get("/people?book=" + book)).items.some((p) => p.id === personC),
    false,
  );
  checks++;
  assert.equal((await get("/people/facets")).eras.includes("合成时代"), true);
  checks++;
  // Canonical era navigation expands aliases, including two groups for cross-period people.
  await db.execute(
    "UPDATE person SET era=CASE id WHEN ? THEN '西汉初年' WHEN ? THEN '东汉' ELSE '元末明初' END WHERE id IN (?,?,?)",
    [personA, personB, personA, personB, personC],
  );
  const periodFirst = await get("/people?period=qin-han&limit=1");
  const periodNext = await get(
    "/people?period=qin-han&limit=1&cursor=" +
      encodeURIComponent(periodFirst.next_cursor),
  );
  assert.equal(periodFirst.items.length, 1);
  assert.equal(periodNext.items.length, 1);
  assert.notEqual(periodFirst.items[0].id, periodNext.items[0].id);
  assert(
    (await get("/people?period=ming")).items.some(
      (p) => p.id === personC && p.era === "元末明初",
    ),
  );
  assert(
    (await get("/people?period=mongol-yuan")).items.some(
      (p) => p.id === personC,
    ),
  );
  assert.equal(
    (await get("/people?era=" + encodeURIComponent("西汉初年"))).items.filter(
      (p) => [personA, personB].includes(p.id),
    ).length,
    1,
  );
  assert(
    (await get("/people/facets")).periods.some(
      (p) => p.key === "qin-han" && p.count >= 2,
    ),
  );
  assert.equal((await fetch(base + "/api/v1/people?period=bad")).status, 400);
  assert.equal(
    (
      await fetch(
        base +
          "/api/v1/people?period=ming&era=" +
          encodeURIComponent("元末明初"),
      )
    ).status,
    400,
  );
  checks += 6;
  // Memorial/retrospective event links do not change the person's recorded era.
  await db.execute("UPDATE person SET era='先秦' WHERE id=?", [personA]);
  await db.execute("UPDATE event SET start_year=960 WHERE id=?", [event]);
  const memorialPerson = (await get("/people?period=pre-qin")).items.find(
    (p) => p.id === personA,
  );
  assert(memorialPerson);
  assert.equal(memorialPerson.era, "先秦");
  assert.equal(memorialPerson.sort_year, 960);
  assert.equal(memorialPerson.sort_year_basis, "event");
  assert(
    !(await get("/people?period=song-liao-jin-xia")).items.some(
      (p) => p.id === personA,
    ),
  );
  await db.execute("UPDATE event SET start_year=NULL WHERE id=?", [event]);
  await db.execute("UPDATE person SET era='合成时代' WHERE id IN (?,?,?)", [
    personA,
    personB,
    personC,
  ]);
  checks++;
  const before = await get("/timeline/overview?compact=1");
  assert(before.years.every((y) => !y.highlights));
  await db.execute("UPDATE event SET start_year=900 WHERE id=?", [event]);
  const after = await get("/timeline/overview?compact=1");
  assert.equal(Number(after.undated), Number(before.undated) - 1);
  assert(
    (await get("/timeline/highlights?year=900")).items.some(
      (e) => e.id === event,
    ),
  );
  checks++;
  assert.equal(
    (
      await fetch(
        base +
          "/api/v1" +
          query +
          "&cursor=" +
          encodeURIComponent(first.next_cursor),
      )
    ).status,
    409,
  );
  checks++;
  await db.execute("UPDATE fact_claim SET status='draft' WHERE id=?", [
    eventClaim,
  ]);
  assert.equal((await db.entry(event)).datings.length, 0);
  checks++;
  await db.execute("UPDATE source SET url=? WHERE id=?", [
    "https://example.test/new",
    source,
  ]);
  assert.equal(await library.sourceLocation(source), null);
  assert.equal((await library.links(book, section, paragraph)).items.length, 0);
  checks++;
  console.log(
    JSON.stringify({
      verified: true,
      checks,
      native_mysql: true,
      actual_nest_http: true,
      model_calls: 0,
      legacy_dates_preserved_before_explicit_fixture_update: true,
    }),
  );
} catch (error) {
  console.error("STRUCTURE_FIXTURE_FAILURE", {
    code: error.code,
    message: error.message,
    sql: error.sql,
  });
  primaryFailure = error;
} finally {
  let cleanupFailure;
  for (const [table, column, values] of [
    ["claim_relation", "id", [claimRelation]],
    ["event_dating", "id", [dating]],
    ["claim_structure", "claim_id", [claim, eventClaim]],
    ["library_paragraph_review", "paragraph_id", [paragraph]],
    ["library_review_coverage", "book_key", [book]],
    ["library_source_link", "source_id", [source]],
    ["person_event", "id", [participation]],
    ["fact_claim", "id", [claim, eventClaim, hiddenClaim]],
    ["event", "id", [event]],
    ["person", "id", [personA, personB, personC]],
    ["source_text", "source_id", [source]],
    ["source", "id", [source]],
    ["library_paragraph", "id", [paragraph]],
    ["library_section", "id", [section]],
    ["library_book", "book_key", [book]],
    ["library_asset", "id", [sha("asset")]],
  ])
    await db
      .execute(
        "DELETE FROM `" +
          table +
          "` WHERE `" +
          column +
          "` IN (" +
          values.map(() => "?").join(",") +
          ")",
        values,
      )
      .catch((error) => {
        cleanupFailure ??= error;
      });
  connection.release();
  if (app) await app.close();
  else await db.onModuleDestroy();
  if (primaryFailure || cleanupFailure) throw primaryFailure ?? cleanupFailure;
}
