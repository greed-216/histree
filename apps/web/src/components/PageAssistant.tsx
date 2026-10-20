import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { askQuestion, askStatus, type AskAnswer, type AskContext, type AskCitation } from '../lib/ask';

export interface ReadingQuestion {
  id: string; question: string; aliases: string[]; answer: string; next: string[]; section: string;
}
type Turn = { question: string; result: AskAnswer; curated: boolean; followups: string[]; section?: string };
type PendingQuestion = { question: string; selectedText: string; failed?: boolean };
type Session = { pending?: PendingQuestion; turns: Turn[]; conversation?: string; aiTurns: number; draft?: string; selectedText?: string };
const sessions = new Map<string, Session>();
function rememberSession(key: string, value: Session) {
  sessions.delete(key); sessions.set(key, value);
  while (sessions.size > 32) sessions.delete(sessions.keys().next().value!);
}

export function CitedText({ text, citations, onSource }: {
  text: string; citations: AskCitation[]; onSource: (key: string) => void;
}) {
  return <>{text.split(/(\[C\d+\])/g).map((part, i) => {
    const citation = citations.find(c => `[${c.key}]` === part);
    return citation ? <button key={i} type="button" className="event-citation" onClick={() => onSource(citation.key)} aria-label={`查看依据 ${citation.key.slice(1)}`}>[{citation.key.slice(1)}]</button> : part;
  })}</>;
}

