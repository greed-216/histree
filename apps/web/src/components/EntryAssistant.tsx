import { useEffect, useRef, useState, type RefObject } from 'react';
import { PageAssistant } from './PageAssistant';
import '../styles/page-assistant.css';

const suggestions = ['用白话解释这个事件。', '这件事的前因后果是什么？', '这里涉及哪些人物，各自做了什么？'];

export function EntryAssistant({ entryId, title, article, headerOnMobile = false }: {
  entryId: string; title: string; article: RefObject<HTMLElement | null>; headerOnMobile?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const serial = useRef(0);
  const [open, setOpen] = useState(false);
  const [selection, setSelection] = useState('');
  const [request, setRequest] = useState<{ question: string; selectedText?: string; serial: number } | null>(null);
  useEffect(() => {
    function captureSelection() {
      const selected = window.getSelection();
      const anchor = selected?.anchorNode;
      const focus = selected?.focusNode;
      const root = article.current;
      if (!anchor || !focus || !root?.contains(anchor) || !root.contains(focus)) {
        setSelection(''); return;
      }
      // Selecting an answer or editing the assistant must not become a new page question.
      if (anchor.parentElement?.closest('dialog') || focus.parentElement?.closest('dialog')) return;
      setSelection(selected.toString().trim().slice(0, 300));
    }
    document.addEventListener('selectionchange', captureSelection);
    return () => document.removeEventListener('selectionchange', captureSelection);
  }, [article]);
  function show(selectedText?: string) {
    setRequest(selectedText ? { question: '', selectedText, serial: ++serial.current } : null);
    setOpen(true);
    dialog.current?.showModal();
  }
  function close() { dialog.current?.close(); }
  return <>
    <div className={`entry-assistant-launcher${headerOnMobile ? ' entry-assistant-header-mobile' : ''}`}>
      {selection && !open && <button type="button" className="entry-selection-question" onClick={() => show(selection)}>
        <span>“{selection.slice(0, 32)}{selection.length > 32 ? '…' : ''}”</span>问这句话 ↗
      </button>}
      <button type="button" className="entry-assistant-trigger" onClick={() => show()} aria-haspopup="dialog">✦ 本页助手</button>
    </div>
    <dialog ref={dialog} className="entry-assistant-dialog" aria-label="本页阅读助手" onClose={() => setOpen(false)} onClick={event => {
      const bounds = event.currentTarget.getBoundingClientRect();
      if (event.target === event.currentTarget && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) close();
    }}>
      {open && <PageAssistant entryId={entryId} title={title} questions={[]} evidence={[]} request={request}
        suggestions={suggestions} onClose={close} onRequestHandled={() => setRequest(null)} onSection={id => {
          close(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
        }} />}
    </dialog>
  </>;
}
