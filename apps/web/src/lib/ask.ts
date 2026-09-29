export interface AskCitation {
  key: string; claimId: string; subjectTable: string; subjectId: string; subjectLabel: string;
  claim: string; quote: string; review: string; sourceId: string; title: string; location: string; url?: string;
}
export interface AskAnswer { answer: string; insufficientEvidence: boolean; citations: AskCitation[] }
export type AskEvent = { type: 'status'; message: string } | { type: 'conversation'; conversation: string } | ({ type: 'result' } & AskAnswer) | { type: 'error'; message: string };
const base = (import.meta.env.VITE_ASK_API_URL || import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
export async function askStatus(signal: AbortSignal) {
  if (!base) return { available: false };
  const res = await fetch(`${base}/ask/status`, { signal });
  if (!res.ok) throw new Error('问答服务暂时无法连接');
  return res.json() as Promise<{ available: boolean }>;
}
export async function askQuestion(body: { question: string; conversation?: string; context?: { kind: string; id: string } }, signal: AbortSignal, onEvent: (event: AskEvent) => void) {
  if (!base) throw new Error('史料问答尚未开放，请先使用普通搜索。');
  const res = await fetch(`${base}/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal });
  if (!res.ok) { const data = await res.json().catch(() => ({})); throw new Error(data.message || `提问失败（${res.status}）`); }
  if (!res.body) throw new Error('问答连接未建立');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let completed = false;
  const consume = (line: string) => {
    if (!line.trim()) return;
    const event = JSON.parse(line) as AskEvent;
    if (event.type === 'error') throw new Error(event.message);
    if (event.type === 'result') completed = true;
    onEvent(event);
  };
  try {
    for (;;) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      if (buffer.length > 200000) throw new Error('回答超出长度限制');
      let end;
      while ((end = buffer.indexOf('\n')) >= 0) { consume(buffer.slice(0, end)); buffer = buffer.slice(end + 1); }
      if (done) { consume(buffer); break; }
    }
    if (!completed) throw new Error('连接已中断，回答未完成，请重试。');
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}
