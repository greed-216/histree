import { supabase, publicSupabase } from '../supabaseClient';
import type { Edge, Event, GraphResponse, Person, RelationshipBundle } from '@histree/shared-types';

const API_BASE = import.meta.env.VITE_API_URL as string | undefined;

type ApiOptions = RequestInit & {
  auth?: boolean;
};

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { auth = false, headers, ...requestInit } = options;
  const method = requestInit.method?.toUpperCase() ?? 'GET';

  if (!API_BASE && method === 'GET' && !auth) {
    return supabasePublicFetch<T>(path);
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

async function supabasePublicFetch<T>(path: string): Promise<T> {
  if (path === '/topics' || path.startsWith('/topics/')) {
    const slug = path.startsWith('/topics/') ? decodeURIComponent(path.slice(8)) : null;
    let query = publicSupabase.from('topic').select('*').eq('status', 'published').order('created_at');
    if (slug) query = query.eq('slug', slug);
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
      publicSupabase.from('source').select('*').eq('id', id).single(),
      publicSupabase.from('fact_claim').select('*, source:source_id(*)', { count: 'exact' })
        .eq('status', 'published').eq('source_id', id).order('id').range(page*50, page*50+49),
    ]);
    if (source.error) throw source.error;
    if (claims.error) throw claims.error;
    return { source: source.data, claims: claims.data ?? [], count: claims.count ?? 0 } as T;
  }
  if (path.startsWith('/evidence/')) {
    const [, , subject, id] = path.split('/');
    const { data, error } = await publicSupabase.from('fact_claim').select('*, source:source_id(*)')
      .eq('status', 'published').eq('subject_table', subject).eq('subject_id', id);
    if (error) throw error;
    return (data ?? []) as T;
  }
  if (path === '/people') {
    const { data, error } = await publicSupabase
      .from('person')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return (data ?? []).map((person) => ({ ...person, type: 'person' })) as T;
  }

  if (path === '/event') {
    const { data, error } = await publicSupabase
      .from('event')
      .select('*')
      .order('start_year', { ascending: true });

    if (error) throw error;
    return (data ?? []).map((event) => ({ ...event, type: 'event' })) as T;
  }

  if (path.startsWith('/graph/')) {
    const id = path.slice('/graph/'.length);
    return getGraphFromSupabase(id) as Promise<T>;
  }

  if (path === '/relationships') {
    return getRelationshipsFromSupabase() as Promise<T>;
  }

  throw new Error(`No static Supabase fallback is available for ${path}.`);
}

async function getRelationshipsFromSupabase(): Promise<RelationshipBundle> {
  const [personRelationships, personEvents, eventCausalities] = await Promise.all([
    publicSupabase.from('person_relationship').select('*').order('created_at', { ascending: false }),
    publicSupabase.from('person_event').select('*').order('created_at', { ascending: false }),
    publicSupabase.from('event_causality').select('*').order('created_at', { ascending: false }),
  ]);

  if (personRelationships.error) throw personRelationships.error;
  if (personEvents.error) throw personEvents.error;
  if (eventCausalities.error) throw eventCausalities.error;

  return {
    person_relationships: personRelationships.data ?? [],
    person_events: personEvents.data ?? [],
    event_causalities: eventCausalities.data ?? [],
  };
}

