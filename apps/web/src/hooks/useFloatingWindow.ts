import { useCallback, useEffect, useRef, type KeyboardEvent, type PointerEvent, type RefObject } from 'react';

type Position = { left: number; top: number };
type Drag = Position & { id: number; x: number; y: number };

export function useFloatingWindow(dialog: RefObject<HTMLDialogElement | null>) {
  const position = useRef<Position | null>(null);
  const drag = useRef<Drag | null>(null);
  const place = useCallback((next: Position) => {
    const element = dialog.current;
    if (!element?.open) return;
    const box = element.getBoundingClientRect();
    const margin = 12;
    const left = Math.max(margin, Math.min(next.left, window.innerWidth - box.width - margin));
    const top = Math.max(margin, Math.min(next.top, window.innerHeight - box.height - margin));
    position.current = { left, top };
    Object.assign(element.style, { left: `${left}px`, top: `${top}px`, right: 'auto', bottom: 'auto', margin: '0' });
  }, [dialog]);
  const restore = useCallback(() => {
    const element = dialog.current;
    if (!element?.open) return;
    const box = element.getBoundingClientRect();
    place(position.current ?? { left: box.left, top: box.top });
  }, [dialog, place]);
  useEffect(() => {
    window.addEventListener('resize', restore);
    return () => window.removeEventListener('resize', restore);
  }, [restore]);

  function onPointerDown(event: PointerEvent<HTMLDialogElement>) {
    const target = event.target as Element;
    if (!event.isPrimary || event.button !== 0 || !target.closest('.assistant-header') || target.closest('button,a,input,textarea,select')) return;
    const box = event.currentTarget.getBoundingClientRect();
    drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY, left: box.left, top: box.top };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.currentTarget.dataset.dragging = 'true';
    event.preventDefault();
  }
  function onPointerMove(event: PointerEvent<HTMLDialogElement>) {
    const start = drag.current;
    if (!start || start.id !== event.pointerId) return;
    place({ left: start.left + event.clientX - start.x, top: start.top + event.clientY - start.y });
  }
  function stop(event: PointerEvent<HTMLDialogElement>) {
    if (drag.current?.id !== event.pointerId) return;
    drag.current = null;
    delete event.currentTarget.dataset.dragging;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }
  function onKeyDown(event: KeyboardEvent<HTMLDialogElement>) {
    if (!(event.target as Element).matches('.assistant-header')) return;
    const direction = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
    if (!direction) return;
    const box = event.currentTarget.getBoundingClientRect();
    const step = event.shiftKey ? 40 : 16;
    place({ left: box.left + direction[0] * step, top: box.top + direction[1] * step });
    event.preventDefault();
  }
  return { restore, onPointerDown, onPointerMove, onPointerUp: stop, onPointerCancel: stop, onLostPointerCapture: stop, onKeyDown };
}
