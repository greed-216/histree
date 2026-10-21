// Reviewed GAME-only repair. Dry-run by default; no model or historical-table writes.
import { createRequire } from "node:module";
import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
const { z } = require("zod");
const {
  makeClueProfile,
  validateCachedClues,
  CLUE_VERSION,
} = require("./dist/modules/ask/guess-clues.js");
const revision = z.string().regex(/^[a-f0-9]{64}$/),
  id = z.string().uuid();
const schema = z
  .object({
    reviewed: z.literal(true),
    reason: z.string().min(20),
    entries: z
      .array(
        z
          .object({
            person_id: id,
            name: z.string().min(1),
            profile_revision: revision,
            result_revision: revision,
            aliases: z.array(z.string().min(1)),
            difficulty: z.enum(["easy", "hard"]).optional(),
            reason: z.string().min(10),
          })
          .strict(),
      )
      .min(1),
    merges: z.array(
      z
        .object({
          duplicate_id: id,
          duplicate_name: z.string(),
          duplicate_revision: revision,
          target_id: id,
          reason: z.string().min(20),
        })
        .strict(),
    ),
  })
  .strict();
const profileSql = `SELECT c.id,c.canonical_person_id,c.knowledge_revision,c.difficulty_revision,c.difficulty game_difficulty,
 COALESCE(p.name,c.name) name,JSON_MERGE_PRESERVE(COALESCE(p.aliases,JSON_ARRAY()),c.aliases) aliases,
 COALESCE(p.courtesy_name,c.courtesy_name) courtesy_name,COALESCE(NULLIF(c.era,''),p.era) era,
 c.period_from,c.period_to,COALESCE(p.birth_year,c.birth_year) birth_year,COALESCE(p.death_year,c.death_year) death_year,
 COALESCE(NULLIF(c.description,''),p.description,'') description
 FROM guess_character c LEFT JOIN person p ON p.id=c.canonical_person_id WHERE c.id=?`;
