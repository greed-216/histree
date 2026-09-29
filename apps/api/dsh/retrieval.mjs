// A bounded, read-only view of published Histree content, shared by MCP and tests.
export function createLibrary(snapshot) {
  const entries = [...snapshot.person.map(x => ({ ...x, kind: 'person' })), ...snapshot.event.map(x => ({ ...x, kind: 'event' })), ...snapshot.topic.map(x => ({ ...x, kind: 'topic' }))].filter(x => x.status === 'published');
  const nodes = new Map(entries.map(x => [x.id, x]));
  const edges = [
    ...snapshot.person_relationship.map(x => ({ ...x, kind: 'person_relationship', from: x.person_a, to: x.person_b, label: x.relation_type })),
    ...snapshot.person_event.map(x => ({ ...x, kind: 'person_event', from: x.person_id, to: x.event_id, label: x.role })),
    ...snapshot.event_causality.map(x => ({ ...x, kind: 'event_causality', from: x.cause_event_id, to: x.effect_event_id, label: '前因后果' })),
  ].filter(x => x.status === 'published' && nodes.has(x.from) && nodes.has(x.to));
  const subjects = new Map([...entries, ...edges].map(x => [`${x.kind}:${x.id}`, x]));
  const citations = snapshot.fact_claim.filter(x => x.status === 'published' && subjects.has(`${x.subject_table}:${x.subject_id}`) && x.source?.title).map((x, i) => {
    const marker = '；核对说明：';
    const note = x.note || '';
    const split = note.indexOf(marker);
    const quote = note.startsWith('原文：') ? note.slice(3, split < 0 ? undefined : split) : '';
    return { key: `C${i + 1}`, claimId: x.id, subjectTable: x.subject_table, subjectId: x.subject_id,
      claim: x.claim_text, quote, review: split >= 0 ? note.slice(split + marker.length) : (quote ? '' : note),
      sourceId: x.source.id, title: x.source.title, location: x.citation || '', url: safeSourceUrl(x.source.url),
      subjectLabel: label(subjects.get(`${x.subject_table}:${x.subject_id}`)) };
  });
  const byKey = new Map(citations.map(x => [x.key, x]));
  const norm = text => String(text ?? '').normalize('NFKC').toLocaleLowerCase();
  const summary = x => ({ id: x.id, kind: x.kind, label: label(x), aliases: x.aliases || [], description: (x.description || '').slice(0, 1600), startYear: x.start_year ?? x.birth_year, endYear: x.end_year ?? x.death_year });
  const evidence = (subject, id) => citations.filter(x => x.subjectTable === subject && x.subjectId === id);
  return {
    citations, byKey,
    search({ keywords, kind = 'all', fromYear, toYear, offset = 0 }) {
      const terms = keywords.map(norm);
      const results = entries.filter(x => kind === 'all' || x.kind === kind).filter(x => {
        if (fromYear === undefined && toYear === undefined) return true;
        const start = x.start_year ?? x.birth_year;
        const end = x.end_year ?? (x.kind === 'event' ? start : x.death_year);
        if (start === undefined && end === undefined) return false;
        return (toYear === undefined || (start ?? end) <= toYear) && (fromYear === undefined || (end ?? start) >= fromYear);
      }).map(x => {
        const names = [label(x), ...(x.aliases || [])].map(norm);
        const body = norm([x.description, x.biography, x.faction, ...(x.tags || []), ...evidence(x.kind, x.id).map(e => `${e.claim} ${e.quote}`)].join(' '));
        const score = terms.reduce((sum, term) => sum + (names.includes(term) ? 10 : names.some(n => n.includes(term)) ? 5 : body.includes(term) ? 1 : 0), 0);
        return { ...summary(x), score, evidenceCount: evidence(x.kind, x.id).length };
      }).filter(x => x.score > 0).sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
      return { total: results.length, items: results.slice(offset, offset + 12), nextOffset: offset + 12 < results.length ? offset + 12 : null, scope: '仅已发布条目及其已录入引文；未搜索整部史书。年代筛选排除年代未知条目。' };
    },
    entry({ kind, id }) {
      const x = subjects.get(`${kind}:${id}`);
      if (!x || !['person', 'event', 'topic'].includes(x.kind)) throw new Error('条目未发布或不存在');
      return { ...summary(x), biography: (x.biography || '').slice(0, 6000), phases: x.phases, sections: x.sections, evidenceCount: evidence(kind, id).length };
    },
    relations({ id, depth = 1 }) {
      if (!nodes.has(id)) throw new Error('条目未发布或不存在');
      const seen = new Set([id]);
      const found = new Map();
      for (let level = 0; level < depth; level++) {
        const frontier = new Set(seen);
        for (const x of edges) if (frontier.has(x.from) || frontier.has(x.to)) { found.set(x.id, x); seen.add(x.from); seen.add(x.to); }
      }
      const selected = [...found.values()].slice(0, 40);
      return { truncated: found.size > 40, edges: selected.map(x => ({ id: x.id, kind: x.kind, from: x.from, to: x.to, fromName: label(nodes.get(x.from)), toName: label(nodes.get(x.to)), relation: x.label, description: x.description, evidenceCount: evidence(x.kind, x.id).length })) };
    },
    evidence({ kind, id, offset = 0 }) {
      if (!subjects.has(`${kind}:${id}`)) throw new Error('条目或关系未发布或不存在');
      const rows = evidence(kind, id);
      return { total: rows.length, items: rows.slice(offset, offset + 10), nextOffset: offset + 10 < rows.length ? offset + 10 : null };
    },
  };
}
function label(x) { return x?.name || x?.title || x?.label || ''; }
export function safeSourceUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' && url.hostname === 'github.com' && url.pathname.startsWith('/greed-216/histree/blob/') ? url.href : undefined; } catch { return undefined; }
}
export function validateAnswer(raw, library, retrieved) {
  const cleaned = raw.trim().replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '');
  const result = JSON.parse(cleaned);
  if (typeof result.answer !== 'string' || !result.answer.trim() || result.answer.length > 12000 || typeof result.insufficientEvidence !== 'boolean') throw new Error('回答格式不正确');
  const keys = [...new Set([...result.answer.matchAll(/\[(C\d+)\]/g)].map(x => x[1]))];
  if (!keys.length && !result.insufficientEvidence) throw new Error('回答缺少可核对的引用');
  if (keys.length > 20 || keys.some(key => !retrieved.has(key) || !library.byKey.has(key))) throw new Error('回答包含未检索的引用');
  // Links are rendered from trusted records, never from model-authored destinations.
  if (/https?:\/\/|\]\(|<\/?[a-z]/i.test(result.answer)) throw new Error('回答包含不允许的链接或标记');
  return { answer: result.answer, insufficientEvidence: result.insufficientEvidence, citations: keys.map(key => library.byKey.get(key)) };
}
