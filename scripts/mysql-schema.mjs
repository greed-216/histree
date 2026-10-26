/** Single ordered manifest; CLI bootstrap only accepts an empty disposable local database. */
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
export const schemaFiles = [
  "database/mysql/001-content.sql",
  "database/mysql/002-ai-quota.sql",
  "database/mysql/003-guess-bank.sql",
  "database/mysql/004-guess-clues.sql",
  "apps/api/mysql/migrations/20261019_feedback.sql",
  "apps/api/mysql/migrations/20261019_source_text.sql",
  "apps/api/mysql/migrations/20261019_library.sql",
  "database/mysql/005-content-structure.sql",
];
export async function applySchema(connection, files = schemaFiles) {
  for (const file of files) {
    const text = await readFile(new URL("../" + file, import.meta.url), "utf8");
    const delimiter = file.endsWith("001-content.sql") ? "$$" : ";";
    for (const statement of text
      .replace(/^DELIMITER .*$/gm, "")
      .split(delimiter)
      .map((s) => s.trim())
      .filter(Boolean))
      await connection.query(statement);
  }
}
if (
  process.argv[1] &&
  import.meta.url === new URL("file://" + process.argv[1]).href
) {
  if (!process.argv.includes("--bootstrap-test")) {
    for (const file of schemaFiles)
      console.log(
        JSON.stringify({
          file,
          sha256: createHash("sha256")
            .update(await readFile(new URL("../" + file, import.meta.url)))
            .digest("hex"),
        }),
      );
  } else {
    if (
      !["127.0.0.1", "localhost"].includes(process.env.MYSQL_HOST) ||
      !/^histree_test_[a-z0-9_]+$/.test(process.env.MYSQL_DATABASE ?? "")
    )
      throw new Error("Disposable local database required");
    const require = createRequire(
        new URL("../apps/api/package.json", import.meta.url),
      ),
      { createConnection } = require("mysql2/promise");
    const db = await createConnection({
      host: process.env.MYSQL_HOST,
      port: Number(process.env.MYSQL_PORT || 3306),
      user: process.env.MYSQL_USER,
      password: process.env.MYSQL_PASSWORD,
      database: process.env.MYSQL_DATABASE,
    });
    try {
      const [tables] = await db.query("SHOW TABLES");
      if (tables.length)
        throw new Error("Bootstrap requires an empty database");
      await applySchema(db);
      console.log("PASS: disposable schema bootstrap");
    } finally {
      await db.end();
    }
  }
}