export function PageAssistant({ entryId, title, questions, evidence, request, onSection, onClose, onRequestHandled, suggestions = [], context, scopeLabel, focusPrompt, movable = false }: {
  entryId: string; title: string; questions: ReadingQuestion[]; evidence: AskCitation[];
  request: { question: string; selectedText?: string; serial: number } | null;
  onSection: (id: string) => void; onClose: () => void; onRequestHandled: () => void;
  suggestions?: string[]; context?: AskContext | null; scopeLabel?: string; focusPrompt?: string; movable?: boolean;
}) {
  const [session, setSession] = useState<Session>(() => sessions.get(entryId) ?? { turns: [], aiTurns: 0 });
  const [question, setQuestion] = useState(() => sessions.get(entryId)?.draft ?? '');
  const [selection, setSelection] = useState(() => sessions.get(entryId)?.selectedText ?? '');
  const [available, setAvailable] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingQuestion | undefined>(() => { const saved = sessions.get(entryId)?.pending; return saved ? {...saved, failed: true} : undefined; });
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  const log = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const handled = useRef<number | undefined>(undefined);
  useEffect(() => { rememberSession(entryId, { ...session, draft: question, selectedText: selection, pending }); }, [entryId, session, question, selection, pending]);
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
  }, [session.turns, busy, error, pending]);
  function prepared(item: ReadingQuestion) {
    if (busy) return;
    const citations = evidence.filter(c => item.answer.includes(`[${c.key}]`));
    setSession(old => ({ ...old, turns: [...old.turns, { question: item.question, result: { answer: item.answer, citations, insufficientEvidence: false }, curated: true, followups: item.next, section: item.section }].slice(-12) }));
    setQuestion(''); setSelection(''); setPending(undefined); setError('');
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
    await send(question.trim(), selection);
  }
  async function send(text: string, selectedText: string) {
    if (busy || text.length < 2) return;
    const item = !selectedText && questions.find(x => x.question === text || x.aliases.includes(text));
    if (item) { prepared(item); return; }
    if (!available) { setError('史料问答暂时无法连接，请稍后重新打开助手尝试。'); return; }
    if (session.aiTurns >= 6) { setError('本次史料对话已满 6 轮，请清空对话后继续。'); return; }
    const abort = new AbortController(); controller.current = abort;
    setPending({question: text, selectedText}); setQuestion(''); setSelection('');
    setBusy(true); setError(''); setStatus('正在查找本页及相关史料…');
    try {
      const previous = session.turns.at(-1)?.question;
      const coreQuestion = selectedText ? `我正在读“${title.slice(0, 80)}”。选中的原句是“${selectedText.slice(0, 300)}”。我的问题：${text}` : previous && text.length <= 550 ? `当前阅读：${title.slice(0, 80)}。我刚才问的是“${previous.slice(0, 100)}”。现在的问题：${text}` : text;
      const scopedQuestion = (focusPrompt ? `${focusPrompt.slice(0, 240)}\n我的问题：${coreQuestion}` : coreQuestion).slice(0, 800);
      await askQuestion({ question: scopedQuestion, conversation: session.conversation, context: context === undefined ? { kind: 'event', id: entryId } : context ?? undefined }, abort.signal, event => {
        if (event.type === 'conversation') setSession(old => ({ ...old, conversation: event.conversation }));
        if (event.type === 'status') setStatus(event.message);
        if (event.type === 'result') {
          setSession(old => ({ ...old, aiTurns: old.aiTurns + 1, turns: [...old.turns, { question: text, result: event, curated: false, followups: questions.length ? ['result', 'north'] : [] }].slice(-12) }));
          setPending(undefined);
        }
      });
    } catch (err) {
      setPending({question: text, selectedText, failed: true});
      if (err instanceof Error && err.message === '不允许此来源访问') {
        setAvailable(false); setError('当前预览地址尚未获准连接史料问答。问题已保留在对话中，可稍后重新尝试。');
      } else setError(abort.signal.aborted ? '已停止本次查阅，可以修改问题后重试。' : err instanceof Error ? err.message : '查阅失败，请重试。');
    } finally { controller.current = null; setBusy(false); setStatus(''); }
  }
  return <section className="page-assistant" aria-label="本页阅读助手">
    <header className="assistant-header" tabIndex={movable ? 0 : undefined} aria-label={movable ? '移动助手窗口：拖动标题栏，或使用方向键移动' : undefined}>
      <div><p className="eyebrow">{movable ? '⠿ 拖动标题栏移动' : '陪你读懂历史'}</p><h2>史料助手 <span>✦</span></h2></div>
      <button type="button" onClick={onClose} aria-label="收起史料助手">×</button>
    </header>
    <p className="assistant-context">{scopeLabel || '正在读'} · {title}</p>
    <div className="assistant-log" ref={log} aria-live="polite" aria-relevant="additions">
      {session.turns.length === 0 && !pending && <div className="assistant-welcome"><p>哪里没读懂？</p><p>可以问一个词，也可以问为什么。答案会带你回到原文，或继续看下一步。</p></div>}
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
      {pending && <article className="assistant-turn assistant-pending" aria-label="已发送的问题">
        <h3>{pending.question}</h3>
        {pending.selectedText && <blockquote className="assistant-pending-selection">{pending.selectedText}</blockquote>}
        {busy ? <div role="status" className="assistant-waiting"><span className="assistant-spinner" aria-hidden="true"/><div><p>{status || '正在查阅史料…'}</p><small>问题已发送，查阅完成后会在这里回复。</small></div></div>
          : pending.failed && <div className="assistant-retry"><span>本次查阅未完成，问题已保留。</span><button type="button" disabled={!available} onClick={() => void send(pending.question, pending.selectedText)}>重新发送</button><button type="button" onClick={() => { setQuestion(pending.question); setSelection(pending.selectedText); setPending(undefined); setError(''); input.current?.focus(); }}>修改问题</button></div>}
      </article>}
      {error && <p role="alert" className="assistant-notice">{error}</p>}
    </div>
    <form onSubmit={submit} className="assistant-form">
      {selection && <div className="assistant-selection"><span>选中原句：{selection}</span><button type="button" onClick={() => setSelection('')} aria-label="取消选中文字">×</button></div>}
      <label htmlFor="page-question" className="sr-only">向本页助手提问</label>
      <textarea ref={input} autoFocus id="page-question" value={question} disabled={busy} onChange={e => setQuestion(e.target.value)} maxLength={selection ? 320 : 800} placeholder={busy ? '问题已发送，正在等待史料回复…' : context?.kind === 'person' ? '例如：他为什么参与这件事？他和谁是什么关系？' : context?.kind && !['person', 'event'].includes(context.kind) ? '例如：这条连线表示什么？哪段史料支持？' : context === null ? '例如：帮我找贾谊上疏相关的史料。' : '例如：这件事为什么发生？这里的词是什么意思？'} rows={2}/>
      <div><button type="button" disabled={busy || (!session.turns.length && !session.conversation && !pending)} onClick={() => { setSession({ turns: [], aiTurns: 0 }); setPending(undefined); setError(''); }}>清空对话</button>
        {busy ? <button type="button" className="assistant-send" onClick={() => controller.current?.abort()}>停止</button> : <button className="assistant-send" disabled={question.trim().length < 2}>提问 ↑</button>}
      </div>
      <p>{available === null ? '正在连接史料问答…' : available ? context === null ? '提问时检索已发布史料，回答附出处。' : '提问时查阅当前条目及相关已发布史料，回答附出处。' : '暂时无法连接史料问答，请稍后重新打开助手。'}</p>
    </form>
  </section>;
}
