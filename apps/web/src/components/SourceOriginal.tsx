import { useEffect, useRef } from 'react';
import type { SourceText } from '@histree/shared-types';
import { useResource } from '../hooks/useResource';
import { sourceCitation } from '../lib/source-reading';
import { LoadState } from './Reading';
import '../styles/source-reading.css';

export function SourceOriginal({ id, archive, quote, citation, selected, selectionLoading = false }: {
  id: string; archive?: string; quote?: string; citation?: string; selected: boolean; selectionLoading?: boolean;
}) {
  const result = useResource<SourceText | null>(`/sources/${id}/text`);
  const section = useRef<HTMLElement>(null);
  const text = result.data && result.data.archive_url === archive ? result.data.content : undefined;
  const excerpt = quote?.trim();
  const start = excerpt && text ? text.indexOf(excerpt) : -1;
  useEffect(() => {
    if (!selected || result.loading || selectionLoading) return;
    (section.current?.querySelector('mark') || section.current)?.scrollIntoView({ block: 'start' });
  }, [id, selected, result.loading, selectionLoading, text, excerpt]);
  return <section ref={section} id="original" className="source-original" aria-labelledby="original-heading">
    <div className="source-original-heading"><div><p className="eyebrow">回到史料</p><h2 id="original-heading">原文片段</h2></div><span>已引用片段</span></div>
    {citation && <p className="source-original-location">{sourceCitation(citation)}</p>}
    <LoadState {...result} />
    {!result.loading && !result.error && (text ? <>
      {selectionLoading ? <p className="source-original-caption">正在定位这条引文…</p> : selected && excerpt && <p className="source-original-caption">{start >= 0 ? '本条所引文字已标出，可结合前后文阅读。' : '本条摘录未能在此片段中连续匹配，可结合下方引用核对。'}</p>}
      <div className="source-original-text">{start >= 0 && excerpt ? <>{text.slice(0, start)}<mark>{excerpt}</mark>{text.slice(start + excerpt.length)}</> : text}</div>
    </> : <p className="source-original-empty">原文片段暂未收录，可以先查看下方引文。</p>)}
  </section>;
}
