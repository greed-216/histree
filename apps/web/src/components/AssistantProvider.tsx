import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { AssistantContext, type AssistantScope, type AssistantRequest } from '../hooks/useAssistant';

const generalSuggestions = ['我可以从哪里开始了解这段历史？', '帮我查找一个人物或事件的史料。'];
function pageScope(pathname: string, search: string): AssistantScope {
  const labels: Record<string, string> = { '/': '历史探索', '/people': '历史人物', '/events': '历史事件', '/graph': '历史图谱', '/map': '历史地图', '/search': '搜索结果', '/ask': '问史料', '/timeline': '历史时间线' };
  const title = labels[pathname] || (pathname.startsWith('/graph') ? '历史图谱' : pathname.startsWith('/learn') ? '历史导读' : '史料阅读');
  const query = new URLSearchParams(search).get('q');
  return { key: `page:${pathname}${search}`, title: query ? `${title} · ${query}` : title, label: '全站史料', prompt: query ? `当前搜索词为“${query.slice(0, 80)}”。` : undefined, suggestions: generalSuggestions };
}
export function AssistantProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [registered, setRegistered] = useState<{ owner: symbol; scope: AssistantScope } | null>(null);
  const serial = useRef(0);
  const [open, setOpen] = useState(false);
  const [request, setRequest] = useState<AssistantRequest | null>(null);
  const register = useCallback((scope: AssistantScope) => {
    const owner = Symbol(); setRegistered({ owner, scope });
    return () => setRegistered(old => old?.owner === owner ? null : old);
  }, []);
  const show = useCallback((question = '', selectedText?: string) => { setRequest(question || selectedText ? { question, selectedText, serial: ++serial.current } : null); setOpen(true); }, []);
  const close = useCallback(() => setOpen(false), []);
  const handled = useCallback(() => setRequest(null), []);
  const fallback = useMemo(() => pageScope(location.pathname, location.search), [location.pathname, location.search]);
  const scope = registered?.scope ?? fallback;
  const value = useMemo(() => ({ scope, open, request, show, close, handled, register }), [scope, open, request, show, close, handled, register]);
  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}
