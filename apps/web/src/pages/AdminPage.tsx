import React, { useCallback, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';
import { PlusIcon, TrashIcon, PencilIcon, PhotoIcon, MapPinIcon } from '@heroicons/react/24/outline';
import type {
  Event,
  EventCausalityRelation,
  Person,
  PersonEventRelation,
  PersonRelationship,
  ReferenceLink,
  RelationshipBundle,
} from '@histree/shared-types';
import { apiFetch } from '../lib/api';
import { Link } from 'react-router-dom';
import { PublicationField } from '../components/PublicationField';
import { referenceTypeLabel } from '../lib/content';
import { relationshipSentence } from '../lib/graph';

export const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'people' | 'events' | 'relationships'>('people');
  const [people, setPeople] = useState<Person[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [relationships, setRelationships] = useState<RelationshipBundle>({
    person_relationships: [],
    person_events: [],
    event_causalities: [],
  });
  
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState('');
  const statusBadge = (status?: string) => <span className={`ml-2 text-xs font-normal ${status === 'published' ? 'text-teal-700' : 'text-amber-700'}`}>{status === 'published' ? '已发布' : '草稿'}</span>;
  const run = async (action: () => Promise<void>) => { setBusy(true); setError(''); try { await action(); } catch (e) { setError(e instanceof Error ? e.message : '操作失败'); } finally { setBusy(false); } };

  // Edit states
  const [editingPerson, setEditingPerson] = useState<Partial<Person> | null>(null);
  const [editingEvent, setEditingEvent] = useState<Partial<Event> | null>(null);
  const [editingPersonRelationship, setEditingPersonRelationship] = useState<Partial<PersonRelationship> | null>(null);
  const [editingPersonEvent, setEditingPersonEvent] = useState<Partial<PersonEventRelation> | null>(null);
  const [editingEventCausality, setEditingEventCausality] = useState<Partial<EventCausalityRelation> | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  const parseList = (value: string) => value.split(/[,，]/).map((item) => item.trim()).filter(Boolean);
  const parseNumber = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return undefined;
    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : undefined;
  };
  const parseReferences = (value: string): ReferenceLink[] =>
    value
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [title, type, url, note] = line.split('|').map((item) => item.trim());
        return {
          title,
          reference_type: (type as ReferenceLink['reference_type']) || 'reference',
          url: url || undefined,
          note: note || undefined,
        };
      })
      .filter((reference) => reference.title);
  const formatReferences = (references?: ReferenceLink[]) =>
    references?.map((reference) => [reference.title, reference.reference_type, reference.url ?? '', reference.note ?? ''].join(' | ')).join('\n') ?? '';

  const fetchData = useCallback(async () => {
    const [pData, eData, person_relationships, person_events, event_causalities] = await Promise.all([
      apiFetch<Person[]>('/editorial/person', { auth: true }),
      apiFetch<Event[]>('/editorial/event', { auth: true }),
      apiFetch<PersonRelationship[]>('/editorial/person_relationship', { auth: true }),
      apiFetch<PersonEventRelation[]>('/editorial/person_event', { auth: true }),
      apiFetch<EventCausalityRelation[]>('/editorial/event_causality', { auth: true }),
    ]);
    const relationshipData = { person_relationships, person_events, event_causalities };
    setPeople(pData);
    setEvents(eData);
    setRelationships(relationshipData);
  }, []);

  useEffect(() => {
    let active = true;
    const check = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!active) return;
      if (!session) { setLoading(false); return; }
      const { data: roles, error: roleError } = await supabase.from('user_roles').select('role').eq('user_id', session.user.id).single();
      if (!active) return;
      if (roleError) throw roleError;
      if (roles?.role === 'admin') { setIsAdmin(true); await fetchData(); }
      if (active) setLoading(false);
    };
    check().catch(e => { if (active) { setError(e.message); setLoading(false); } });
    return () => { active = false; };
  }, [fetchData]);

  const personName = (id?: string) => people.find((person) => person.id === id)?.name ?? id ?? '-';
  const eventTitle = (id?: string) => events.find((event) => event.id === id)?.title ?? id ?? '-';

  const savePerson = async () => {
    if (!editingPerson?.name?.trim()) throw new Error('请填写人物姓名');

    if (editingPerson.id) {
      await apiFetch<Person>(`/people/${editingPerson.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingPerson),
        auth: true,
      });
    } else {
      await apiFetch<Person>('/people', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingPerson),
        auth: true,
      });
    }
    setEditingPerson(null);
    await fetchData();
  };

  const deletePerson = async (id: string) => {
    if (!confirm('确定要删除这位人物吗？')) return;
    await apiFetch<{ id: string }>(`/people/${id}`, {
      method: 'DELETE',
      auth: true,
    });
    await fetchData();
  };

  const saveEvent = async () => {
    if (!editingEvent?.title?.trim()) throw new Error('请填写事件标题');

    const lat = editingEvent.location_lat ?? null;
    const lng = editingEvent.location_lng ?? null;
    if ((lat === null) !== (lng === null)) throw new Error('纬度和经度需要同时填写或同时留空');
    if ((lat !== null && Math.abs(lat) > 90) || (lng !== null && Math.abs(lng) > 180)) throw new Error('经纬度超出有效范围');
    if (editingEvent.start_year != null && editingEvent.end_year != null && editingEvent.start_year > editingEvent.end_year) throw new Error('起始年份不能晚于结束年份');
    const body = JSON.stringify({ ...editingEvent, location_lat: lat, location_lng: lng, start_year: editingEvent.start_year ?? null, end_year: editingEvent.end_year ?? null });
    if (editingEvent.id) {
      await apiFetch<Event>(`/event/${editingEvent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body,
        auth: true,
      });
    } else {
      await apiFetch<Event>('/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        auth: true,
      });
    }
    setEditingEvent(null);
    await fetchData();
  };

  const deleteEvent = async (id: string) => {
    if (!confirm('确定要删除这条事件吗？')) return;
    await apiFetch<{ id: string }>(`/event/${id}`, {
      method: 'DELETE',
      auth: true,
    });
    await fetchData();
  };

  const savePersonRelationship = async () => {
    if (!editingPersonRelationship?.person_a || !editingPersonRelationship.person_b || !editingPersonRelationship.relation_type) throw new Error('请补全人物关系');

    const payload = {
      status: editingPersonRelationship.status ?? 'draft',
      person_a: editingPersonRelationship.person_a,
      person_b: editingPersonRelationship.person_b,
      relation_type: editingPersonRelationship.relation_type,
      description: editingPersonRelationship.description,
    };

    if (editingPersonRelationship.id) {
      await apiFetch<PersonRelationship>(`/relationships/person-relationships/${editingPersonRelationship.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    } else {
      await apiFetch<PersonRelationship>('/relationships/person-relationships', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    }

    setEditingPersonRelationship(null);
    await fetchData();
  };

  const savePersonEvent = async () => {
    if (!editingPersonEvent?.person_id || !editingPersonEvent.event_id || !editingPersonEvent.role) throw new Error('请补全参与关系');

    const payload = {
      status: editingPersonEvent.status ?? 'draft',
      person_id: editingPersonEvent.person_id,
      event_id: editingPersonEvent.event_id,
      role: editingPersonEvent.role,
    };

    if (editingPersonEvent.id) {
      await apiFetch<PersonEventRelation>(`/relationships/person-events/${editingPersonEvent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    } else {
      await apiFetch<PersonEventRelation>('/relationships/person-events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    }

    setEditingPersonEvent(null);
    await fetchData();
  };

  const saveEventCausality = async () => {
    if (!editingEventCausality?.cause_event_id || !editingEventCausality.effect_event_id) throw new Error('请选择前后事件');

    const payload = {
      status: editingEventCausality.status ?? 'draft',
      cause_event_id: editingEventCausality.cause_event_id,
      effect_event_id: editingEventCausality.effect_event_id,
      description: editingEventCausality.description,
    };

    if (editingEventCausality.id) {
      await apiFetch<EventCausalityRelation>(`/relationships/event-causalities/${editingEventCausality.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    } else {
      await apiFetch<EventCausalityRelation>('/relationships/event-causalities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        auth: true,
      });
    }

    setEditingEventCausality(null);
    await fetchData();
  };

  const deleteRelationship = async (path: string, message: string) => {
    if (!confirm(message)) return;
    await apiFetch<{ id: string }>(path, {
      method: 'DELETE',
      auth: true,
    });
    await fetchData();
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>, isPerson: boolean) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiFetch<{ url: string }>('/upload', {
        method: 'POST',
        body: formData,
        auth: true,
      });
      
      if (isPerson && editingPerson) {
        setEditingPerson({ ...editingPerson, image_url: res.url });
      } else if (!isPerson && editingEvent) {
        setEditingEvent({ ...editingEvent, image_url: res.url });
      }
    } catch (err) {
      console.error('Image upload error:', err);
      alert('图片上传失败。');
    } finally {
      setUploadingImage(false);
    }
  };

  if (loading) return <div className="p-12 text-center text-slate-500">加载中...</div>;
  if (!isAdmin) return <div className="p-12 text-center text-rose-500 font-bold">无权访问，只有管理员可进入。</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8">
      <Link to="/admin/editorial" className="inline-block text-sky-700 underline">专题与出处管理 →</Link>
      {error && <p role="alert" className="p-4 bg-rose-50 text-rose-700 rounded-xl">{error}</p>}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">数据管理</h1>
        <div className="flex gap-2 bg-slate-200/50 p-1 rounded-xl">
          <button 
            onClick={() => setActiveTab('people')} 
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'people' ? 'bg-white shadow-sm text-sky-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            人物
          </button>
          <button 
            onClick={() => setActiveTab('events')} 
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'events' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            事件
          </button>
          <button
            onClick={() => setActiveTab('relationships')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'relationships' ? 'bg-white shadow-sm text-emerald-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            关系
          </button>
        </div>
      </div>

      {activeTab !== 'relationships' && <input aria-label="筛选人物或事件" placeholder="按姓名或事件标题筛选…" className="reading-input" value={query} onChange={e => setQuery(e.target.value)} />}
      {activeTab === 'people' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h2 className="font-semibold text-slate-700">人物管理</h2>
            <button onClick={() => setEditingPerson({})} className="flex items-center gap-1 bg-sky-500 hover:bg-sky-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
              <PlusIcon className="w-4 h-4" /> 新增人物
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-medium">
                <tr>
                  <th className="px-6 py-3">姓名</th>
                  <th className="px-6 py-3">时代</th>
                  <th className="px-6 py-3">出处</th>
                  <th className="px-6 py-3">图片</th>
                  <th className="px-6 py-3 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {people.filter(p => p.name.includes(query)).map(p => (
                  <tr key={p.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-semibold text-slate-800">{p.name}{statusBadge(p.status)}</td>
                    <td className="px-6 py-4">{p.era}</td>
                    <td className="px-6 py-4">{p.references?.length || 0}</td>
                    <td className="px-6 py-4">
                      {p.image_url ? <img src={p.image_url} className="w-8 h-8 rounded-full object-cover border border-slate-200" /> : '-'}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => setEditingPerson(p)} className="p-1.5 text-sky-500 hover:bg-sky-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                      <button disabled={busy} onClick={() => run(() => deletePerson(p.id))} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'events' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h2 className="font-semibold text-slate-700">事件管理</h2>
            <button onClick={() => setEditingEvent({})} className="flex items-center gap-1 bg-orange-500 hover:bg-orange-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
              <PlusIcon className="w-4 h-4" /> 新增事件
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-medium">
                <tr>
                  <th className="px-6 py-3">标题</th>
                  <th className="px-6 py-3">年份</th>
                  <th className="px-6 py-3">地点</th>
                  <th className="px-6 py-3">出处</th>
                  <th className="px-6 py-3 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {events.filter(e => e.title.includes(query)).map(e => (
                  <tr key={e.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-semibold text-slate-800">{e.title}{statusBadge(e.status)}</td>
                    <td className="px-6 py-4">{e.start_year}</td>
                    <td className="px-6 py-4">{e.location_name || '-'}</td>
                    <td className="px-6 py-4">{e.references?.length || 0}</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => setEditingEvent(e)} className="p-1.5 text-orange-500 hover:bg-orange-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                      <button disabled={busy} onClick={() => run(() => deleteEvent(e.id))} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'relationships' && (
        <div className="space-y-6">

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="font-semibold text-slate-700">人物关系</h2>
              <button
                onClick={() => setEditingPersonRelationship({
                  person_a: people[0]?.id,
                  person_b: people[1]?.id ?? people[0]?.id,
                  relation_type: '',
                })}
                className="flex items-center gap-1 bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                disabled={people.length < 2}
              >
                <PlusIcon className="w-4 h-4" /> 新增人物关系
              </button>
            </div>
            {editingPersonRelationship && (
              <div className="p-4 border-b border-slate-100 grid gap-3 md:grid-cols-[1fr_1fr_1fr_1.5fr_auto]">
                <p className="md:col-span-full text-sm text-slate-600">方向约定：A —关系→ B 表示 A 是 B 的该关系。例如：A —父亲→ B 表示 A 是 B 的父亲。兄弟、夫妻等对称关系不区分方向。</p>
                <PublicationField value={editingPersonRelationship.status} onChange={status => setEditingPersonRelationship({...editingPersonRelationship, status})} />
                <select value={editingPersonRelationship.person_a || ''} onChange={e => setEditingPersonRelationship({ ...editingPersonRelationship, person_a: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {people.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}
                </select>
                <select value={editingPersonRelationship.person_b || ''} onChange={e => setEditingPersonRelationship({ ...editingPersonRelationship, person_b: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {people.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}
                </select>
                <input placeholder="关系类型" value={editingPersonRelationship.relation_type || ''} onChange={e => setEditingPersonRelationship({ ...editingPersonRelationship, relation_type: e.target.value })} className="w-full p-2 border rounded-lg text-sm" />
                <input placeholder="说明" value={editingPersonRelationship.description || ''} onChange={e => setEditingPersonRelationship({ ...editingPersonRelationship, description: e.target.value })} className="w-full p-2 border rounded-lg text-sm" />
                <p className="md:col-span-full text-sm font-medium text-teal-800">预览：{editingPersonRelationship.relation_type ? relationshipSentence(personName(editingPersonRelationship.person_a || ''), personName(editingPersonRelationship.person_b || ''), editingPersonRelationship.relation_type) : '请选择两位人物并填写关系类型'}</p>
                <div className="flex gap-2">
                  <button onClick={() => setEditingPersonRelationship(null)} className="px-3 py-2 text-slate-500 hover:bg-slate-100 rounded-lg text-sm">取消</button>
                  <button disabled={busy} onClick={() => run(savePersonRelationship)} className="px-3 py-2 bg-emerald-500 text-white rounded-lg text-sm">保存</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-3">人物 A</th>
                    <th className="px-6 py-3">人物 B</th>
                    <th className="px-6 py-3">类型</th>
                    <th className="px-6 py-3">说明</th>
                    <th className="px-6 py-3 text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {relationships.person_relationships.map(relationship => (
                    <tr key={relationship.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-semibold text-slate-800">{personName(relationship.person_a)}</td>
                      <td className="px-6 py-4 font-semibold text-slate-800">{personName(relationship.person_b)}</td>
                      <td className="px-6 py-4">{relationshipSentence(personName(relationship.person_a), personName(relationship.person_b), relationship.relation_type)}{statusBadge(relationship.status)}</td>
                      <td className="px-6 py-4">{relationship.description || '-'}</td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button onClick={() => setEditingPersonRelationship(relationship)} className="p-1.5 text-emerald-500 hover:bg-emerald-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                        <button onClick={() => run(() => deleteRelationship(`/relationships/person-relationships/${relationship.id}`, '确定要删除这条人物关系吗？'))} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  ))}
                  {relationships.person_relationships.length === 0 && (
                    <tr><td className="px-6 py-6 text-slate-400" colSpan={5}>暂无人物关系。</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="font-semibold text-slate-700">事件参与</h2>
              <button
                onClick={() => setEditingPersonEvent({ person_id: people[0]?.id, event_id: events[0]?.id, role: '' })}
                className="flex items-center gap-1 bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                disabled={people.length === 0 || events.length === 0}
              >
                <PlusIcon className="w-4 h-4" /> 新增参与关系
              </button>
            </div>
            {editingPersonEvent && (
              <div className="p-4 border-b border-slate-100 grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]">
                <PublicationField value={editingPersonEvent.status} onChange={status => setEditingPersonEvent({...editingPersonEvent, status})} />
                <select value={editingPersonEvent.person_id || ''} onChange={e => setEditingPersonEvent({ ...editingPersonEvent, person_id: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {people.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}
                </select>
                <select value={editingPersonEvent.event_id || ''} onChange={e => setEditingPersonEvent({ ...editingPersonEvent, event_id: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {events.map(event => <option key={event.id} value={event.id}>{event.title}</option>)}
                </select>
                <input placeholder="角色" value={editingPersonEvent.role || ''} onChange={e => setEditingPersonEvent({ ...editingPersonEvent, role: e.target.value })} className="w-full p-2 border rounded-lg text-sm" />
                <div className="flex gap-2">
                  <button onClick={() => setEditingPersonEvent(null)} className="px-3 py-2 text-slate-500 hover:bg-slate-100 rounded-lg text-sm">取消</button>
                  <button disabled={busy} onClick={() => run(savePersonEvent)} className="px-3 py-2 bg-indigo-500 text-white rounded-lg text-sm">保存</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-3">人物</th>
                    <th className="px-6 py-3">事件</th>
                    <th className="px-6 py-3">角色</th>
                    <th className="px-6 py-3 text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {relationships.person_events.map(relation => (
                    <tr key={relation.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-semibold text-slate-800">{personName(relation.person_id)}</td>
                      <td className="px-6 py-4">{eventTitle(relation.event_id)}</td>
                      <td className="px-6 py-4">{relation.role}{statusBadge(relation.status)}</td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button onClick={() => setEditingPersonEvent(relation)} className="p-1.5 text-indigo-500 hover:bg-indigo-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                        <button onClick={() => run(() => deleteRelationship(`/relationships/person-events/${relation.id}`, '确定要删除这条参与关系吗？'))} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  ))}
                  {relationships.person_events.length === 0 && (
                    <tr><td className="px-6 py-6 text-slate-400" colSpan={4}>暂无事件参与关系。</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="font-semibold text-slate-700">事件因果</h2>
              <button
                onClick={() => setEditingEventCausality({
                  cause_event_id: events[0]?.id,
                  effect_event_id: events[1]?.id ?? events[0]?.id,
                })}
                className="flex items-center gap-1 bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                disabled={events.length < 2}
              >
                <PlusIcon className="w-4 h-4" /> 新增因果关系
              </button>
            </div>
            {editingEventCausality && (
              <div className="p-4 border-b border-slate-100 grid gap-3 md:grid-cols-[1fr_1fr_1.5fr_auto]">
                <PublicationField value={editingEventCausality.status} onChange={status => setEditingEventCausality({...editingEventCausality, status})} />
                <select value={editingEventCausality.cause_event_id || ''} onChange={e => setEditingEventCausality({ ...editingEventCausality, cause_event_id: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {events.map(event => <option key={event.id} value={event.id}>{event.title}</option>)}
                </select>
                <select value={editingEventCausality.effect_event_id || ''} onChange={e => setEditingEventCausality({ ...editingEventCausality, effect_event_id: e.target.value })} className="w-full p-2 border rounded-lg text-sm">
                  {events.map(event => <option key={event.id} value={event.id}>{event.title}</option>)}
                </select>
                <input placeholder="说明" value={editingEventCausality.description || ''} onChange={e => setEditingEventCausality({ ...editingEventCausality, description: e.target.value })} className="w-full p-2 border rounded-lg text-sm" />
                <div className="flex gap-2">
                  <button onClick={() => setEditingEventCausality(null)} className="px-3 py-2 text-slate-500 hover:bg-slate-100 rounded-lg text-sm">取消</button>
                  <button disabled={busy} onClick={() => run(saveEventCausality)} className="px-3 py-2 bg-amber-500 text-white rounded-lg text-sm">保存</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-3">原因事件</th>
                    <th className="px-6 py-3">结果事件</th>
                    <th className="px-6 py-3">说明</th>
                    <th className="px-6 py-3 text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {relationships.event_causalities.map(relation => (
                    <tr key={relation.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-semibold text-slate-800">{eventTitle(relation.cause_event_id)}</td>
                      <td className="px-6 py-4">{eventTitle(relation.effect_event_id)}</td>
                      <td className="px-6 py-4">{relation.description || '-'}{statusBadge(relation.status)}</td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button onClick={() => setEditingEventCausality(relation)} className="p-1.5 text-amber-500 hover:bg-amber-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                        <button onClick={() => run(() => deleteRelationship(`/relationships/event-causalities/${relation.id}`, '确定要删除这条事件因果关系吗？'))} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  ))}
                  {relationships.event_causalities.length === 0 && (
                    <tr><td className="px-6 py-6 text-slate-400" colSpan={4}>暂无事件因果关系。</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Edit Person Modal */}
      {editingPerson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold">{editingPerson.id ? '编辑人物' : '新增人物'}</h3>
            <PublicationField value={editingPerson.status} onChange={status => setEditingPerson({...editingPerson, status})} />
            <input placeholder="姓名" value={editingPerson.name || ''} onChange={e => setEditingPerson({...editingPerson, name: e.target.value})} className="w-full p-2 border rounded-lg" />
            <div className="grid grid-cols-2 gap-2">
              <label className="text-sm">出生年份<input type="number" value={editingPerson.birth_year ?? ''} onChange={e => setEditingPerson({...editingPerson, birth_year: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg" /></label>
              <label className="text-sm">去世年份<input type="number" value={editingPerson.death_year ?? ''} onChange={e => setEditingPerson({...editingPerson, death_year: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg" /></label>
            </div>
            <input placeholder="时代" value={editingPerson.era || ''} onChange={e => setEditingPerson({...editingPerson, era: e.target.value})} className="w-full p-2 border rounded-lg" />
            <div className="grid grid-cols-2 gap-2">
              <input placeholder="阵营" value={editingPerson.faction || ''} onChange={e => setEditingPerson({...editingPerson, faction: e.target.value})} className="w-full p-2 border rounded-lg" />
              <input placeholder="籍贯" value={editingPerson.native_place || ''} onChange={e => setEditingPerson({...editingPerson, native_place: e.target.value})} className="w-full p-2 border rounded-lg" />
            </div>
            <input placeholder="别名（用逗号分隔）" value={editingPerson.aliases?.join('，') || ''} onChange={e => setEditingPerson({...editingPerson, aliases: parseList(e.target.value)})} className="w-full p-2 border rounded-lg" />
            <input placeholder="标签（用逗号分隔）" value={editingPerson.tags?.join('，') || ''} onChange={e => setEditingPerson({...editingPerson, tags: parseList(e.target.value)})} className="w-full p-2 border rounded-lg" />
            <textarea placeholder="概述" value={editingPerson.description || ''} onChange={e => setEditingPerson({...editingPerson, description: e.target.value})} className="w-full p-2 border rounded-lg" rows={3} />
            <textarea placeholder="生平" value={editingPerson.biography || ''} onChange={e => setEditingPerson({...editingPerson, biography: e.target.value})} className="w-full p-2 border rounded-lg" rows={5} />
            <textarea placeholder="历史评价" value={editingPerson.historical_evaluation || ''} onChange={e => setEditingPerson({...editingPerson, historical_evaluation: e.target.value})} className="w-full p-2 border rounded-lg" rows={3} />
            <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-sm font-medium text-slate-700">参考资料</div>
              <textarea
                placeholder="标题 | 类型 | 链接 | 备注&#10;例如：维基百科：管仲 | encyclopedia | https://zh.wikipedia.org/wiki/管仲 | 便于快速定位"
                value={formatReferences(editingPerson.references)}
                onChange={e => setEditingPerson({ ...editingPerson, references: parseReferences(e.target.value) })}
                className="w-full p-2 border rounded-lg bg-white text-sm"
                rows={5}
              />
              <div className="text-xs text-slate-500">
                类型可填：encyclopedia、primary、reference、scholarship、digital。
              </div>
              {editingPerson.references && editingPerson.references.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {editingPerson.references.map((reference, index) => (
                    <span key={`${reference.title}-${index}`} className="px-2 py-1 rounded-md border border-slate-200 bg-white text-xs text-slate-600">
                      {reference.title} · {referenceTypeLabel(reference.reference_type)}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <PhotoIcon className="w-5 h-5 text-slate-400" />
                <input placeholder="图片链接" value={editingPerson.image_url || ''} onChange={e => setEditingPerson({...editingPerson, image_url: e.target.value})} className="w-full p-2 border rounded-lg" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500 px-7">或直接上传</span>
                <input type="file" accept="image/*" onChange={e => handleImageUpload(e, true)} disabled={uploadingImage} className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 disabled:opacity-50" />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button onClick={() => setEditingPerson(null)} className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-lg">取消</button>
              <button disabled={busy} onClick={() => run(savePerson)} className="px-4 py-2 bg-sky-500 text-white rounded-lg">保存</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Event Modal */}
      {editingEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold">{editingEvent.id ? '编辑事件' : '新增事件'}</h3>
            <PublicationField value={editingEvent.status} onChange={status => setEditingEvent({...editingEvent, status})} />
            <input placeholder="标题" value={editingEvent.title || ''} onChange={e => setEditingEvent({...editingEvent, title: e.target.value})} className="w-full p-2 border rounded-lg" />
            <div className="flex gap-2">
              <input type="number" placeholder="起始年份" value={editingEvent.start_year ?? ''} onChange={e => setEditingEvent({...editingEvent, start_year: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg" />
              <input placeholder="时代 / 国家" value={editingEvent.dynasty || ''} onChange={e => setEditingEvent({...editingEvent, dynasty: e.target.value})} className="w-full p-2 border rounded-lg" />
            </div>
            <label className="block text-sm">结束年份<input type="number" value={editingEvent.end_year ?? ''} onChange={e => setEditingEvent({...editingEvent, end_year: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg" /></label>
            <div className="space-y-3"><h4 className="font-medium">事件阶段</h4>{editingEvent.phases?.map((phase, index) => {
              const update = (next: typeof phase) => setEditingEvent({...editingEvent, phases: editingEvent.phases!.map((p, i) => i === index ? next : p)});
              return <div key={index} className="border rounded-lg p-3 space-y-2">
                <input aria-label="阶段标题" placeholder="阶段标题" className="w-full p-2 border rounded-lg" value={phase.title} onChange={e => update({...phase, title: e.target.value})} />
                <input type="number" aria-label="阶段起始年份" placeholder="起始年份（公元前用负数）" className="w-full p-2 border rounded-lg" value={phase.start_year ?? ''} onChange={e => update({...phase, start_year: parseNumber(e.target.value)})} />
                <input type="number" aria-label="阶段结束年份" placeholder="结束年份（可选）" className="w-full p-2 border rounded-lg" value={phase.end_year ?? ''} onChange={e => update({...phase, end_year: parseNumber(e.target.value)})} />
                <textarea aria-label="阶段说明" placeholder="阶段说明" className="w-full p-2 border rounded-lg" value={phase.description || ''} onChange={e => update({...phase, description: e.target.value})} />
                <button className="text-sm text-rose-700" onClick={() => setEditingEvent({...editingEvent, phases: editingEvent.phases!.filter((_, i) => i !== index)})}>删除阶段</button>
              </div>;
            })}<button className="text-sm text-teal-700" onClick={() => setEditingEvent({...editingEvent, phases: [...editingEvent.phases ?? [], { title: '' }]})}>＋ 添加阶段</button></div>
            <textarea placeholder="概述" value={editingEvent.description || ''} onChange={e => setEditingEvent({...editingEvent, description: e.target.value})} className="w-full p-2 border rounded-lg" rows={3} />
            <input placeholder="标签（用逗号分隔）" value={editingEvent.tags?.join('，') || ''} onChange={e => setEditingEvent({...editingEvent, tags: parseList(e.target.value)})} className="w-full p-2 border rounded-lg" />
            <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="text-sm font-medium text-slate-700">参考资料</div>
              <textarea
                placeholder="标题 | 类型 | 链接 | 备注&#10;例如：维基百科：城濮之战 | encyclopedia | https://zh.wikipedia.org/wiki/城濮之战 | 便于快速定位"
                value={formatReferences(editingEvent.references)}
                onChange={e => setEditingEvent({ ...editingEvent, references: parseReferences(e.target.value) })}
                className="w-full p-2 border rounded-lg bg-white text-sm"
                rows={5}
              />
              <div className="text-xs text-slate-500">
                类型可填：encyclopedia、primary、reference、scholarship、digital。
              </div>
              {editingEvent.references && editingEvent.references.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {editingEvent.references.map((reference, index) => (
                    <span key={`${reference.title}-${index}`} className="px-2 py-1 rounded-md border border-slate-200 bg-white text-xs text-slate-600">
                      {reference.title} · {referenceTypeLabel(reference.reference_type)}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <PhotoIcon className="w-5 h-5 text-slate-400 shrink-0" />
                <input placeholder="图片链接" value={editingEvent.image_url || ''} onChange={e => setEditingEvent({...editingEvent, image_url: e.target.value})} className="w-full p-2 border rounded-lg" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500 px-7">或直接上传</span>
                <input type="file" accept="image/*" onChange={e => handleImageUpload(e, false)} disabled={uploadingImage} className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100 disabled:opacity-50" />
              </div>
            </div>
            
            <div className="space-y-2 border-t border-slate-100 pt-4">
              <div className="flex items-center gap-2 text-slate-500 text-sm font-medium">
                <MapPinIcon className="w-4 h-4" /> 地点信息（可选）
              </div>
              <label className="block text-sm">原始纪年<input className="block w-full p-2 border rounded-lg" value={editingEvent.time_original || ''} onChange={e => setEditingEvent({...editingEvent, time_original: e.target.value})} /></label>
              <label className="block text-sm">今地对应<input className="block w-full p-2 border rounded-lg" value={editingEvent.location_modern_name || ''} onChange={e => setEditingEvent({...editingEvent, location_modern_name: e.target.value})} /></label>
              <label className="block text-sm">定位精度<select aria-label="定位精度" className="block w-full p-2 border rounded-lg" value={editingEvent.location_precision || 'unknown'} onChange={e => setEditingEvent({...editingEvent, location_precision: e.target.value as Event['location_precision']})}><option value="unknown">待核对</option><option value="site">已定位城址／遗址</option><option value="approximate">概略位置</option><option value="region">区域代表点</option></select></label>
              <label className="block text-sm">定位说明<textarea className="block w-full p-2 border rounded-lg" value={editingEvent.location_note || ''} onChange={e => setEditingEvent({...editingEvent, location_note: e.target.value})} /></label>
              <p className="text-xs text-slate-500">经纬度使用 WGS84，须同时填写或同时留空；定位出处在“专题与出处管理”中关联到此事件。</p>
              <input placeholder="地点名称" value={editingEvent.location_name || ''} onChange={e => setEditingEvent({...editingEvent, location_name: e.target.value})} className="w-full p-2 border rounded-lg text-sm" />
              <div className="flex gap-2">
                <input type="number" placeholder="纬度" value={editingEvent.location_lat ?? ''} onChange={e => setEditingEvent({...editingEvent, location_lat: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg text-sm" />
                <input type="number" placeholder="经度" value={editingEvent.location_lng ?? ''} onChange={e => setEditingEvent({...editingEvent, location_lng: parseNumber(e.target.value)})} className="w-full p-2 border rounded-lg text-sm" />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button onClick={() => setEditingEvent(null)} className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-lg">取消</button>
              <button disabled={busy} onClick={() => run(saveEvent)} className="px-4 py-2 bg-orange-500 text-white rounded-lg">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
