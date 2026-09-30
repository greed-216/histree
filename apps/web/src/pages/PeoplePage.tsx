import React from 'react';
import { Link } from 'react-router-dom';
import { UserIcon } from '@heroicons/react/24/outline';
import type { Person, PageResult } from '@histree/shared-types';
import { useInfiniteResource } from '../hooks/useInfiniteResource';
import { InfiniteScroll } from '../components/InfiniteScroll';
import { LoadState } from '../components/Reading';
import { primaryReference } from '../lib/content';

export const PeoplePage: React.FC = () => {
  const result=useInfiniteResource<PageResult<Person>>("/catalog/person");
  const people=result.data?.items??[];
  const loading=result.loading;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-teal-100 rounded-xl text-teal-600">
          <UserIcon className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-serif text-stone-800 tracking-tight">历史人物</h1>
      </div>

      <Link to="/search" className="inline-block text-teal-700 text-sm">搜索姓名、别名与标签 →</Link>
      <LoadState {...result}/>
      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">加载中...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {people.map(person => (
            <Link 
              key={person.id} 
              to={`/people/${person.id}`}
              className="reading-card directory-card group flex items-start gap-4"
            >
              <div className="w-14 h-14 rounded-full bg-teal-50 text-teal-500 flex items-center justify-center shrink-0 font-bold text-lg overflow-hidden border border-slate-200 group-hover:border-teal-300 transition-colors">
                {person.image_url ? (
                  <img src={person.image_url} alt={person.name} className="w-full h-full object-cover" />
                ) : (
                  person.name.charAt(0)
                )}
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800 mb-1 group-hover:text-teal-600 transition-colors">{person.name}</h3>
                <div className="text-sm text-slate-500 mb-2">
                  {person.era || '时代待补充'}
                  {person.faction ? ` · ${person.faction}` : ''}
                  {person.native_place ? ` · ${person.native_place}` : ''}
                </div>
                {person.description && (
                  <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">{person.description}</p>
                )}
                {person.biography && (
                  <p className="text-sm text-slate-500 line-clamp-3 leading-relaxed mt-2">{person.biography}</p>
                )}
                {person.tags && person.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {person.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-500 text-xs border border-slate-200">{tag}</span>
                    ))}
                  </div>
                )}
                {primaryReference(person.references) && (
                  <div className="mt-3 text-xs text-teal-700 line-clamp-1">
                    参考：{primaryReference(person.references)?.title}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
      <InfiniteScroll {...result} count={people.length} label="人物"/>
    </div>
  );
};
