import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { SparklesIcon, UserIcon, AcademicCapIcon } from '@heroicons/react/24/outline';
import type { Event, Person } from '@histree/shared-types';
import { apiFetch } from '../lib/api';
import { formatDisplayRange, primaryReference } from '../lib/content';

export const ExplorePage: React.FC = () => {
  const [people, setPeople] = useState<Person[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<Person[]>('/people'),
      apiFetch<Event[]>('/event'),
    ])
      .then(([peopleData, eventsData]) => {
        setPeople(peopleData);
        setEvents(eventsData);
      })
      .catch((err) => {
        console.error('Failed to load exploration data:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const recommendedPeople = people.slice(0, 4);
  const recommendedEvents = events.slice(0, 4);
  const featuredNode = useMemo(() => {
    return events.find((event) => event.impact_level === 5) ?? events[0] ?? people[0];
  }, [events, people]);

  return (
    <div className="flex flex-col items-center justify-center py-12 md:py-24 text-center max-w-2xl mx-auto space-y-12">
      <div className="space-y-6">
        <div className="inline-flex items-center justify-center p-4 bg-sky-100 rounded-3xl mb-4">
          <SparklesIcon className="w-12 h-12 text-sky-500" />
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold text-slate-800 tracking-tight">
          Histree 历史之树
        </h1>
        <p className="text-xl text-slate-500 max-w-lg mx-auto">
          以人物、事件、关系和出处为核心，逐步搭建面向中国史的知识图谱平台。
        </p>
      </div>

      <div className="w-full bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-700 mb-6">推荐探索</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3 text-left">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <UserIcon className="w-4 h-4" /> 人物
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {loading && <span className="text-sm text-slate-400">加载中...</span>}
              {!loading && recommendedPeople.length === 0 && <span className="text-sm text-slate-400">暂无人物数据</span>}
              {recommendedPeople.map((person) => (
                <Link key={person.id} to={`/graph/${person.id}`} className="flex items-start gap-3 px-3 py-3 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded-xl text-slate-700 transition-colors">
                  {person.image_url ? (
                    <img src={person.image_url} alt={person.name} className="w-10 h-10 rounded-full object-cover border border-slate-200 shrink-0" />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-semibold shrink-0">
                      {person.name.charAt(0)}
                    </div>
                  )}
                  <div className="min-w-0">
                    <div className="font-semibold text-slate-800">{person.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{person.era || '时代待补充'}{person.faction ? ` · ${person.faction}` : ''}</div>
                    {primaryReference(person.references) && (
                      <div className="text-xs text-sky-700 mt-1 line-clamp-1">
                        参考：{primaryReference(person.references)?.title}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
          
          <div className="space-y-3 text-left">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <AcademicCapIcon className="w-4 h-4" /> 事件
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {loading && <span className="text-sm text-slate-400">加载中...</span>}
              {!loading && recommendedEvents.length === 0 && <span className="text-sm text-slate-400">暂无事件数据</span>}
              {recommendedEvents.map((event) => (
                <Link key={event.id} to={`/graph/${event.id}`} className="block px-4 py-3 bg-slate-50 hover:bg-orange-50 border border-slate-200 hover:border-orange-200 rounded-xl text-slate-700 transition-colors">
                  <div className="font-semibold text-slate-800">{event.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{formatDisplayRange(event.start_year, event.end_year)}{event.dynasty ? ` · ${event.dynasty}` : ''}</div>
                  {primaryReference(event.references) && (
                    <div className="text-xs text-orange-700 mt-1 line-clamp-1">
                      参考：{primaryReference(event.references)?.title}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {featuredNode && (
          <div className="mt-8 pt-8 border-t border-slate-100">
            <Link to={`/graph/${featuredNode.id}`} className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-colors shadow-sm">
              <SparklesIcon className="w-5 h-5" />
              开始探索
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
