import React from 'react';
import { Link } from 'react-router-dom';
import { AcademicCapIcon } from '@heroicons/react/24/outline';
import type { Event, PageResult } from '@histree/shared-types';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { LoadState } from '../components/Reading';
import { formatDisplayRange, primaryReference } from '../lib/content';

export const EventsPage: React.FC = () => {
  const result=useInfiniteResource<PageResult<Event>>("/catalog/event");
  const events=result.data?.items??[];
  const loading=result.loading;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-orange-100 rounded-xl text-orange-600">
          <AcademicCapIcon className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-serif text-stone-800 tracking-tight">历史事件</h1>
      </div>

      <Link to="/search" className="inline-block text-teal-700 text-sm">搜索姓名、别名与标签 →</Link>
      <LoadState {...result}/>
      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">加载中...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map(event => (
            <Link 
              key={event.id} 
              to={`/events/${event.id}`}
              className="reading-card directory-card group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 bg-orange-50 text-orange-500 rounded-lg group-hover:bg-orange-500 group-hover:text-white transition-colors">
                  <AcademicCapIcon className="w-5 h-5" />
                </div>
                <div className="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-full border border-slate-200">
                  {formatDisplayRange(event.start_year, event.end_year)}
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-orange-600 transition-colors">{event.title}</h3>
              {event.description && (
                <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed mb-4">{event.description}</p>
              )}
              <div className="flex flex-wrap gap-2">
                {event.dynasty && (
                  <div className="inline-block px-2.5 py-1 bg-slate-50 text-slate-500 text-xs font-medium rounded-md border border-slate-100">
                    {event.dynasty}
                  </div>
                )}
                {event.location_name && (
                  <div className="inline-block px-2.5 py-1 bg-slate-50 text-slate-500 text-xs font-medium rounded-md border border-slate-100">
                    {event.location_name}
                  </div>
                )}
                {event.tags?.slice(0, 2).map((tag) => (
                  <div key={tag} className="inline-block px-2.5 py-1 bg-orange-50 text-orange-600 text-xs font-medium rounded-md border border-orange-100">
                    {tag}
                  </div>
                ))}
              </div>
              {primaryReference(event.references) && (
                <div className="mt-4 text-xs text-orange-700 line-clamp-1">
                  参考：{primaryReference(event.references)?.title}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
      <InfiniteScroll {...result} count={events.length} label="事件"/>
    </div>
  );
};
