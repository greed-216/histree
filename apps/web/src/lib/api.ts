import { exploreRequest, contentRequest, pageNumber, timelineYear } from '@histree/shared-types';
import { supabase, publicSupabase } from '../supabaseClient';


const API_BASE = import.meta.env.VITE_API_URL as string | undefined;

type ApiOptions = RequestInit & {
  auth?: boolean;
};

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { auth = false, headers, ...requestInit } = options;
  const method = requestInit.method?.toUpperCase() ?? 'GET';

  if (!API_BASE && method === 'GET' && !auth) {
    return supabasePublicFetch<T>(path, requestInit.signal ?? undefined);
  }

  if (!API_BASE) {
    throw new Error('API URL is not configured for this operation.');
  }

  const requestHeaders = new Headers(headers);

  if (auth) {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('Authentication is required.');
    }

    requestHeaders.set('Authorization', `Bearer ${session.access_token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...requestInit,
    headers: requestHeaders,
  });

  if (!response.ok) {
    const body = await response.text();
    let message = body;
    try { const parsed = JSON.parse(body); message = Array.isArray(parsed.message) ? parsed.message.join('；') : parsed.message || body; } catch { /* Response may be plain text. */ }
    throw new Error(message || `请求失败（${response.status}）`);
  }

  return response.json() as Promise<T>;
}

async function supabasePublicFetch<T>(path: string, signal?: AbortSignal): Promise<T> {
  if (path === '/timeline/overview') {
    let rpc = publicSupabase.rpc('timeline_overview');
    if (signal) rpc = rpc.abortSignal(signal);
    const { data, error } = await rpc;
    if (error) throw error;
    return data as T;
  }
  if (path.startsWith('/timeline?')) {
    const url = new URL(path, 'https://histree.local');
    if (url.searchParams.has('year')) {
      const year = timelineYear(url.searchParams.get('year')), page = pageNumber(url.searchParams.get('page'));
      let query = publicSupabase.from('event').select('*').eq('status', 'published')
        .lte('start_year', year).or(`end_year.gte.${year},and(end_year.is.null,start_year.eq.${year})`)
        .order('start_year').order('id').range(page * 20, page * 20 + 20);
      if (signal) query = query.abortSignal(signal);
      const { data, error } = await query;
      if (error) throw error;
      return { items: (data ?? []).slice(0, 20), has_more: (data?.length ?? 0) > 20 } as T;
    }
  }
  if(path.startsWith('/catalog/')) {
    let rpc=publicSupabase.rpc('content_page',contentRequest(path));if(signal)rpc=rpc.abortSignal(signal);
    const {data,error}=await rpc;if(error)throw error;return data as T;
  }
  if(path.startsWith('/entry-context/')) {
    const url=new URL(path,'https://histree.local'),id=url.pathname.split('/')[2];exploreRequest(`/entry/${id}`);
    let rpc=publicSupabase.rpc('entry_context',{p_id:id,p_page:pageNumber(url.searchParams.get('page'))});if(signal)rpc=rpc.abortSignal(signal);
    const {data,error}=await rpc;if(error)throw error;if(!data)throw new Error('条目尚未发布或不存在');return data as T;
  }
  const request = exploreRequest(path);
  if (request) {
    let rpc = publicSupabase.rpc(request.name, request.args);
    if (signal) rpc = rpc.abortSignal(signal);
    const { data, error } = await rpc;
    if (error) throw error;
    if (!data) throw new Error('条目尚未发布或不存在');
    return data as T;
  }
  if (path.startsWith('/topics/')) {
    const slug = path.startsWith('/topics/') ? decodeURIComponent(path.slice(8)) : null;
    let query = publicSupabase.from('topic').select('*').eq('status', 'published').order('created_at');
    if (slug) query = query.eq('slug', slug);
    if(signal)query=query.abortSignal(signal);
    const { data, error } = await query;
    if (error) throw error;
    if (slug && !data?.length) throw new Error('专题尚未发布或不存在');
    return (slug ? data![0] : data ?? []) as T;
  }
  if (path.startsWith('/sources/')) {
    const url = new URL(path, 'https://histree.local');
    const id = url.pathname.split('/')[2];
    const page = Number(url.searchParams.get('page') ?? 0);
    if (!/^[0-9a-f-]{36}$/i.test(id) || !Number.isInteger(page) || page < 0 || page > 100000) throw new Error('无效的来源地址');
    const [source, claims] = await Promise.all([
      publicSupabase.from('source').select('*').eq('id', id).abortSignal(signal??new AbortController().signal).single(),
      publicSupabase.from('fact_claim').select('*, source:source_id(*)', { count: 'exact' })
        .eq('status', 'published').eq('source_id', id).order('id').range(page*50, page*50+49).abortSignal(signal??new AbortController().signal),
    ]);
    if (source.error) throw source.error;
    if (claims.error) throw claims.error;
    return { source: source.data, claims: claims.data ?? [], count: claims.count ?? 0 } as T;
  }
  const url=new URL(path,'https://histree.local');
  if(['/people','/event','/topics','/timeline'].includes(url.pathname)) {
    const table=url.pathname==='/people'?'person':url.pathname==='/topics'?'topic':'event';
    return supabasePublicFetch<T>(`/catalog/${table}?${url.searchParams}`,signal);
  }
  if(url.pathname.startsWith('/evidence/')) {
    const [, ,subject,id]=url.pathname.split('/');url.searchParams.set('subject',subject);url.searchParams.set('subject_id',id);
    return supabasePublicFetch<T>(`/catalog/fact_claim?${url.searchParams}`,signal);
  }
  if(url.pathname.startsWith('/graph/'))return supabasePublicFetch<T>(`/entry-context/${url.pathname.split('/')[2]}?${url.searchParams}`,signal);
  if(url.pathname==='/relationships') {
    const [p,pe,e]=await Promise.all(['person_relationship','person_event','event_causality'].map(table=>supabasePublicFetch<{items:unknown[],has_more:boolean}>(`/catalog/${table}?${url.searchParams}`,signal)));
    return {person_relationships:p.items,person_events:pe.items,event_causalities:e.items,has_more:p.has_more||pe.has_more||e.has_more} as T;
  }
  throw new Error(`No static Supabase fallback is available for ${path}.`);
}

export async function getCurrentUserRole(): Promise<'admin' | 'user' | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    return null;
  }

  const { data, error } = await supabase
    .from('user_roles')
    .select('role')
    .eq('user_id', session.user.id)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return data?.role === 'admin' ? 'admin' : 'user';
}
