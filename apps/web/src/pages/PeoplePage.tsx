import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { UserIcon } from '@heroicons/react/24/outline';
import type { Person } from '@histree/shared-types';

export const PeoplePage: React.FC = () => {
  const { t } = useTranslation();
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(import.meta.env.VITE_API_URL?.replace('/graph/person/00000000-0000-0000-0000-000000000001', '/people') || 'http://localhost:3000/api/v1/people')
      .then(res => res.json())
      .then(data => {
        setPeople(data);
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
        <div className="p-3 bg-sky-100 rounded-xl text-sky-600">
          <UserIcon className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">{t('People Directory')}</h1>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">{t('loading')}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {people.map(person => (
            <Link 
              key={person.id} 
              to={`/graph/${person.id}`}
              className="bg-white p-6 rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-md transition-all group flex items-start gap-4"
            >
              <div className="w-12 h-12 rounded-full bg-sky-50 text-sky-500 flex items-center justify-center shrink-0 font-bold text-lg group-hover:bg-sky-500 group-hover:text-white transition-colors">
                {person.name.charAt(0)}
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800 mb-1 group-hover:text-sky-600 transition-colors">{person.name}</h3>
                <div className="text-sm text-slate-500 mb-2">{person.era}</div>
                {person.description && (
                  <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">{person.description}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
