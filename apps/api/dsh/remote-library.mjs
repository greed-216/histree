import { readFile, writeFile } from 'node:fs/promises';
import { safeSourceUrl } from './retrieval.mjs';

/** Anonymous, bounded RPC reads. Only retrieved citations are persisted for validation. */
export async function createRemoteLibrary(manifest, ledgerPath) {
  const url = new URL(manifest.url);
  if (
    !['https:', 'http:'].includes(url.protocol) ||
    typeof manifest.anonKey !== 'string'
  )
    throw new Error('Invalid public query configuration');
  const saved = JSON.parse(
    await readFile(`${ledgerPath}.json`, 'utf8').catch(() => '[]'),
  );
  let writes = Promise.resolve();
  const byClaim = new Map(saved.map((c) => [c.claimId, c]));
  const rpc = async (name, args) => {
    const response = await fetch(
      `${url.href.replace(/\/$/, '')}/rest/v1/rpc/${name}`,
      {
        method: 'POST',
        headers: {
          apikey: manifest.anonKey,
          Authorization: `Bearer ${manifest.anonKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(args),
        signal: AbortSignal.timeout(15000),
      },
    );
    if (!response.ok)
      throw new Error(`Public query failed (${response.status})`);
    return response.json();
  };
  const scope = (table, extra = {}) => ({
    p_table: table,
    p_page: 0,
    p_limit: 10,
    p_admin: false,
    ...extra,
  });
  const summary = (row) => ({
    id: row.id,
    kind: row.type || 'topic',
    label: row.name || row.title || row.label,
    aliases: row.aliases || [],
    description: (row.description || '').slice(0, 1600),
    biography: (row.biography || '').slice(0, 6000),
    startYear: row.start_year ?? row.birth_year,
    endYear: row.end_year ?? row.death_year,
    phases: row.phases,
    sections: row.sections,
  });
  return {
    async search({ keywords, kind = 'all', fromYear, toYear, offset = 0 }) {
      return rpc('ask_search', {
        p_keywords: keywords,
        p_kind: kind,
        p_from: fromYear ?? null,
        p_to: toYear ?? null,
        p_offset: offset,
      });
    },
    async entry({ kind, id }) {
      const row =
        kind === 'topic'
          ? await rpc('topic_detail', { p_id: id })
          : await rpc('entry_detail', { p_id: id });
      if (!row || (row.type && row.type !== kind))
        throw new Error('条目未发布或不存在');
      return { ...summary(row), kind };
    },
    async relations({ id, depth = 1 }) {
      const first = await rpc('entry_context', {
        p_id: id,
        p_page: 0,
        p_limit: 40,
      });
      if (!first) throw new Error('条目未发布或不存在');
      const found = new Map(
        first.edges.map((e) => [`${e.subject_table}:${e.id}`, e]),
      );
      const nodes = new Map(first.nodes.map((n) => [n.id, n]));
      let truncated = first.has_more;
      if (depth === 2) {
        const neighbors = [...nodes.keys()].filter((n) => n !== id).slice(0, 5);
        if (first.nodes.length - 1 > 5) truncated = true;
        for (const neighbor of neighbors) {
          const page = await rpc('entry_context', {
            p_id: neighbor,
            p_page: 0,
            p_limit: 10,
          });
          if (!page) continue;
          truncated ||= page.has_more;
          page.nodes.forEach((n) => nodes.set(n.id, n));
          page.edges.forEach((e) => found.set(`${e.subject_table}:${e.id}`, e));
        }
      }
      return {
        truncated: truncated || found.size > 40,
        edges: [...found.values()]
          .slice(0, 40)
          .map((e) => ({
            id: e.id,
            kind: e.subject_table,
            from: e.source,
            to: e.target,
            fromName: nodes.get(e.source)?.name || nodes.get(e.source)?.title,
            toName: nodes.get(e.target)?.name || nodes.get(e.target)?.title,
            relation: e.type,
            description: e.description,
          })),
      };
    },
    async evidence({ kind, id, offset = 0 }) {
      const result = await rpc(
        'content_page',
        scope('fact_claim', {
          p_subject: kind,
          p_subject_id: id,
          p_page: Math.floor(offset / 10),
        }),
      );
      const items = [];
      for (const row of result.items) {
        if (!row.source?.title) continue;
        let citation = byClaim.get(row.id);
        if (!citation) {
          const note = row.note || '',
            marker = '；核对说明：',
            split = note.indexOf(marker),
            quote = note.startsWith('原文：')
              ? note.slice(3, split < 0 ? undefined : split)
              : '';
          citation = {
            key: `C${byClaim.size + 1}`,
            claimId: row.id,
            subjectTable: row.subject_table,
            subjectId: row.subject_id,
            claim: row.claim_text,
            quote,
            review:
              split >= 0
                ? note.slice(split + marker.length)
                : quote
                  ? ''
                  : note,
            sourceId: row.source.id,
            title: row.source.title,
            location: row.citation || '',
            url: safeSourceUrl(row.source.url),
            subjectLabel: result.labels?.[row.subject_id] || '',
          };
          byClaim.set(row.id, citation);
        }
        items.push(citation);
      }
      const snapshot = JSON.stringify([...byClaim.values()]);
      writes = writes.then(() =>
        writeFile(`${ledgerPath}.json`, snapshot, { mode: 0o600 }),
      );
      await writes;
      return { items, nextOffset: result.has_more ? offset + 10 : null };
    },
  };
}
