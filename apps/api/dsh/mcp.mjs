import { readFile, appendFile } from 'node:fs/promises';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { createRemoteLibrary } from './remote-library.mjs';
import { createLibrary } from './retrieval.mjs';

const manifest = JSON.parse(
  await readFile(process.env.HISTREE_SNAPSHOT, 'utf8'),
);
const library =
  manifest.mode === 'remote'
    ? await createRemoteLibrary(manifest, process.env.HISTREE_RETRIEVED)
    : createLibrary(manifest);
const server = new McpServer({ name: 'histree', version: '1.0.0' });
const kind = z.enum(['person', 'event', 'topic']);
const subject = z.enum([
  'person',
  'event',
  'topic',
  'person_relationship',
  'person_event',
  'event_causality',
]);
const id = z.string().uuid();
const offset = z.number().int().min(0).max(10000).optional();
let calls = 0;
function tool(name, description, inputSchema, run) {
  server.registerTool(
    name,
    {
      description,
      inputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
      },
    },
    async (args) => {
      if (++calls > 16)
        throw new Error('已达到本次检索次数上限，请根据已有证据作答');
      await appendFile(process.env.HISTREE_RETRIEVED, `tool:${name}\n`);
      const value = await run(args);
      if (name === 'get_evidence')
        await appendFile(
          process.env.HISTREE_RETRIEVED,
          value.items.map((x) => `${x.key}\n`).join(''),
        );
      return { content: [{ type: 'text', text: JSON.stringify(value) }] };
    },
  );
}
tool(
  'search_entries',
  '搜索已发布人物、事件、专题及已录入引文。将问题拆成姓名、别名或短关键词；不是整部史书搜索。',
  {
    keywords: z.array(z.string().trim().min(1).max(40)).min(1).max(6),
    kind: z.enum(['all', 'person', 'event', 'topic']).optional(),
    fromYear: z.number().int().min(-3000).max(2100).optional(),
    toYear: z.number().int().min(-3000).max(2100).optional(),
    offset,
  },
  (args) => {
    if (
      args.fromYear !== undefined &&
      args.toYear !== undefined &&
      args.fromYear > args.toYear
    )
      throw new Error('年份范围无效');
    return library.search(args);
  },
);
tool(
  'get_entry',
  '读取一个已发布条目；详情是网站整理，回答事实前还应读取证据。',
  { kind, id },
  (args) => library.entry(args),
);
tool(
  'get_relations',
  '查询已发布条目的直接或两层人物关系、事件参与、事件因果。返回的关系 ID 可用于查证据。',
  { id, depth: z.number().int().min(1).max(2).optional() },
  (args) => library.relations(args),
);
tool(
  'get_evidence',
  '读取条目或关系的史料依据。quote 是引文，claim 是整理后的说法，review 是校核备注；引用时使用返回的 key，例如 [C12]。',
  { kind: subject, id, offset },
  (args) => library.evidence(args),
);
await server.connect(new StdioServerTransport());
