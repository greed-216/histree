/** Native reading-layout regression. Disposable loopback MySQL only; exact owned-ID cleanup. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
const { ConfigService } = require("@nestjs/config");
const { MysqlService } = require("./dist/modules/mysql/mysql.service.js");
const { LibraryService } = require("./dist/modules/library/library.service.js");
assert(["localhost", "127.0.0.1"].includes(process.env.MYSQL_HOST));
assert.match(process.env.MYSQL_DATABASE ?? "", /^histree_test_[a-z0-9_]+$/);
const db = new MysqlService(new ConfigService(process.env));
const library = new LibraryService(db);
const sha = (text) => createHash("sha256").update(text).digest("hex");
const data = JSON.parse(
  await readFile(
    new URL("../apps/api/src/data/shiji-reading-layout.json", import.meta.url),
    "utf8",
  ),
);
const source = Array.from(
  await readFile(
    new URL(
      "../resources/originals/twenty-four-histories/01史记-EPUB全文.txt",
      import.meta.url,
    ),
    "utf8",
  ),
);
const corpus = gunzipSync(
  await readFile(
    new URL(
      "../resources/derived/history-library/shiji/paragraphs.jsonl.gz",
      import.meta.url,
    ),
  ),
)
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse);
const wanted = new Set([
  "shiji-174f8dfa444c-p001800",
  "shiji-174f8dfa444c-p001413",
  "shiji-174f8dfa444c-p001422",
]);
const last = corpus
  .filter((p) => p.volume_candidate === 22 && p.kind === "table_row")
  .slice(0, 48);
last.forEach((p) => wanted.add(p.id));
for (const id of [...wanted])
  data.tables[data.paragraphs[id].table_id].header_paragraph_ids.forEach(
    (pid) => wanted.add(pid),
  );
const rows = corpus.filter((p) => wanted.has(p.id));
const sections = data.chapters.filter((c) =>
  rows.some((p) => p.section_id === c.section_id),
);
const asset = sha("native-shiji-reading-layout-owned-fixture");
const tables = {
  library_book: "book_key",
  library_asset: "id",
  library_section: "id",
  library_paragraph: "id",
};
const baseline = {};
let owned = false,
  checks = 0;
try {
  for (const [table, key] of Object.entries(tables))
    baseline[table] = new Set(
      (await db.rows(`SELECT ${key} AS k FROM ${table}`)).map((r) => r.k),
    );
  assert(!baseline.library_book.has("shiji"));
  assert(!baseline.library_asset.has(asset));
  assert(sections.every((s) => !baseline.library_section.has(s.section_id)));
  assert(rows.every((p) => !baseline.library_paragraph.has(p.id)));
  owned = true;
  await db.execute(
    "INSERT INTO library_book VALUES('shiji','史记排版合成夹具',?,0,?,?,?,JSON_OBJECT(),'available')",
    [data.source_version, sections.length, rows.length, sha("fixture")],
  );
  await db.execute(
    "INSERT INTO library_asset VALUES(?, 'synthetic-layout-fixture.txt', ?)",
    [asset, data.source_sha256],
  );
  for (const section of sections)
    await db.execute(
      "INSERT INTO library_section VALUES(?,?,?,'原卷题',?,'volume',0,JSON_OBJECT())",
      [section.section_id, "shiji", section.volume, section.volume],
    );
  for (const [ordinal, p] of rows.entries()) {
    const content = source
      .slice(p.locator.char_start, p.locator.char_end)
      .join("");
    assert.equal(sha(content), data.paragraphs[p.id].content_sha256);
    await db.execute(
      "INSERT INTO library_paragraph VALUES(?,?,?,?,?,?,?,?,?,?,JSON_ARRAY())",
      [
        p.id,
        "shiji",
        p.section_id,
        ordinal,
        p.kind,
        content,
        sha(content),
        asset,
        p.locator.char_start,
        p.locator.char_end,
      ],
    );
  }
  const book = await library.book("shiji");
  assert.equal(book.book.divisions.length, 5);
  assert(book.sections.every((s) => s.division === "biao" && s.display_title));
  checks++;
  const section = sections.find((s) => s.volume === 22).section_id;
  const page = await library.section("shiji", section, { page: "1" });
  assert(
    page.paragraphs.length > 0 && page.paragraphs.every((p) => p.table_row),
  );
  const header = "shiji-174f8dfa444c-p002487";
  const tid = data.paragraphs[header].table_id;
  assert.equal(page.table_headers[tid][0].id, header);
  checks++;
  const leading = await library.section(
    "shiji",
    sections.find((s) => s.volume === 16).section_id,
    { paragraph: "shiji-174f8dfa444c-p001800" },
  );
  const row = leading.paragraphs.find((p) =>
    p.id.endsWith("p001800"),
  ).table_row;
  assert.equal(row.cells[row.fragments[0][0]][0], 2);
  checks++;
  const split = await library.section(
    "shiji",
    sections.find((s) => s.volume === 14).section_id,
  );
  const parts = split.paragraphs.filter((p) =>
    ["shiji-174f8dfa444c-p001413", "shiji-174f8dfa444c-p001422"].includes(p.id),
  );
  assert.equal(parts.length, 2);
  assert.equal(parts[0].table_row.row_index, parts[1].table_row.row_index);
  checks++;
  await db.execute(
    "UPDATE library_paragraph SET content='changed',content_sha256=? WHERE id=?",
    [sha("changed"), header],
  );
  const drift = await library.section("shiji", section, { page: "1" });
  assert(drift.paragraphs.every((p) => !p.table_row));
  assert.deepEqual(drift.table_headers, {});
  checks++;
  await db.execute(
    "UPDATE library_book SET source_version='unbound-edition' WHERE book_key='shiji'",
  );
  const unbound = await library.book("shiji");
  assert(!unbound.book.divisions);
  assert(unbound.sections.every((s) => !s.display_title));
  checks++;
  console.log(
    JSON.stringify({
      native_mysql: true,
      reading_layout_checks: checks,
      production_env_reads: 0,
      schema_changes: 0,
    }),
  );
} finally {
  if (owned) {
    for (const p of rows)
      await db.execute("DELETE FROM library_paragraph WHERE id=?", [p.id]);
    for (const s of sections)
      await db.execute("DELETE FROM library_section WHERE id=?", [
        s.section_id,
      ]);
    await db.execute("DELETE FROM library_asset WHERE id=?", [asset]);
    await db.execute("DELETE FROM library_book WHERE book_key='shiji'");
    for (const [table, key] of Object.entries(tables))
      assert.deepEqual(
        new Set(
          (await db.rows(`SELECT ${key} AS k FROM ${table}`)).map((r) => r.k),
        ),
        baseline[table],
      );
    console.log(
      "PASS: exact reading fixture cleanup; all preexisting library IDs preserved",
    );
  }
  await db.onModuleDestroy();
}
