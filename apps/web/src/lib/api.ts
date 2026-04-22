import { supabase } from '../supabaseClient';
import type { Edge, Event, GraphResponse, Person } from '@histree/shared-types';

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
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function supabasePublicFetch<T>(path: string): Promise<T> {
  if (path === '/people') {
    const { data, error } = await supabase
      .from('person')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return (data ?? []).map((person) => ({ ...person, type: 'person' })) as T;
  }

  if (path === '/event') {
    const { data, error } = await supabase
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

  throw new Error(`No static Supabase fallback is available for ${path}.`);
}

async function getGraphFromSupabase(id: string): Promise<GraphResponse> {
  const { data: personData, error: personError } = await supabase
    .from('person')
    .select('*')
    .eq('id', id)
    .maybeSingle();

  if (personError) throw personError;

  const { data: eventData, error: eventError } = personData
    ? { data: null, error: null }
    : await supabase.from('event').select('*').eq('id', id).maybeSingle();

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
      supabase.from('person_relationship').select('person_b, relation_type, description').eq('person_a', id),
      supabase.from('person_relationship').select('person_a, relation_type, description').eq('person_b', id),
      supabase.from('person_event').select('event_id, role').eq('person_id', id),
    ]);

    if (relsAError) throw relsAError;
    if (relsBError) throw relsBError;
    if (personEventsError) throw personEventsError;

    relsA?.forEach((relationship) => {
      relatedPersonIds.add(relationship.person_b);
      edges.push({ source: id, target: relationship.person_b, type: relationship.relation_type, description: relationship.description });
    });

    relsB?.forEach((relationship) => {
      relatedPersonIds.add(relationship.person_a);
      edges.push({ source: relationship.person_a, target: id, type: relationship.relation_type, description: relationship.description });
    });

    personEvents?.forEach((personEvent) => {
      relatedEventIds.add(personEvent.event_id);
      edges.push({ source: id, target: personEvent.event_id, type: personEvent.role });
    });
  } else {
    relatedEventIds.add(id);

    const [{ data: eventPeople, error: eventPeopleError }, { data: effects, error: effectsError }, { data: causes, error: causesError }] = await Promise.all([
      supabase.from('person_event').select('person_id, role').eq('event_id', id),
      supabase.from('event_causality').select('effect_event_id, description').eq('cause_event_id', id),
      supabase.from('event_causality').select('cause_event_id, description').eq('effect_event_id', id),
    ]);

    if (eventPeopleError) throw eventPeopleError;
    if (effectsError) throw effectsError;
    if (causesError) throw causesError;

    eventPeople?.forEach((eventPerson) => {
      relatedPersonIds.add(eventPerson.person_id);
      edges.push({ source: eventPerson.person_id, target: id, type: eventPerson.role });
    });

    effects?.forEach((effect) => {
      relatedEventIds.add(effect.effect_event_id);
      edges.push({ source: id, target: effect.effect_event_id, type: 'causes', description: effect.description });
    });

    causes?.forEach((cause) => {
      relatedEventIds.add(cause.cause_event_id);
      edges.push({ source: cause.cause_event_id, target: id, type: 'causes', description: cause.description });
    });
  }

  const [people, events] = await Promise.all([
    getPeopleByIds(Array.from(relatedPersonIds)),
    getEventsByIds(Array.from(relatedEventIds)),
  ]);

  return {
    center,
    nodes: [...people, ...events],
    edges,
  };
}

async function getPeopleByIds(ids: string[]): Promise<Person[]> {
  if (ids.length === 0) return [];
  const { data, error } = await supabase.from('person').select('*').in('id', ids);
  if (error) throw error;
  return (data ?? []).map((person) => ({ ...person, type: 'person' }) as Person);
}

async function getEventsByIds(ids: string[]): Promise<Event[]> {
  if (ids.length === 0) return [];
  const { data, error } = await supabase.from('event').select('*').in('id', ids);
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
