import type { EvidenceClaim } from '@histree/shared-types';
export function splitEvidenceNote(input?: string | null) {
  const note=input??'';
  const marker = '；核对说明：';
  if (!note.startsWith('原文：') || !note.includes(marker)) return { quote: '', review: note };
  const end = note.indexOf(marker);
  return { quote: note.slice(3, end), review: note.slice(end + marker.length) };
}
export function evidencePath(claim: EvidenceClaim) {
  return `/evidence/${claim.subject_table}/${claim.subject_id}#claim-${claim.id}`;
}
export function correctionUrl(claim: EvidenceClaim, permalink: string) {
  const body = `条目引用：${permalink}\n引用编号：${claim.id}\n说法：${claim.claim_text}\n出处：${claim.source?.title ?? ''} ${claim.citation ?? ''}\n\n建议修改：\n\n依据（书名、版本、卷页或链接）：\n`;
  return `https://github.com/greed-216/histree/issues/new?title=${encodeURIComponent('史料勘误：' + claim.claim_text.slice(0, 45))}&body=${encodeURIComponent(body)}`;
}
