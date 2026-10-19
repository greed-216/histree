import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import '../styles/feedback.css';

export function FeedbackButton({ claimId, sourceId, context, label = '提交勘误' }: {
  claimId?: string; sourceId?: string; context?: string; label?: string;
}) {
  const [open, setOpen] = useState(false);
  return <><button type="button" className="feedback-trigger" onClick={() => setOpen(true)}>{label}</button>
    {open && <FeedbackForm claimId={claimId} sourceId={sourceId} context={context} title={label} onClose={() => setOpen(false)} />}
  </>;
}

function FeedbackForm({ claimId, sourceId, context, title, onClose }: {
  claimId?: string; sourceId?: string; context?: string; title: string; onClose: () => void;
}) {
  const location = useLocation();
  const dialog = useRef<HTMLDialogElement>(null);
  const request = useRef({ id: crypto.randomUUID(), signature: '' });
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [pending, setPending] = useState(false);
  const [received, setReceived] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const element = dialog.current;
    if (!element?.open) element?.showModal();
    const before = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { element?.close(); document.body.style.overflow = before; };
  }, []);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setError('');
    const payload = { claim_id: claimId, source_id: sourceId, message: message.trim(), email: email.trim(), page_path: location.pathname + location.search };
    const signature = JSON.stringify(payload);
    if (request.current.signature && request.current.signature !== signature) request.current.id = crypto.randomUUID();
    request.current.signature = signature;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    try {
      const result = await apiFetch<{ received: boolean }>('/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: request.current.id, ...payload }), signal: controller.signal });
      if (!result.received) throw new Error('反馈未能保存，请稍后重试。');
      setReceived(true);
    } catch (cause) {
      setError(cause instanceof Error && cause.name !== 'AbortError' ? cause.message : '提交暂未完成，请重试。');
    } finally { window.clearTimeout(timeout); setPending(false); }
  }
  return <dialog ref={dialog} className="feedback-dialog" aria-label={title} onCancel={event => { event.preventDefault(); if (!pending) onClose(); }} onClick={event => { if (event.target === event.currentTarget && !pending) onClose(); }}>
    <div className="feedback-panel">
      <div className="feedback-heading"><h2>{title}</h2><button type="button" aria-label="关闭反馈" disabled={pending} onClick={onClose}>×</button></div>
      {received ? <div className="feedback-success" role="status"><p>反馈已收到，谢谢你帮助完善内容。</p><button type="button" className="feedback-submit" onClick={onClose}>完成</button></div> : <form onSubmit={submit} aria-busy={pending}>
        {context && <p className="feedback-context">关于：{context.length > 180 ? context.slice(0, 180) + '…' : context}</p>}
        <label>问题或修改建议<textarea autoFocus required minLength={5} maxLength={3000} rows={5} value={message} disabled={pending} onChange={event => setMessage(event.target.value)} placeholder="哪里有问题？如有依据，也可以一并告诉我们。" /></label>
        <label>邮箱（选填）<input type="email" autoComplete="email" maxLength={254} value={email} disabled={pending} onChange={event => setEmail(event.target.value)} placeholder="方便我们向你核实或回复" /></label>
        <p className="feedback-privacy">不留邮箱也可以提交。邮箱仅用于联系你核实或回复反馈，不会公开展示。</p>
        {error && <p className="feedback-error" role="alert">{error}</p>}
        <div className="feedback-actions"><button type="button" disabled={pending} onClick={onClose}>取消</button><button type="submit" className="feedback-submit" disabled={pending}>{pending ? '正在提交…' : '提交反馈'}</button></div>
      </form>}
    </div>
  </dialog>;
}
