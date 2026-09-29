import assert from 'node:assert/strict';
import { createLibrary, validateAnswer, safeSourceUrl } from '../apps/api/dsh/retrieval.mjs';
const snapshot = {
  person: [{ id: 'p1', name: '朱温', aliases: ['朱全忠'], status: 'published' }, { id: 'p2', name: '敬翔', status: 'published' }, { id: 'draft', name: '秘密人物', status: 'draft' }],
  event: [{ id: 'e1', title: '唐梁禅代', start_year: 907, status: 'published' }, { id: 'e2', title: '后梁灭亡', start_year: 923, status: 'published' }], topic: [],
  person_relationship: [{ id: 'r1', person_a: 'p1', person_b: 'p2', relation_type: '任用者', status: 'published' }, { id: 'hidden', person_a: 'p1', person_b: 'draft', status: 'published' }],
  person_event: [{ id: 'r2', person_id: 'p2', event_id: 'e1', role: '参与者', status: 'published' }], event_causality: [],
  fact_claim: [
    { id: 'c1', status: 'published', subject_table: 'person_relationship', subject_id: 'r1', claim_text: '关系说明', note: '原文：测试引文。；核对说明：年代待考。', source: { id: 's1', title: '旧五代史', url: 'https://github.com/greed-216/histree/blob/abc/resources/book.txt' } },
    { id: 'c2', status: 'published', subject_table: 'person_relationship', subject_id: 'hidden', source: { title: '不可见' } },
    { id: 'c3', status: 'draft', subject_table: 'person', subject_id: 'p1', source: { title: '不可见' } },
  ],
};
const lib = createLibrary(snapshot);
assert.equal(lib.search({ keywords: ['朱全忠'] }).items[0].id, 'p1');
assert.equal(lib.search({ keywords: ['秘密'] }).total, 0);
assert.deepEqual(lib.search({ keywords: ['唐梁', '后梁'], fromYear: 907, toYear: 907 }).items.map(x => x.id), ['e1']);
assert.equal(lib.relations({ id: 'p1' }).edges.length, 1);
assert.equal(lib.relations({ id: 'p1', depth: 2 }).edges.length, 2);
assert.throws(() => lib.entry({ kind: 'person', id: 'draft' }));
assert.equal(lib.citations.length, 1);
assert.equal(lib.evidence({ kind: 'person_relationship', id: 'r1' }).items[0].quote, '测试引文。');
const raw = JSON.stringify({ answer: '关系见引文。[C1]', insufficientEvidence: false });
assert.throws(() => validateAnswer(raw, lib, new Set()));
assert.equal(validateAnswer(raw, lib, new Set(['C1'])).citations[0].claimId, 'c1');
assert.throws(() => validateAnswer(JSON.stringify({ answer: '断言[C999]', insufficientEvidence: false }), lib, new Set(['C999'])));
assert.throws(() => validateAnswer(JSON.stringify({ answer: '无引文断言', insufficientEvidence: false }), lib, new Set()));
assert.throws(() => validateAnswer(JSON.stringify({ answer: '跳转 https://evil.test [C1]', insufficientEvidence: false }), lib, new Set(['C1'])));
assert.equal(validateAnswer(JSON.stringify({ answer: '当前收录材料不足。', insufficientEvidence: true }), lib, new Set()).citations.length, 0);
assert.equal(safeSourceUrl('javascript:alert(1)'), undefined);
assert.equal(safeSourceUrl('https://github.com.evil.test/greed-216/histree/blob/a'), undefined);
assert.equal(safeSourceUrl('https://github.com/other/repo/blob/a'), undefined);
console.log('Ask retrieval: aliases, dates, published scope, graph depth, citation verification passed');
