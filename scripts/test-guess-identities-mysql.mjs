/** Native MySQL atomic repair regressions. Synthetic fixtures, no model calls. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { randomUUID, createHash } from "node:crypto";
import { readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { repairGuessIdentities } from "./repair-guess-identities.mjs";
const r = createRequire(new URL("../apps/api/package.json", import.meta.url));
const { createConnection } = r("mysql2/promise");
const { makeClueProfile } = r("./dist/modules/ask/guess-clues.js");
const { ConfigService } = r("@nestjs/config");
const { MysqlService } = r("./dist/modules/mysql/mysql.service.js");
const { GuessClueStore } = r("./dist/modules/ask/guess-clue-store.js");
const { GuessGameLibrary } = r("./dist/modules/ask/guess-game-library.js");
const env = process.env;
assert.match(env.MYSQL_DATABASE || "", /^histree_test_[a-z0-9_]+$/);
assert(["127.0.0.1", "localhost"].includes(env.MYSQL_HOST));
const conn = await createConnection({
  host: env.MYSQL_HOST,
  port: Number(env.MYSQL_PORT || 3306),
  database: env.MYSQL_DATABASE,
  user: env.MYSQL_USER,
  password: env.MYSQL_PASSWORD,
  charset: "utf8mb4",
  dateStrings: true,
});
const query = async (sql, args = []) => {
  const [rows] = await conn.execute(sql, args);
  return rows;
};
const db = new MysqlService(new ConfigService(env)),
  ids = Array.from({ length: 4 }, () => randomUUID()),
  [target, duplicate, protectedId, homonym] = ids;
const backup = join(tmpdir(), "histree-identity-" + randomUUID() + ".json"),
  importPath = backup + ".characters.json",
  seedPath = backup + ".seed.json";
let checks = 0;
const clues = [
  "我曾离开家乡，走向另一个城市。",
  "我曾在地方担任管理事务的官职。",
  "我与同僚一起商议过当时的政务。",
  "我曾经历一场影响后人的变故。",
  "我留下过被后世记录的言行事迹。",
  "我的生平见于后人编写的史书。",
].map((text) => ({
  text,
  explanation: "仅用于隔离测试的合成解释，不构成真实历史资料。",
}));
const profile = (id, name, canonical, aliases = []) =>
  makeClueProfile({
    id,
    name,
    canonical_person_id: canonical,
    aliases,
    description: "",
    era: null,
    birth_year: null,
    death_year: null,
    period_from: null,
    period_to: null,
    knowledge_revision: 1,
  });
try {
  assert.equal((await query("SELECT COUNT(*) n FROM person"))[0].n, 0);
  for (const [id, name] of [
    [target, "李世民（李渊子）"],
    [protectedId, "高长恭（齐兰陵王）"],
    [homonym, "杨广（杨亮子）"],
  ]) {
    await query(
      "INSERT INTO person(id,name,status,aliases) VALUES(?,?,'published',JSON_ARRAY())",
      [id, name],
    );
    await query(
      "INSERT INTO guess_bank(person_id,difficulty) VALUES(?,'hard')",
      [id],
    );
    await query(
      "INSERT INTO guess_character(id,canonical_person_id,name,aliases,description,difficulty,question_difficulty) VALUES(?,?,?,JSON_ARRAY(),'','hard','hard')",
      [id, id, name],
    );
  }
  await query(
    "INSERT INTO guess_character(id,name,aliases,description,difficulty,question_difficulty) VALUES(?,'李世民',JSON_ARRAY('唐太宗'),'','easy','easy')",
    [duplicate],
  );
  const before = profile(target, "李世民（李渊子）", target),
    source = profile(duplicate, "李世民", null, ["唐太宗"]),
    protectedBefore = profile(protectedId, "高长恭（齐兰陵王）", protectedId);
  const after = profile(target, before.person.name, target, [
    "李世民",
    "唐太宗",
  ]);
  // The canonical target has no cache: it must inherit the reviewed duplicate's cached six clues.
  for (const p of [source, protectedBefore])
    await query(
      "INSERT INTO guess_clue_set(person_id,profile_revision,generator_version,status,clues,provenance) VALUES(?,?,2,'ready',?,?)",
      [
        p.person.id,
        p.revision,
        JSON.stringify(clues),
        JSON.stringify({
          kind: "general_knowledge",
          method: "codex_direct",
          reviewed: true,
        }),
      ],
    );
  const hash = (s) => createHash("sha256").update(s).digest("hex");
  for (const id of [duplicate, protectedId])
    await query(
      "INSERT INTO guess_clue_feedback(game_hash,person_id,clue_revision,difficulty_revision,actor_hash,rating,guesses,unlocked,outcome) VALUES(?,?,?,1,?,'hard',1,2,'revealed')",
      [hash("game" + id), id, hash("clues" + id), hash("actor" + id)],
    );
  await query("UPDATE guess_character SET hard_votes=1 WHERE id=?", [
    protectedId,
  ]);
  const plan = {
    reviewed: true,
    reason: "合成测试中经人工明确确认的游戏同人映射，保留原记录。",
    entries: [
      {
        person_id: target,
        name: before.person.name,
        profile_revision: before.revision,
        result_revision: after.revision,
        aliases: ["李世民", "唐太宗"],
        difficulty: "easy",
        reason: "合成测试，修正已核对的身份后缀误分。",
      },
      {
        person_id: protectedId,
        name: protectedBefore.person.name,
        profile_revision: protectedBefore.revision,
        result_revision: protectedBefore.revision,
        aliases: [],
        difficulty: "easy",
        reason: "合成测试，保留玩家已参与评分的难度。",
      },
    ],
    merges: [
      {
        duplicate_id: duplicate,
        duplicate_name: "李世民",
        duplicate_revision: source.revision,
        target_id: target,
        reason: "合成测试：已核实为同一游戏人物，原始线索与评分保留归档。",
      },
    ],
  };
  const dry = await repairGuessIdentities(plan, { connection: conn });
  assert.equal(dry.merged, 1);
  assert.equal(dry.protectedFeedback.length, 1);
  assert.equal(
    (
      await query("SELECT enabled FROM guess_character WHERE id=?", [duplicate])
    )[0].enabled,
    1,
  );
  checks++;
  const stale = structuredClone(plan);
  stale.merges[0].duplicate_revision = "0".repeat(64);
  await assert.rejects(
    repairGuessIdentities(stale, { connection: conn }),
    /Stale/,
  );
  checks++;
  // Failure after target updates/cache writes must roll back the entire transaction.
  const failing = {
    beginTransaction: () => conn.beginTransaction(),
    commit: () => conn.commit(),
    rollback: () => conn.rollback(),
    execute: (sql, args) => {
      if (sql.startsWith("UPDATE guess_character SET enabled=0"))
        throw Error("Injected repair failure");
      return conn.execute(sql, args);
    },
  };
  await assert.rejects(
    repairGuessIdentities(plan, {
      connection: failing,
      apply: true,
      backupPath: backup,
    }),
    /Injected/,
  );
  assert.equal(
    (
      await query("SELECT difficulty FROM guess_character WHERE id=?", [target])
    )[0].difficulty,
    "hard",
  );
  assert.equal(
    (
      await query("SELECT COUNT(*) n FROM guess_clue_set WHERE person_id=?", [
        target,
      ])
    )[0].n,
    0,
  );
  checks++;
  await rm(backup);
  const applied = await repairGuessIdentities(plan, {
    connection: conn,
    apply: true,
    backupPath: backup,
  });
  assert.equal(applied.merged, 1);
  assert.equal(applied.cacheReused, 1);
  assert.equal(applied.clueLevelsChanged, 1);
  checks++;
  assert.equal(
    (
      await query(
        "SELECT difficulty,hard_votes FROM guess_character WHERE id=?",
        [protectedId],
      )
    )[0].difficulty,
    "hard",
  );
  assert.equal(
    (await query("SELECT COUNT(*) n FROM guess_clue_feedback"))[0].n,
    2,
  );
  assert.equal(
    (
      await query("SELECT enabled FROM guess_character WHERE id=?", [duplicate])
    )[0].enabled,
    0,
  );
  checks++;
  assert.equal(
    (
      await query("SELECT difficulty FROM guess_character WHERE id=?", [
        homonym,
      ])
    )[0].difficulty,
    "hard",
  );
  assert.equal((await query("SELECT COUNT(*) n FROM person"))[0].n, 3);
  checks++;
  const saved = (
    await query(
      "SELECT clues,provenance FROM guess_clue_set WHERE person_id=? AND profile_revision=?",
      [target, after.revision],
    )
  )[0];
  assert.deepEqual(saved.clues, clues);
  assert.equal(saved.provenance.method, "codex_direct");
  assert.equal(saved.provenance.identity_repair.from_person_id, duplicate);
  checks++;
  const store = new GuessClueStore(db),
    sets = {
      ready: async (p) =>
        (
          await query(
            "SELECT clues FROM guess_clue_set WHERE person_id=? AND profile_revision=? AND status='ready'",
            [p.person.id, p.revision],
          )
        )[0] || null,
    };
  assert(!(await store.readyPeople(AbortSignal.timeout(10000))).has(duplicate));
  checks++;
  const library = new GuessGameLibrary(db, { prepare: async () => {} }, sets);
  const catalogue = await library.catalogue(AbortSignal.timeout(10000));
  const cluePeople = [
    ...(await store.candidates(
      { difficulty: "easy" },
      AbortSignal.timeout(10000),
      true,
    )),
    ...(await store.candidates(
      { difficulty: "hard" },
      AbortSignal.timeout(10000),
      true,
    )),
  ];
  assert.deepEqual(
    catalogue.map((p) => p.id).sort(),
    cluePeople.map((p) => p.id).sort(),
  );
  assert(catalogue.some((p) => p.id === target));
  assert(!catalogue.some((p) => p.id === duplicate));
  checks++;
  const character = {
    id: duplicate,
    canonical_person_id: null,
    name: "李世民",
    aliases: ["唐太宗"],
    era: "唐",
    birth_year: null,
    death_year: null,
    description: "",
    difficulty: "easy",
  };
  await writeFile(importPath, JSON.stringify([character]));
  await writeFile(
    seedPath,
    JSON.stringify({
      entries: [
        {
          person_id: duplicate,
          profile_revision: source.revision,
          generator_version: 2,
          clues,
        },
      ],
    }),
  );
  const importer = (file) =>
    execFileSync(
      process.execPath,
      [
        new URL("./prepare-guess-clues.mjs", import.meta.url).pathname,
        "--apply",
        "--import",
        file,
        "--seed",
        seedPath,
        "--difficulty",
        "easy",
        "--limit",
        "1",
      ],
      { env: { ...env, HISTREE_ASK_ENABLED: "false" }, stdio: "pipe" },
    );
  importer(importPath);
  assert.equal(
    (
      await query("SELECT enabled FROM guess_character WHERE id=?", [duplicate])
    )[0].enabled,
    0,
  );
  checks++;
  const newId = randomUUID();
  await writeFile(importPath, JSON.stringify([{ ...character, id: newId }]));
  assert.throws(() => importer(importPath), /Command failed/);
  assert.equal(
    (
      await query("SELECT COUNT(*) n FROM guess_character WHERE id=?", [newId])
    )[0].n,
    0,
  );
  checks++;
  const repeat = await repairGuessIdentities(plan, { connection: conn });
  for (const k of [
    "merged",
    "aliasesUpdated",
    "cacheReused",
    "clueLevelsChanged",
    "questionLevelsChanged",
    "bankLevelsChanged",
  ])
    assert.equal(repeat[k], 0, k);
  checks++;
  const backed = JSON.parse(await readFile(backup, "utf8"));
  assert.equal(backed.feedback.guess_clue_feedback.length, 2);
  assert.equal(backed.characters.find((c) => c.id === duplicate).enabled, 1);
  checks++;
  console.log(
    JSON.stringify({
      status: "passed",
      checks,
      environment: "isolated native MySQL 8",
      modelCalls: 0,
    }),
  );
} finally {
  for (const id of ids)
    await query("DELETE FROM guess_character WHERE id=?", [id]);
  for (const id of [target, protectedId, homonym])
    await query("DELETE FROM person WHERE id=?", [id]);
  await rm(backup, { force: true });
  await rm(importPath, { force: true });
  await rm(seedPath, { force: true });
  await conn.end();
  await db.onModuleDestroy();
}
