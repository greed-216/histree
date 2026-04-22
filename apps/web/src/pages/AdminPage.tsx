import React, { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';
import { useTranslation } from 'react-i18next';
import { PlusIcon, TrashIcon, PencilIcon, PhotoIcon, MapPinIcon } from '@heroicons/react/24/outline';
import type { Person, Event } from '@histree/shared-types';
import { apiFetch } from '../lib/api';

export const AdminPage: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'people' | 'events'>('people');
  const [people, setPeople] = useState<Person[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  // Edit states
  const [editingPerson, setEditingPerson] = useState<Partial<Person> | null>(null);
  const [editingEvent, setEditingEvent] = useState<Partial<Event> | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    checkAdminAndLoadData();
  }, []);

  const checkAdminAndLoadData = async () => {
    setLoading(true);
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      setLoading(false);
      return;
    }

    const { data: roles } = await supabase.from('user_roles').select('role').eq('user_id', session.user.id).single();
    if (roles?.role === 'admin') {
      setIsAdmin(true);
      fetchData();
    }
    setLoading(false);
  };

  const fetchData = async () => {
    const [pData, eData] = await Promise.all([
      apiFetch<Person[]>('/people'),
      apiFetch<Event[]>('/event'),
    ]);
    setPeople(pData);
    setEvents(eData);
  };

  const savePerson = async () => {
    if (!editingPerson?.name) return;

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
    fetchData();
  };

  const deletePerson = async (id: string) => {
    if (!confirm(t('Are you sure you want to delete this person?'))) return;
    await apiFetch<{ id: string }>(`/people/${id}`, {
      method: 'DELETE',
      auth: true,
    });
    fetchData();
  };

  const saveEvent = async () => {
    if (!editingEvent?.title) return;

    if (editingEvent.id) {
      await apiFetch<Event>(`/event/${editingEvent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingEvent),
        auth: true,
      });
    } else {
      await apiFetch<Event>('/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingEvent),
        auth: true,
      });
    }
    setEditingEvent(null);
    fetchData();
  };

  const deleteEvent = async (id: string) => {
    if (!confirm(t('Are you sure you want to delete this event?'))) return;
    await apiFetch<{ id: string }>(`/event/${id}`, {
      method: 'DELETE',
      auth: true,
    });
    fetchData();
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
      alert(t('Failed to upload image.'));
    } finally {
      setUploadingImage(false);
    }
  };

  if (loading) return <div className="p-12 text-center text-slate-500">{t('loading')}</div>;
  if (!isAdmin) return <div className="p-12 text-center text-rose-500 font-bold">{t('Access Denied. Admins only.')}</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">{t('Data Management')}</h1>
        <div className="flex gap-2 bg-slate-200/50 p-1 rounded-xl">
          <button 
            onClick={() => setActiveTab('people')} 
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'people' ? 'bg-white shadow-sm text-sky-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            {t('People')}
          </button>
          <button 
            onClick={() => setActiveTab('events')} 
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'events' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500 hover:text-slate-700'}`}
          >
            {t('Events')}
          </button>
        </div>
      </div>

      {activeTab === 'people' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h2 className="font-semibold text-slate-700">{t('Manage People')}</h2>
            <button onClick={() => setEditingPerson({})} className="flex items-center gap-1 bg-sky-500 hover:bg-sky-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
              <PlusIcon className="w-4 h-4" /> {t('Add Person')}
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-medium">
                <tr>
                  <th className="px-6 py-3">{t('Name')}</th>
                  <th className="px-6 py-3">{t('Era')}</th>
                  <th className="px-6 py-3">{t('Image')}</th>
                  <th className="px-6 py-3 text-right">{t('Actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {people.map(p => (
                  <tr key={p.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-semibold text-slate-800">{p.name}</td>
                    <td className="px-6 py-4">{p.era}</td>
                    <td className="px-6 py-4">
                      {p.image_url ? <img src={p.image_url} className="w-8 h-8 rounded-full object-cover border border-slate-200" /> : '-'}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => setEditingPerson(p)} className="p-1.5 text-sky-500 hover:bg-sky-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                      <button onClick={() => deletePerson(p.id)} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
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
            <h2 className="font-semibold text-slate-700">{t('Manage Events')}</h2>
            <button onClick={() => setEditingEvent({})} className="flex items-center gap-1 bg-orange-500 hover:bg-orange-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
              <PlusIcon className="w-4 h-4" /> {t('Add Event')}
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-medium">
                <tr>
                  <th className="px-6 py-3">{t('Title')}</th>
                  <th className="px-6 py-3">{t('Year')}</th>
                  <th className="px-6 py-3">{t('Location')}</th>
                  <th className="px-6 py-3 text-right">{t('Actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {events.map(e => (
                  <tr key={e.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-semibold text-slate-800">{e.title}</td>
                    <td className="px-6 py-4">{e.start_year}</td>
                    <td className="px-6 py-4">{e.location_name || '-'}</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => setEditingEvent(e)} className="p-1.5 text-orange-500 hover:bg-orange-50 rounded-md transition-colors"><PencilIcon className="w-4 h-4" /></button>
                      <button onClick={() => deleteEvent(e.id)} className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-md transition-colors"><TrashIcon className="w-4 h-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Edit Person Modal */}
      {editingPerson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold">{editingPerson.id ? t('Edit Person') : t('Add Person')}</h3>
            <input placeholder={t('Name')} value={editingPerson.name || ''} onChange={e => setEditingPerson({...editingPerson, name: e.target.value})} className="w-full p-2 border rounded-lg" />
            <input placeholder={t('Era')} value={editingPerson.era || ''} onChange={e => setEditingPerson({...editingPerson, era: e.target.value})} className="w-full p-2 border rounded-lg" />
            <textarea placeholder={t('Description')} value={editingPerson.description || ''} onChange={e => setEditingPerson({...editingPerson, description: e.target.value})} className="w-full p-2 border rounded-lg" rows={3} />
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <PhotoIcon className="w-5 h-5 text-slate-400" />
                <input placeholder={t('Image URL')} value={editingPerson.image_url || ''} onChange={e => setEditingPerson({...editingPerson, image_url: e.target.value})} className="w-full p-2 border rounded-lg" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500 px-7">{t('or upload')}</span>
                <input type="file" accept="image/*" onChange={e => handleImageUpload(e, true)} disabled={uploadingImage} className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 disabled:opacity-50" />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <button onClick={() => setEditingPerson(null)} className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-lg">{t('Cancel')}</button>
              <button onClick={savePerson} className="px-4 py-2 bg-sky-500 text-white rounded-lg">{t('Save')}</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Event Modal */}
      {editingEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold">{editingEvent.id ? t('Edit Event') : t('Add Event')}</h3>
            <input placeholder={t('Title')} value={editingEvent.title || ''} onChange={e => setEditingEvent({...editingEvent, title: e.target.value})} className="w-full p-2 border rounded-lg" />
            <div className="flex gap-2">
              <input type="number" placeholder={t('Start Year')} value={editingEvent.start_year || ''} onChange={e => setEditingEvent({...editingEvent, start_year: Number(e.target.value)})} className="w-full p-2 border rounded-lg" />
              <input placeholder={t('Dynasty')} value={editingEvent.dynasty || ''} onChange={e => setEditingEvent({...editingEvent, dynasty: e.target.value})} className="w-full p-2 border rounded-lg" />
            </div>
            <textarea placeholder={t('Description')} value={editingEvent.description || ''} onChange={e => setEditingEvent({...editingEvent, description: e.target.value})} className="w-full p-2 border rounded-lg" rows={3} />
            
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <PhotoIcon className="w-5 h-5 text-slate-400 shrink-0" />
                <input placeholder={t('Image URL')} value={editingEvent.image_url || ''} onChange={e => setEditingEvent({...editingEvent, image_url: e.target.value})} className="w-full p-2 border rounded-lg" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500 px-7">{t('or upload')}</span>
                <input type="file" accept="image/*" onChange={e => handleImageUpload(e, false)} disabled={uploadingImage} className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100 disabled:opacity-50" />
              </div>
            </div>
            
            <div className="space-y-2 border-t border-slate-100 pt-4">
              <div className="flex items-center gap-2 text-slate-500 text-sm font-medium">
                <MapPinIcon className="w-4 h-4" /> {t('Location Data (Optional)')}
              </div>
              <input placeholder={t('Location Name (e.g. Chibi)')} value={editingEvent.location_name || ''} onChange={e => setEditingEvent({...editingEvent, location_name: e.target.value})} className="w-full p-2 border rounded-lg text-sm" />
              <div className="flex gap-2">
                <input type="number" placeholder={t('Latitude')} value={editingEvent.location_lat || ''} onChange={e => setEditingEvent({...editingEvent, location_lat: parseFloat(e.target.value)})} className="w-full p-2 border rounded-lg text-sm" />
                <input type="number" placeholder={t('Longitude')} value={editingEvent.location_lng || ''} onChange={e => setEditingEvent({...editingEvent, location_lng: parseFloat(e.target.value)})} className="w-full p-2 border rounded-lg text-sm" />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button onClick={() => setEditingEvent(null)} className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-lg">{t('Cancel')}</button>
              <button onClick={saveEvent} className="px-4 py-2 bg-orange-500 text-white rounded-lg">{t('Save')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
