import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { SparklesIcon, UserIcon, AcademicCapIcon } from '@heroicons/react/24/outline';

export const ExplorePage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center py-12 md:py-24 text-center max-w-2xl mx-auto space-y-12">
      <div className="space-y-6">
        <div className="inline-flex items-center justify-center p-4 bg-sky-100 rounded-3xl mb-4">
          <SparklesIcon className="w-12 h-12 text-sky-500" />
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold text-slate-800 tracking-tight">
          {t('title', 'Histree')}
        </h1>
        <p className="text-xl text-slate-500 max-w-lg mx-auto">
          {t('subtitle')}
        </p>
      </div>

      <div className="w-full bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-700 mb-6">{t('Recommended Exploration')}</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3 text-left">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <UserIcon className="w-4 h-4" /> {t('People')}
            </h3>
            <div className="flex flex-wrap gap-2">
              <Link to="/graph/00000000-0000-0000-0000-000000000001" className="px-4 py-2 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded-xl text-slate-700 font-medium transition-colors">曹操</Link>
              <Link to="/graph/00000000-0000-0000-0000-000000000002" className="px-4 py-2 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded-xl text-slate-700 font-medium transition-colors">刘备</Link>
            </div>
          </div>
          
          <div className="space-y-3 text-left">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <AcademicCapIcon className="w-4 h-4" /> {t('Events')}
            </h3>
            <div className="flex flex-wrap gap-2">
              <Link to="/graph/00000000-0000-0000-0000-000000000004" className="px-4 py-2 bg-slate-50 hover:bg-orange-50 border border-slate-200 hover:border-orange-200 rounded-xl text-slate-700 font-medium transition-colors">官渡之战</Link>
              <Link to="/graph/00000000-0000-0000-0000-000000000005" className="px-4 py-2 bg-slate-50 hover:bg-orange-50 border border-slate-200 hover:border-orange-200 rounded-xl text-slate-700 font-medium transition-colors">赤壁之战</Link>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-100">
          <Link to="/graph/00000000-0000-0000-0000-000000000005" className="inline-flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-colors shadow-sm">
            <SparklesIcon className="w-5 h-5" />
            {t('Random Explore')}
          </Link>
        </div>
      </div>
    </div>
  );
};
