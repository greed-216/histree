/** Deterministic, resumable sidecar upgrade. Default prepares a bounded read-only plan. */
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import {
  legacyEvidence,
  validateDating,
} from "../packages/shared-types/dist/index.js";
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
const { createConnection } = require("mysql2/promise");
const args = process.argv.slice(2),
  arg = (name) =>
    args.includes(name) ? args[args.indexOf(name) + 1] : undefined;
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const envPath = arg("--mysql-env");
assert(envPath, "Explicit --mysql-env required");
const env = Object.fromEntries(
  (await readFile(envPath, "utf8"))
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s && !s.startsWith("#") && s.includes("="))
    .map((s) => {
      const p = s.indexOf("=");
      return [s.slice(0, p), s.slice(p + 1).replace(/^(['"])(.*)\1$/, "$2")];
    }),
);
const fingerprint = sha(
  [env.MYSQL_HOST, env.MYSQL_DATABASE, env.MYSQL_USER].join("\0"),
);
assert(
  ["disabled", "require", "verify-full"].includes(
    env.MYSQL_SSL_MODE ?? "disabled",
  ),
  "Invalid TLS mode",
);
const ssl =
  env.MYSQL_SSL_MODE === "verify-full"
    ? { rejectUnauthorized: true }
    : env.MYSQL_SSL_MODE === "require"
      ? { rejectUnauthorized: false }
      : undefined;
let db;
try {
  db = await createConnection({
    host: env.MYSQL_HOST,
    port: Number(env.MYSQL_PORT || 3306),
    user: env.MYSQL_USER,
    password: env.MYSQL_PASSWORD,
    database: env.MYSQL_DATABASE,
    charset: "utf8mb4",
    ...(ssl ? { ssl } : {}),
  });
  if (!args.includes("--apply")) {
    await db.query("SET TRANSACTION READ ONLY");
    await db.beginTransaction();
    const after = arg("--after") ?? "",
      limit = Number(arg("--limit") ?? 500);
    assert(Number.isInteger(limit) && limit > 0 && limit <= 5000);
    assert(!after || /^[a-f0-9-]{36}$/.test(after));
    const [claims] = await db.execute(
      `SELECT id,note FROM fact_claim WHERE status='published' AND id>? ORDER BY id LIMIT ${limit}`,
      [after],
    );
    const structures = claims.map((c) => {
      const e = legacyEvidence(c.note);
      return {
        claim_id: c.id,
        note_sha256: sha(c.note ?? ""),
        quote_text: e.quote,
        review_note: e.review,
        review_state: e.review_state,
      };
    });
    const datingPath = arg("--dating-plan"),
      datings = datingPath
        ? JSON.parse(await readFile(datingPath, "utf8")).map(validateDating)
        : [];
    const coveragePath = arg("--coverage-plan"),
      coverage = coveragePath
        ? JSON.parse(await readFile(coveragePath, "utf8"))
        : { coverage: [], paragraphs: [] };
    const plan = {
      format_version: 1,
      target_fingerprint: fingerprint,
      claim_structure: structures,
      event_dating: datings,
      coverage: coverage.coverage,
      paragraphs: coverage.paragraphs,
      next_after: claims.at(-1)?.id ?? null,
      model_calls: 0,
    };
    const output = arg("--output");
    assert(output, "--output required");
    const bytes = JSON.stringify(plan, null, 2) + "\n";
    await writeFile(output, bytes);
    await db.rollback();
    console.log(
      JSON.stringify({
        plan: output,
        sha256: sha(bytes),
        claims: structures.length,
        dating_estimates: datings.length,
        coverage_volumes: plan.coverage.length,
        next_after: plan.next_after,
        database_writes: 0,
        model_calls: 0,
      }),
    );
  } else {
    const input = arg("--plan"),
      expected = arg("--expected-sha256");
    assert(
      input && /^[a-f0-9]{64}$/.test(expected ?? ""),
      "Exact reviewed plan hash required",
    );
    const raw = await readFile(input);
    assert.equal(sha(raw), expected, "Plan changed");
    const plan = JSON.parse(raw);
    assert.equal(plan.format_version, 1);
    assert.equal(
      plan.target_fingerprint,
      fingerprint,
      "Database target changed",
    );
    const [[lock]] = await db.query(
      "SELECT GET_LOCK('histree-content-publish',0) acquired",
    );
    assert.equal(Number(lock.acquired), 1, "Another publisher is active");
    await db.beginTransaction();
    async function insert(table, row, identity) {
      const keys = Object.keys(identity),
        where = keys.map((k) => "`" + k + "`=?").join(" AND ");
      const [old] = await db.execute(
        "SELECT * FROM `" + table + "` WHERE " + where + " FOR UPDATE",
        Object.values(identity),
      );
      if (old.length) {
        for (const [key, value] of Object.entries(row))
          assert.deepEqual(
            old[0][key],
            value,
            "Existing sidecar differs: " + table,
          );
        return;
      }
      const allowed = {
        claim_structure: [
          "claim_id",
          "note_sha256",
          "quote_text",
          "review_note",
          "review_state",
        ],
        event_dating: [
          "id",
          "event_id",
          "claim_id",
          "earliest_year",
          "latest_year",
          "precision_kind",
          "era_key",
          "basis",
          "review_state",
        ],
        library_review_coverage: [
          "book_key",
          "source_version",
          "volume",
          "reviewed",
          "published",
          "no_new",
          "deferred",
          "audit_sha256",
          "audit_path",
        ],
        library_paragraph_review: [
          "paragraph_id",
          "content_sha256",
          "disposition",
          "reason",
          "audit_sha256",
        ],
      };
      const columns = Object.keys(row);
      assert(
        columns.every((key) => allowed[table]?.includes(key)),
        "Unexpected sidecar fields",
      );
      await db.execute(
        "INSERT INTO `" +
          table +
          "` (" +
          columns.map((k) => "`" + k + "`").join(",") +
          ") VALUES (" +
          columns.map(() => "?").join(",") +
          ")",
        Object.values(row),
      );
    }
    for (const row of plan.claim_structure) {
      const [[current]] = await db.execute(
        "SELECT note,status FROM fact_claim WHERE id=? FOR UPDATE",
        [row.claim_id],
      );
      assert(current && current.status === "published");
      assert.equal(sha(current.note ?? ""), row.note_sha256, "Claim changed");
      const e = legacyEvidence(current.note);
      assert.deepEqual(
        [row.quote_text, row.review_note, row.review_state],
        [e.quote, e.review, e.review_state],
        "Evidence was not a lossless deterministic split",
      );
      await insert("claim_structure", row, { claim_id: row.claim_id });
    }
    for (const input of plan.event_dating) {
      const row = validateDating(input);
      assert.equal(
        row.review_state,
        "reviewed",
        "Unreviewed dating cannot be published",
      );
      const [[basis]] = await db.execute(
        "SELECT c.id FROM fact_claim c JOIN event e ON e.id=c.subject_id WHERE c.id=? AND c.subject_table='event' AND c.subject_id=? AND c.status='published' AND e.status='published' AND e.start_year IS NULL FOR UPDATE",
        [row.claim_id, row.event_id],
      );
      assert(basis, "Dating evidence or unknown original year changed");
      const { precision, ...rest } = row;
      await insert(
        "event_dating",
        { ...rest, precision_kind: precision },
        { id: row.id },
      );
    }
    for (const row of plan.coverage) {
      const root =
        arg("--source-root") ?? new URL("../", import.meta.url).pathname;
      const { resolve, relative } = await import("node:path");
      const file = resolve(root, row.audit_path);
      assert(!relative(root, file).startsWith(".."));
      assert.equal(
        sha(await readFile(file)),
        row.audit_sha256,
        "Review audit changed",
      );
      const [[book]] = await db.execute(
        "SELECT source_version FROM library_book WHERE book_key=? AND status='available'",
        [row.book_key],
      );
      assert.equal(
        book?.source_version,
        row.source_version,
        "Corpus version changed",
      );
      await insert("library_review_coverage", row, {
        book_key: row.book_key,
        source_version: row.source_version,
        volume: row.volume,
      });
    }
    for (const row of plan.paragraphs) {
      const [[paragraph]] = await db.execute(
        "SELECT content_sha256 FROM library_paragraph WHERE id=?",
        [row.paragraph_id],
      );
      assert.equal(
        paragraph?.content_sha256,
        row.content_sha256,
        "Reader paragraph changed",
      );
      await insert("library_paragraph_review", row, {
        paragraph_id: row.paragraph_id,
      });
    }
    await db.commit();
    console.log(
      JSON.stringify({
        verified: true,
        plan_sha256: expected,
        model_calls: 0,
        legacy_rows_changed: 0,
      }),
    );
  }
} catch (error) {
  await db?.rollback();
  console.error(
    JSON.stringify({
      failed: true,
      reason:
        error instanceof assert.AssertionError
          ? error.message
          : "Structure upgrade failed; connection details suppressed",
    }),
  );
  process.exitCode = 1;
} finally {
  await db?.end();
}