async function getGraphFromSupabase(id: string): Promise<GraphResponse> {
  const { data: personData, error: personError } = await publicSupabase
    .from('person')
    .select('*')
    .eq('id', id)
    .maybeSingle();

  if (personError) throw personError;

  const { data: eventData, error: eventError } = personData
    ? { data: null, error: null }
    : await publicSupabase.from('event').select('*').eq('id', id).maybeSingle();

  if (eventError) throw eventError;

  const center = personData
    ? ({ ...personData, type: 'person' } as Person)
    : eventData
      ? ({ ...eventData, type: 'event' } as Event)
      : null;

  if (!center) {
    throw new Error('Node not found');
  }

  const relatedPersonIds = new Set<string>();
  const relatedEventIds = new Set<string>();
  const edges: Edge[] = [];

  if (center.type === 'person') {
    relatedPersonIds.add(id);

    const [{ data: relsA, error: relsAError }, { data: relsB, error: relsBError }, { data: personEvents, error: personEventsError }] = await Promise.all([
      publicSupabase.from('person_relationship').select('id, person_b, relation_type, description').eq('person_a', id),
      publicSupabase.from('person_relationship').select('id, person_a, relation_type, description').eq('person_b', id),
      publicSupabase.from('person_event').select('id, event_id, role').eq('person_id', id),
    ]);

    if (relsAError) throw relsAError;
    if (relsBError) throw relsBError;
    if (personEventsError) throw personEventsError;

    relsA?.forEach((relationship) => {
      relatedPersonIds.add(relationship.person_b);
      edges.push({ id: relationship.id, subject_table: 'person_relationship', source: id, target: relationship.person_b, type: relationship.relation_type, description: relationship.description });
    });

    relsB?.forEach((relationship) => {
      relatedPersonIds.add(relationship.person_a);
      edges.push({ id: relationship.id, subject_table: 'person_relationship', source: relationship.person_a, target: id, type: relationship.relation_type, description: relationship.description });
    });

    personEvents?.forEach((personEvent) => {
      relatedEventIds.add(personEvent.event_id);
      edges.push({ id: personEvent.id, subject_table: 'person_event', source: id, target: personEvent.event_id, type: personEvent.role });
    });
  } else {
    relatedEventIds.add(id);

    const [{ data: eventPeople, error: eventPeopleError }, { data: effects, error: effectsError }, { data: causes, error: causesError }] = await Promise.all([
      publicSupabase.from('person_event').select('id, person_id, role').eq('event_id', id),
      publicSupabase.from('event_causality').select('id, effect_event_id, description').eq('cause_event_id', id),
      publicSupabase.from('event_causality').select('id, cause_event_id, description').eq('effect_event_id', id),
    ]);

    if (eventPeopleError) throw eventPeopleError;
    if (effectsError) throw effectsError;
    if (causesError) throw causesError;

    eventPeople?.forEach((eventPerson) => {
      relatedPersonIds.add(eventPerson.person_id);
      edges.push({ id: eventPerson.id, subject_table: 'person_event', source: eventPerson.person_id, target: id, type: eventPerson.role });
    });

    effects?.forEach((effect) => {
      relatedEventIds.add(effect.effect_event_id);
      edges.push({ id: effect.id, subject_table: 'event_causality', source: id, target: effect.effect_event_id, type: 'causes', description: effect.description });
    });

    causes?.forEach((cause) => {
      relatedEventIds.add(cause.cause_event_id);
      edges.push({ id: cause.id, subject_table: 'event_causality', source: cause.cause_event_id, target: id, type: 'causes', description: cause.description });
    });
  }

  const [people, events] = await Promise.all([
    getPeopleByIds(Array.from(relatedPersonIds)),
    getEventsByIds(Array.from(relatedEventIds)),
  ]);

  return {
    center,
    nodes: [...people, ...events],
    edges: edges.filter(e => [...people, ...events].some(n => n.id === e.source) && [...people, ...events].some(n => n.id === e.target)),
  };
}

async function getPeopleByIds(ids: string[]): Promise<Person[]> {
  if (ids.length === 0) return [];
  const { data, error } = await publicSupabase.from('person').select('*').in('id', ids);
  if (error) throw error;
  return (data ?? []).map((person) => ({ ...person, type: 'person' }) as Person);
}

async function getEventsByIds(ids: string[]): Promise<Event[]> {
  if (ids.length === 0) return [];
  const { data, error } = await publicSupabase.from('event').select('*').in('id', ids);
  if (error) throw error;
  return (data ?? []).map((event) => ({ ...event, type: 'event' }) as Event);
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
