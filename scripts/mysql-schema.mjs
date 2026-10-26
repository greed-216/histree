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
export function schemaStatements(file, text) {
  const delimiter = file.endsWith("001-content.sql") ? "$$" : ";";
  text = text.replace(/^DELIMITER .*$/gm, "");
  const statements = [];
  let buffer = "",
    quote = "";
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quote) {
      buffer += char;
      if (char === "\\" && i + 1 < text.length) buffer += text[++i];
      else if (char === quote) {
        if (text[i + 1] === quote) buffer += text[++i];
        else quote = "";
      }
      continue;
    }
    if (char === "'" || char === '"' || char === "`") {
      quote = char;
      buffer += char;
      continue;
    }
    if (char === "-" && text[i + 1] === "-" && /\s/.test(text[i + 2] ?? "")) {
      while (i < text.length && text[i] !== "\n") i++;
      buffer += "\n";
      continue;
    }
    if (char === "/" && text[i + 1] === "*") {
      const end = text.indexOf("*/", i + 2);
      if (end < 0) throw new Error("Unclosed schema comment");
      i = end + 1;
      buffer += " ";
      continue;
    }
    if (text.startsWith(delimiter, i)) {
      if (buffer.trim()) statements.push(buffer.trim());
      buffer = "";
      i += delimiter.length - 1;
    } else buffer += char;
  }
  if (quote) throw new Error("Unclosed schema literal");
  if (buffer.trim()) statements.push(buffer.trim());
  return statements;
}
export async function applySchema(connection, files = schemaFiles) {
  for (const file of files) {
    const text = await readFile(new URL("../" + file, import.meta.url), "utf8");
    for (const statement of schemaStatements(file, text))
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
