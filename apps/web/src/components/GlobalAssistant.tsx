import { useEffect, useRef, useState } from 'react';
import { PageAssistant } from './PageAssistant';
import { useAssistant, type AssistantScope } from '../hooks/useAssistant';
import { useFloatingWindow } from '../hooks/useFloatingWindow';
import '../styles/page-assistant.css';

export function GlobalAssistant() {
  const { scope, open, request, show, close, handled } = useAssistant();
  const dialog = useRef<HTMLDialogElement>(null);
  const { restore, ...floatingHandlers } = useFloatingWindow(dialog);
  const launcher = useRef<HTMLButtonElement>(null);
  const [selected, setSelected] = useState({ key: scope.key, text: '' });
  const [memory, setMemory] = useState({ key: scope.key, open, visited: [] as AssistantScope[], viewing: null as AssistantScope | null });
  if (memory.key !== scope.key || memory.open !== open) {
    setMemory({ key: scope.key, open, viewing: memory.key !== scope.key ? null : memory.viewing, visited: open ? [scope, ...memory.visited.filter(x => x.key !== scope.key)].slice(0, 8) : memory.visited });
  }
  const visited = memory.visited;
  const viewing = memory.viewing;
  const setViewing = (value: AssistantScope | null) => setMemory(old => ({ ...old, viewing: value }));
  const selection = selected.key === scope.key ? selected.text : '';
  const active = viewing ?? scope;
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) {
      element.show();
      restore();
      element.querySelector<HTMLTextAreaElement>('textarea')?.focus({ preventScroll: true });
    } else if (!open && element.open) { element.close(); launcher.current?.focus({ preventScroll: true }); }
  }, [open, restore]);
  useEffect(() => {
    function capture() {
      const selected = getSelection();
      const root = document.querySelector('main');
      if (!selected?.anchorNode || !selected.focusNode || !root?.contains(selected.anchorNode) || !root.contains(selected.focusNode)) { setSelected({ key: scope.key, text: '' }); return; }
      if (selected.anchorNode.parentElement?.closest('input,textarea,[contenteditable],dialog') || selected.focusNode.parentElement?.closest('input,textarea,[contenteditable],dialog')) return;
      setSelected({ key: scope.key, text: selected.toString().trim().slice(0, 300) });
    }
    function escape(event: KeyboardEvent) { if (event.key === 'Escape' && open) close(); }
    document.addEventListener('selectionchange', capture); document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('selectionchange', capture); document.removeEventListener('keydown', escape); };
  }, [open, close, scope.key]);
  return <>
    <div className={`entry-assistant-launcher entry-assistant-header-mobile global-assistant-launcher${open ? ' is-open' : ''}`}>
      {selection && !open && <button type="button" className="entry-selection-question" onClick={() => { setViewing(null); show('', selection); }}><span>“{selection.slice(0, 32)}{selection.length > 32 ? '…' : ''}”</span>问这句话 ↗</button>}
      <button ref={launcher} type="button" className="entry-assistant-trigger" aria-haspopup="dialog" aria-expanded={open} onClick={() => { setViewing(null); show(); }}>✦ 史料助手</button>
    </div>
    <dialog ref={dialog} {...floatingHandlers} className="entry-assistant-dialog global-assistant-panel" aria-label="史料助手" onClose={close} onCancel={close}>
      {visited.length > 1 && <div className="assistant-history"><label htmlFor="assistant-history">阅读中的讨论</label><select id="assistant-history" value={active.key} onChange={event => { const found = visited.find(x => x.key === event.target.value); setViewing(found?.key === scope.key ? null : found ?? null); handled(); }}>
        {[scope, ...visited.filter(x => x.key !== scope.key)].map(x => <option key={x.key} value={x.key}>{x.key === scope.key ? '当前 · ' : ''}{x.title}</option>)}
      </select>{viewing && <button onClick={() => setViewing(null)}>回到当前页面</button>}</div>}
      {open && <PageAssistant key={active.key} entryId={active.key} title={active.title} questions={[]} evidence={[]} request={viewing ? null : request}
        movable context={active.context ?? null} scopeLabel={active.label} focusPrompt={active.prompt} suggestions={active.suggestions}
        onClose={close} onRequestHandled={handled} onSection={id => { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); }}/>} 
    </dialog>
  </>;
}
