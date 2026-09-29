import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { askQuestion, askStatus, type AskAnswer } from '../lib/ask';

const examples = ['907 年唐梁禅代有哪些相关事件？', '朱温与敬翔是什么关系？有哪些史料依据？', '李克用与李存勖的关系，有哪些记载？'];
export function AskPage() {
  const [params] = useSearchParams();
  const kind = params.get('kind'); const id = params.get('id');
  const context = (kind === 'person' || kind === 'event') && id ? { kind, id } : undefined;
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState<Array<{ question: string; result: AskAnswer }>>([]);
  const [conversation, setConversation] = useState<string>();
  const [available, setAvailable] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(0);
  const abort = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    askStatus(controller.signal).then(x => setAvailable(x.available)).catch(() => { if (!controller.signal.aborted) setAvailable(false); });
    return () => controller.abort();
  }, [checking]);
  useEffect(() => () => abort.current?.abort(), []);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !available || question.trim().length < 2) return;
    const text = question.trim();
    const controller = new AbortController(); abort.current = controller;
    setBusy(true); setError(''); setStatus('正在连接史料检索服务…');
    try {
      await askQuestion({ question: text, conversation, context }, controller.signal, event => {
        if (event.type === 'conversation') setConversation(event.conversation);
        if (event.type === 'status') setStatus(event.message);
        if (event.type === 'result') { setTurns(old => [...old, { question: text, result: event }]); setQuestion(''); }
      });
    } catch (err) { setError(controller.signal.aborted ? '本次提问已停止。' : err instanceof Error ? err.message : '提问失败，请重试。'); }
    finally { setBusy(false); setStatus(''); abort.current = null; }
  }
  return <div className="mx-auto max-w-4xl space-y-7">
    <header className="reading-card bg-gradient-to-br! from-teal-50 to-stone-50">
      <p className="eyebrow">以史料为据 · Histree × dsh</p>
      <h1 className="font-serif text-3xl md:text-4xl mt-3">问史料</h1>
      <p className="mt-4 text-stone-600 leading-7">从一个问题出发，查阅人物、事件和关系，沿着引用回到原文。</p>
      <p className="mt-2 text-sm text-stone-500">目前检索网站已发布内容及所引史料，尚未覆盖整部史书。回答由 AI 整理，请结合出处阅读。</p>
      {context && <Link className="mt-4 inline-block text-sm text-teal-800 underline" to={`/${context.kind === 'person' ? 'people' : 'events'}/${context.id}`}>围绕当前条目提问 · 查看条目 →</Link>}
    </header>
    {available === false && <div role="status" className="reading-card text-stone-600">问答服务暂未就绪，你仍可<Link className="text-teal-800 underline mx-1" to="/search">搜索和阅读史料</Link>。<button className="ml-2 underline text-sm" onClick={() => { setAvailable(null); setChecking(n => n + 1); }}>重新连接</button></div>}
    {turns.length === 0 && <div className="grid sm:grid-cols-3 gap-3">{examples.map(text => <button key={text} onClick={() => setQuestion(text)} className="reading-card text-left text-sm leading-6 hover:border-teal-500">{text}<span className="block mt-3 text-teal-700">试着问问 ↗</span></button>)}</div>}
    <div className="space-y-7">{turns.map((turn, index) => <article key={index} className="space-y-3">
      <h2 className="font-medium text-lg pl-4 border-l-4 border-teal-700">{turn.question}</h2>
      <div className="reading-card">
        <div className="whitespace-pre-wrap leading-8 text-stone-800">{turn.result.answer.split(/(\[C\d+\])/g).map((part, n) => {
          const citation = turn.result.citations.find(x => `[${x.key}]` === part);
          return citation ? <a key={n} className="text-teal-800 font-medium mx-1 underline" href={`#answer-${index}-${citation.key}`} onClick={() => document.getElementById(`answer-${index}-${citation.key}`)?.setAttribute('open', '')} aria-label={`查看出处 ${citation.title}`}>[{turn.result.citations.indexOf(citation) + 1}]</a> : part;
        })}</div>
        {turn.result.insufficientEvidence && <p className="mt-4 text-sm text-amber-800">当前资料不足以完整回答，下面的出处只支持回答中对应的部分。</p>}
        {turn.result.citations.length > 0 && <section className="mt-6 border-t border-stone-200 pt-4 space-y-3" aria-label="本次回答的史料依据"><h3 className="eyebrow">史料依据 · {turn.result.citations.length}</h3>{turn.result.citations.map((c, n) => <details key={c.key} id={`answer-${index}-${c.key}`} className="rounded-xl bg-stone-50 p-4 scroll-mt-28">
          <summary className="cursor-pointer text-sm text-teal-900">[{n + 1}] {c.title} · {c.location}</summary>
          <p className="mt-3 text-sm leading-7">{c.claim}</p>
          {c.quote ? <blockquote className="mt-3 pl-4 border-l-2 border-stone-300 text-sm leading-7 whitespace-pre-wrap">{c.quote}</blockquote> : <p className="mt-2 text-sm text-stone-500">此条暂未摘录原文。</p>}
          {c.review && <p className="mt-3 text-xs leading-6 text-stone-500">{c.review}</p>}
          <div className="flex flex-wrap gap-4 mt-3 text-sm text-teal-800">
            <Link className="underline" to={`/evidence/${c.subjectTable}/${c.subjectId}#claim-${c.claimId}`}>出处与勘误</Link>
            {c.url && <a className="underline" href={c.url} target="_blank" rel="noreferrer">GitHub 原文 ↗</a>}
            {(c.subjectTable === 'person' || c.subjectTable === 'event') && <><Link className="underline" to={`/${c.subjectTable === 'person' ? 'people' : 'events'}/${c.subjectId}`}>查看条目</Link><Link className="underline" to={`/graph/${c.subjectId}`}>查看关系图</Link></>}
          </div>
        </details>)}</section>}
      </div>
    </article>)}</div>
    <form onSubmit={submit} className="reading-card space-y-3">
      <label htmlFor="history-question" className="font-medium">{turns.length ? '继续追问' : '你想了解什么？'}</label>
      <textarea id="history-question" className="reading-input w-full min-h-28 mt-2" value={question} onChange={e => setQuestion(e.target.value)} maxLength={800} disabled={busy} placeholder="例如：907 年唐梁禅代的过程，史书是怎么记载的？" />
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <span className="text-stone-500">{question.length}/800 · {turns.length}/6 轮</span>
        <div className="flex gap-3">
          {conversation && <button type="button" disabled={busy} className="text-stone-600 disabled:opacity-40" onClick={() => { setConversation(undefined); setTurns([]); setError(''); }}>新对话</button>}
          {busy ? <button type="button" className="rounded-lg border border-stone-300 px-5 py-2" onClick={() => abort.current?.abort()}>停止</button> : <button disabled={!available || question.trim().length < 2 || turns.length >= 6} className="rounded-lg bg-teal-800 text-white px-5 py-2 disabled:opacity-40">查阅史料</button>}
        </div>
      </div>
      <p role="status" aria-live="polite" className="text-sm text-teal-800">{available === null ? '正在检查问答服务…' : status}</p>
      {error && <p role="alert" className="text-sm text-amber-800">{error} <Link to={`/search?q=${encodeURIComponent(question)}`} className="underline">使用普通搜索</Link></p>}
    </form>
  </div>;
}
