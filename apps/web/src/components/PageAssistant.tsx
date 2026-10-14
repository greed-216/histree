import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { askQuestion, askStatus, type AskAnswer, type AskCitation } from '../lib/ask';

export interface ReadingQuestion {
  id: string; question: string; aliases: string[]; answer: string; next: string[]; section: string;
}
type Turn = { question: string; result: AskAnswer; curated: boolean; followups: string[]; section?: string };
type Session = { turns: Turn[]; conversation?: string; aiTurns: number; draft?: string; selectedText?: string };
const sessions = new Map<string, Session>();

export function CitedText({ text, citations, onSource }: {
  text: string; citations: AskCitation[]; onSource: (key: string) => void;
}) {
  return <>{text.split(/(\[C\d+\])/g).map((part, i) => {
    const citation = citations.find(c => `[${c.key}]` === part);
    return citation ? <button key={i} type="button" className="event-citation" onClick={() => onSource(citation.key)} aria-label={`查看依据 ${citation.key.slice(1)}`}>[{citation.key.slice(1)}]</button> : part;
  })}</>;
}

export function PageAssistant({ entryId, title, questions, evidence, request, onSection, onClose, onRequestHandled, suggestions = [] }: {
  entryId: string; title: string; questions: ReadingQuestion[]; evidence: AskCitation[];
  request: { question: string; selectedText?: string; serial: number } | null;
  onSection: (id: string) => void; onClose: () => void; onRequestHandled: () => void;
  suggestions?: string[];
}) {
  const [session, setSession] = useState<Session>(() => sessions.get(entryId) ?? { turns: [], aiTurns: 0 });
  const [question, setQuestion] = useState(() => sessions.get(entryId)?.draft ?? '');
  const [selection, setSelection] = useState(() => sessions.get(entryId)?.selectedText ?? '');
  const [available, setAvailable] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  const log = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const handled = useRef<number | undefined>(undefined);
  useEffect(() => { sessions.set(entryId, { ...session, draft: question, selectedText: selection }); }, [entryId, session, question, selection]);
  useEffect(() => {
    const abort = new AbortController();
    askStatus(abort.signal).then(x => setAvailable(x.available)).catch(() => { if (!abort.signal.aborted) setAvailable(false); });
    return () => { abort.abort(); controller.current?.abort(); };
  }, []);
  useEffect(() => {
    const container = log.current;
    if (!container) return;
    const last = Array.from(container.querySelectorAll<HTMLElement>('.assistant-turn')).at(-1);
    if (busy || error) container.scrollTop = container.scrollHeight;
    else if (last) container.scrollTop += last.getBoundingClientRect().top - container.getBoundingClientRect().top - 8;
  }, [session.turns, busy, error]);
  function prepared(item: ReadingQuestion) {
    if (busy) return;
    const citations = evidence.filter(c => item.answer.includes(`[${c.key}]`));
    setSession(old => ({ ...old, turns: [...old.turns, { question: item.question, result: { answer: item.answer, citations, insufficientEvidence: false }, curated: true, followups: item.next, section: item.section }].slice(-12) }));
    setQuestion(''); setSelection(''); setError('');
  }
  useEffect(() => {
    if (!request || handled.current === request.serial) return;
    handled.current = request.serial;
    const item = questions.find(x => x.question === request.question);
    if (item && !request.selectedText) prepared(item);
    else { setQuestion(request.question); setSelection(request.selectedText ?? ''); input.current?.focus(); }
    onRequestHandled();
    // Each request is a deliberate click; reopening the panel must not repeat it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [request]);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || question.trim().length < 2) return;
    const text = question.trim();
    const item = !selection && questions.find(x => x.question === text || x.aliases.includes(text));
    if (item) { prepared(item); return; }
    if (!available) { setError('史料问答暂时无法连接，请稍后重新打开助手尝试。'); return; }
    if (session.aiTurns >= 6) { setError('本次史料对话已满 6 轮，请清空对话后继续。'); return; }
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setError(''); setStatus('正在查找本页及相关史料…');
    try {
      const previous = session.turns.at(-1)?.question;
      const scopedQuestion = selection ? `我正在读“${title.slice(0, 80)}”。选中的原句是“${selection.slice(0, 300)}”。我的问题：${text}` : previous && text.length <= 550 ? `当前事件：${title.slice(0, 80)}。我刚才问的是“${previous.slice(0, 100)}”。现在的问题：${text}` : text;
      await askQuestion({ question: scopedQuestion, conversation: session.conversation, context: { kind: 'event', id: entryId } }, abort.signal, event => {
        if (event.type === 'conversation') setSession(old => ({ ...old, conversation: event.conversation }));
        if (event.type === 'status') setStatus(event.message);
        if (event.type === 'result') {
          setSession(old => ({ ...old, aiTurns: old.aiTurns + 1, turns: [...old.turns, { question: text, result: event, curated: false, followups: questions.length ? ['result', 'north'] : [] }].slice(-12) }));
          setQuestion(''); setSelection('');
        }
      });
    } catch (err) {
      if (err instanceof Error && err.message === '不允许此来源访问') {
        setAvailable(false); setError('当前预览地址尚未获准连接史料问答。已保留问题，可稍后重新尝试。');
      } else setError(abort.signal.aborted ? '已停止本次查阅，可以修改问题后重试。' : err instanceof Error ? err.message : '查阅失败，请重试。');
    } finally { controller.current = null; setBusy(false); setStatus(''); }
  }
  return <section className="page-assistant" aria-label="本页阅读助手">
    <header className="assistant-header">
      <div><p className="eyebrow">陪你读懂这一页</p><h2>本页助手 <span>✦</span></h2></div>
      <button type="button" onClick={onClose} aria-label="收起本页助手">×</button>
    </header>
    <p className="assistant-context">正在读 · {title}</p>
    <div className="assistant-log" ref={log} aria-live="polite" aria-relevant="additions">
      {session.turns.length === 0 && <div className="assistant-welcome"><p>哪里没读懂？</p><p>可以问一个词，也可以问为什么。答案会带你回到原文，或继续看下一步。</p></div>}
      <div className="assistant-prompts" aria-label="提问建议">
        {(session.turns.length ? questions.slice(0, 4) : questions.slice(0, 6)).map(item => <button key={item.id} disabled={busy} onClick={() => prepared(item)}>{item.question} ↗</button>)}
        {!questions.length && suggestions.map(text => <button key={text} disabled={busy} onClick={() => { setQuestion(text); setSelection(''); input.current?.focus(); }}>{text} ↗</button>)}
      </div>
      {session.turns.map((turn, index) => <article className="assistant-turn" key={index}>
        <h3>{turn.question}</h3><p className="assistant-answer-kind">{turn.curated ? '本页解读 · 已整理依据' : 'AI 查阅 · 以本次检索为据'}</p>
        <div className="assistant-answer"><CitedText text={turn.result.answer} citations={turn.result.citations} onSource={key => {
          if (turn.curated) onSection(`source-${key}`);
          else {
            const source = document.getElementById(`assistant-${index}-${key}`);
            source?.setAttribute('open', '');
            source?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            source?.focus({ preventScroll: true });
          }
        }}/></div>
        {turn.result.insufficientEvidence && <p className="assistant-notice">现有材料不足以完整回答，请按引用核对已确认的部分。</p>}
        {!turn.curated && turn.result.citations.map(c => <details className="assistant-evidence" key={c.key} id={`assistant-${index}-${c.key}`} tabIndex={-1}>
          <summary>{c.title} · {c.key}</summary><p>{c.location}</p><blockquote>{c.quote || c.claim}</blockquote>{c.review && <p>{c.review}</p>}
          <Link to={`/evidence/${c.subjectTable}/${c.subjectId}#claim-${c.claimId}`}>打开出处与勘误 →</Link>
        </details>)}
        {(turn.followups.length > 0 || suggestions.length > 0 || turn.section) && <div className="assistant-followups"><p>接着了解</p>{turn.followups.map(id => {
          const item = questions.find(x => x.id === id);
          return item && <button key={id} disabled={busy} onClick={() => prepared(item)}>{item.question} →</button>;
        })}{!turn.curated && suggestions.slice(1, 3).map(text => <button key={text} disabled={busy} onClick={() => { setQuestion(text); setSelection(''); input.current?.focus(); }}>{text} →</button>)}{turn.section && <button onClick={() => onSection(turn.section!)}>回到对应的事件环节 ↓</button>}</div>}
      </article>)}
      {busy && <p role="status" className="assistant-notice">{status}</p>}
      {error && <p role="alert" className="assistant-notice">{error}</p>}
    </div>
    <form onSubmit={submit} className="assistant-form">
      {selection && <div className="assistant-selection"><span>选中原句：{selection}</span><button type="button" onClick={() => setSelection('')} aria-label="取消选中文字">×</button></div>}
      <label htmlFor="page-question" className="sr-only">向本页助手提问</label>
      <textarea ref={input} autoFocus id="page-question" value={question} disabled={busy} onChange={e => setQuestion(e.target.value)} maxLength={selection ? 320 : 800} placeholder="例如：这件事为什么发生？这里的词是什么意思？" rows={2}/>
      <div><button type="button" disabled={busy || !session.turns.length} onClick={() => { setSession({ turns: [], aiTurns: 0 }); setError(''); }}>清空对话</button>
        {busy ? <button type="button" className="assistant-send" onClick={() => controller.current?.abort()}>停止</button> : <button className="assistant-send" disabled={question.trim().length < 2}>提问 ↑</button>}
      </div>
      <p>{available === null ? '正在连接史料问答…' : available ? '提问时查阅本页及相关已发布史料，回答附出处。' : '暂时无法连接史料问答，请稍后重新打开助手。'}</p>
    </form>
  </section>;
}
