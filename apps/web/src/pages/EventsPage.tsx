import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AcademicCapIcon } from '@heroicons/react/24/outline';
import type { Event } from '@histree/shared-types';

export const EventsPage: React.FC = () => {
  const { t } = useTranslation();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1';

    fetch(`${apiBase}/event`)
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-orange-100 rounded-xl text-orange-600">
          <AcademicCapIcon className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">{t('Events Directory')}</h1>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">{t('loading')}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map(event => (
            <Link 
              key={event.id} 
              to={`/graph/${event.id}`}
              className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-orange-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-orange-50 text-orange-500 rounded-lg group-hover:bg-orange-500 group-hover:text-white transition-colors">
                  <AcademicCapIcon className="w-5 h-5" />
                </div>
                <div className="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-full border border-slate-200">
                  {event.start_year || t('Unknown Year')}
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-orange-600 transition-colors">{event.title}</h3>
              {event.description && (
                <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed mb-4">{event.description}</p>
              )}
              {event.dynasty && (
                <div className="inline-block px-2.5 py-1 bg-slate-50 text-slate-500 text-xs font-medium rounded-md border border-slate-100">
                  {event.dynasty}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