export async function repairGuessIdentities(
  raw,
  { connection: conn, apply = false, backupPath } = {},
) {
  const plan = schema.parse(raw),
    targets = new Set(plan.entries.map((e) => e.person_id)),
    sources = new Set(plan.merges.map((m) => m.duplicate_id));
  if (
    targets.size !== plan.entries.length ||
    sources.size !== plan.merges.length ||
    [...sources].some((id) => targets.has(id)) ||
    plan.merges.some((m) => !targets.has(m.target_id))
  )
    throw Error("Conflicting repair identities");
  if (apply && !backupPath)
    throw Error("Apply requires a private before-state backup");
  const ids = [...targets, ...sources].sort(),
    marks = ids.map(() => "?").join(",");
  const query = async (sql, args = []) => {
    const [rows] = await conn.execute(sql, args);
    return rows;
  };
  const report = {
    mode: apply ? "applied" : "read-only",
    modelCalls: 0,
    merged: 0,
    aliasesUpdated: 0,
    cacheReused: 0,
    clueLevelsChanged: 0,
    questionLevelsChanged: 0,
    bankLevelsChanged: 0,
    protectedFeedback: [],
    details: [],
  };
  await conn.beginTransaction();
  try {
    // Same row locks used by live feedback. Freeze the full reviewed batch before any writes.
    const characters = await query(
      `SELECT * FROM guess_character WHERE id IN (${marks}) ORDER BY id FOR UPDATE`,
      ids,
    );
    if (characters.length !== ids.length)
      throw Error("Unknown repair character");
    const byId = new Map(characters.map((c) => [c.id, c]));
    const canonical = [
      ...new Set(characters.map((c) => c.canonical_person_id).filter(Boolean)),
    ].sort();
    if (canonical.length)
      await query(
        `SELECT id FROM person WHERE id IN (${canonical.map(() => "?").join(",")}) ORDER BY id FOR SHARE`,
        canonical,
      );
    const banks = canonical.length
      ? await query(
          `SELECT * FROM guess_bank WHERE person_id IN (${canonical.map(() => "?").join(",")}) ORDER BY person_id FOR UPDATE`,
          canonical,
        )
      : [];
    const bankById = new Map(banks.map((b) => [b.person_id, b]));
    const caches = await query(
      `SELECT * FROM guess_clue_set WHERE person_id IN (${marks}) ORDER BY person_id,profile_revision,generator_version FOR UPDATE`,
      ids,
    );
    if (
      caches.some(
        (c) =>
          c.status === "generating" &&
          new Date(c.lease_until + "Z") > new Date(),
      )
    )
      throw Error("Active generation lease; retry after it completes");
    const feedback = {};
    for (const table of [
      "guess_clue_feedback",
      "guess_question_feedback",
      "guess_difficulty_feedback",
    ])
      feedback[table] = await query(
        `SELECT * FROM ${table} WHERE person_id IN (${marks})`,
        ids,
      );
    const profiles = new Map();
    for (const personId of ids)
      profiles.set(
        personId,
        makeClueProfile((await query(profileSql, [personId]))[0]),
      );
    const ready = (p) =>
      caches.find(
        (c) =>
          c.person_id === p.person.id &&
          c.profile_revision === p.revision &&
          c.generator_version === CLUE_VERSION &&
          c.status === "ready",
      );
    for (const m of plan.merges) {
      const profile = profiles.get(m.duplicate_id),
        target = byId.get(m.target_id);
      if (
        profile.person.name !== m.duplicate_name ||
        profile.revision !== m.duplicate_revision
      )
        throw Error("Stale duplicate identity: " + m.duplicate_id);
      if (!target.enabled) throw Error("Merge target is disabled");
      // These are reviewed identity mappings, never guesses based on equal name strings.
      report.merged += Number(!!byId.get(m.duplicate_id).enabled);
    }
    const changes = [];
    for (const e of plan.entries) {
      const c = byId.get(e.person_id),
        before = profiles.get(e.person_id);
      if (
        !c.enabled ||
        before.person.name !== e.name ||
        ![e.profile_revision, e.result_revision].includes(before.revision)
      )
        throw Error("Stale target identity: " + e.person_id);
      const aliases = [...new Set([...c.aliases, ...e.aliases])];
      const after = makeClueProfile({
        ...before.person,
        aliases: [...before.person.aliases, ...aliases],
      });
      if (after.revision !== e.result_revision)
        throw Error("Unreviewed result identity: " + e.person_id);
      let cache = ready(after) || ready(before);
      if (!cache) {
        for (const m of plan.merges.filter(
          (m) => m.target_id === e.person_id,
        )) {
          cache = ready(profiles.get(m.duplicate_id));
          if (cache) break;
        }
      }
      if (cache) validateCachedClues(cache.clues, after); // Added short answers must not leak through existing hints.
      if (!cache && plan.merges.some((m) => m.target_id === e.person_id))
        throw Error("Merge would lose playable clues");
      const hasFeedback = (table) =>
        feedback[table].some((f) => f.person_id === e.person_id);
      const changedAliases = after.revision !== before.revision;
      const levelChanges = [];
      for (const [column, rev, scope, votes, table] of [
        [
          "difficulty",
          "difficulty_revision",
          "vote_clue_revision",
          ["easy_votes", "right_votes", "hard_votes"],
          "guess_clue_feedback",
        ],
        [
          "question_difficulty",
          "question_revision",
          "question_vote_clue_revision",
          [
            "question_easy_votes",
            "question_right_votes",
            "question_hard_votes",
          ],
          "guess_question_feedback",
        ],
      ]) {
        if (!e.difficulty || c[column] === e.difficulty) continue;
        if (
          c[rev] !== 1 ||
          c[scope] ||
          votes.some((v) => c[v]) ||
          hasFeedback(table)
        ) {
          report.protectedFeedback.push({ id: e.person_id, mode: column });
          continue;
        }
        levelChanges.push({ column, rev });
      }
      const bank = bankById.get(c.canonical_person_id);
      let changeBank = false;
      if (e.difficulty && bank && bank.difficulty !== e.difficulty) {
        if (
          bank.revision !== 1 ||
          bank.easy_votes ||
          bank.right_votes ||
          bank.hard_votes ||
          feedback.guess_difficulty_feedback.some(
            (f) => f.person_id === bank.person_id,
          )
        )
          report.protectedFeedback.push({ id: e.person_id, mode: "bank" });
        else changeBank = true;
      }
      changes.push({
        e,
        c,
        before,
        after,
        aliases,
        cache,
        changedAliases,
        levelChanges,
        changeBank,
      });
      report.aliasesUpdated += Number(changedAliases);
      report.cacheReused += Number(!!cache && !ready(after));
      for (const change of levelChanges)
        report[
          change.column === "difficulty"
            ? "clueLevelsChanged"
            : "questionLevelsChanged"
        ]++;
      report.bankLevelsChanged += Number(changeBank);
    }
    // Backup is created before mutation and includes immutable old caches and all feedback.
    if (apply)
      await writeFile(
        backupPath,
        JSON.stringify(
          {
            at: new Date().toISOString(),
            plan,
            characters,
            banks,
            caches,
            feedback,
          },
          null,
          2,
        ) + "\n",
        { mode: 0o600, flag: "wx" },
      );
    for (const change of changes) {
      const {
        e,
        after,
        aliases,
        cache,
        changedAliases,
        levelChanges,
        changeBank,
      } = change;
      if (apply) {
        if (changedAliases)
          await query("UPDATE guess_character SET aliases=? WHERE id=?", [
            JSON.stringify(aliases),
            e.person_id,
          ]);
        for (const { column, rev } of levelChanges)
          await query(
            `UPDATE guess_character SET ${column}=?,${rev}=${rev}+1 WHERE id=?`,
            [e.difficulty, e.person_id],
          );
        if (changeBank)
          await query(
            "UPDATE guess_bank SET difficulty=?,revision=revision+1 WHERE person_id=?",
            [e.difficulty, change.c.canonical_person_id],
          );
        if (cache && !ready(after))
          await query(
            `INSERT INTO guess_clue_set(person_id,profile_revision,generator_version,status,clues,provenance) VALUES(?,?,?,'ready',?,?)
     ON DUPLICATE KEY UPDATE status='ready',clues=VALUES(clues),provenance=VALUES(provenance),lease_token=NULL,lease_until=NULL,retry_after=NULL`,
            [
              e.person_id,
              after.revision,
              CLUE_VERSION,
              JSON.stringify(cache.clues),
              JSON.stringify({
                ...(cache.provenance || {}),
                identity_repair: {
                  from_person_id: cache.person_id,
                  from_profile_revision: cache.profile_revision,
                  reason: e.reason,
                },
              }),
            ],
          );
      }
      report.details.push({
        id: e.person_id,
        name: e.name,
        profile_revision: after.revision,
        cacheReady: !!cache,
      });
    }
    if (apply) {
      for (const m of plan.merges)
        await query("UPDATE guess_character SET enabled=0 WHERE id=?", [
          m.duplicate_id,
        ]);
      for (const change of changes) {
        const saved = makeClueProfile(
          (await query(profileSql, [change.e.person_id]))[0],
        );
        if (saved.revision !== change.after.revision)
          throw Error("Repair readback mismatch");
        if (change.cache) {
          const rows = await query(
            "SELECT clues FROM guess_clue_set WHERE person_id=? AND profile_revision=? AND generator_version=? AND status='ready'",
            [change.e.person_id, saved.revision, CLUE_VERSION],
          );
          if (!rows[0]) throw Error("Cache readback missing");
          validateCachedClues(rows[0].clues, saved);
        }
      }
      const disabled = await query(
        `SELECT id FROM guess_character WHERE id IN (${[...sources].map(() => "?").join(",") || "NULL"}) AND enabled=1`,
        [...sources],
      );
      if (disabled.length) throw Error("Duplicate still playable");
      await conn.commit();
    } else await conn.rollback();
    return report;
  } catch (error) {
    await conn.rollback();
    throw error;
  }
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const args = process.argv.slice(2),
    get = (k) => args[args.indexOf(k) + 1],
    apply = args.includes("--apply");
  if (!args.includes("--input")) throw Error("Required --input FILE");
  const bytes = await readFile(get("--input"));
  if (
    apply &&
    (!args.includes("--sha256") ||
      createHash("sha256").update(bytes).digest("hex") !== get("--sha256"))
  )
    throw Error("Reviewed repair plan changed");
  const { createConnection } = require("mysql2/promise");
  const env = process.env,
    mode = env.MYSQL_SSL_MODE || "disabled";
  if (!["disabled", "require", "verify-full"].includes(mode))
    throw Error("Invalid TLS mode");
  const conn = await createConnection({
    host: env.MYSQL_HOST,
    port: Number(env.MYSQL_PORT || 3306),
    database: env.MYSQL_DATABASE,
    user: env.MYSQL_USER,
    password: env.MYSQL_PASSWORD,
    charset: "utf8mb4",
    timezone: "Z",
    dateStrings: true,
    ...(mode === "disabled"
      ? {}
      : { ssl: { rejectUnauthorized: mode === "verify-full" } }),
  });
  try {
    await conn.query("SET SESSION innodb_lock_wait_timeout=5");
    const report = await repairGuessIdentities(JSON.parse(bytes), {
      connection: conn,
      apply,
      backupPath: args.includes("--backup") ? get("--backup") : undefined,
    });
    if (args.includes("--report"))
      await writeFile(get("--report"), JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify(report));
  } finally {
    await conn.end();
  }
}
