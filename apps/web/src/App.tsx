import { useEffect, useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supabase } from './supabaseClient';
import { AuthModal } from './AuthModal';
import { UserIcon, ArrowRightOnRectangleIcon, AcademicCapIcon, MapIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { getCurrentUserRole } from './lib/api';
import { ExplorePage } from './pages/ExplorePage';
import { GraphPage } from './pages/GraphPage';
import { PeoplePage } from './pages/PeoplePage';
import { EventsPage } from './pages/EventsPage';
import { AdminPage } from './pages/AdminPage';
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';

function App() {
  const { t, i18n } = useTranslation();
  const [session, setSession] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isAuthModalOpen, setAuthModalOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    const refreshAuthState = async (nextSession: any) => {
      setSession(nextSession);
      if (!nextSession) {
        setIsAdmin(false);
        return;
      }

      try {
        const role = await getCurrentUserRole();
        if (!cancelled) {
          setIsAdmin(role === 'admin');
        }
      } catch (err) {
        console.error('Failed to resolve current user role:', err);
        if (!cancelled) {
          setIsAdmin(false);
        }
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      refreshAuthState(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      refreshAuthState(session);
      if (session) {
        setAuthModalOpen(false);
      }
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  const navLinkClass = (path: string) => 
    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      location.pathname === path || (path !== '/' && location.pathname.startsWith(path))
        ? 'bg-slate-800 text-white shadow-sm'
        : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'
    }`;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center shadow-sm">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-800 tracking-tight">Histree</span>
            </Link>
            
            <nav className="hidden md:flex items-center gap-2">
              <Link to="/" className={navLinkClass('/')}>
                <MapIcon className="w-4 h-4" />
                {t('Explore')}
              </Link>
              <Link to="/people" className={navLinkClass('/people')}>
                <UserIcon className="w-4 h-4" />
                {t('People')}
              </Link>
              <Link to="/events" className={navLinkClass('/events')}>
                <AcademicCapIcon className="w-4 h-4" />
                {t('Events')}
              </Link>
              {isAdmin && (
                <Link to="/admin" className={navLinkClass('/admin')}>
                  <AdjustmentsHorizontalIcon className="w-4 h-4" />
                  {t('Admin')}
                </Link>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {/* Auth Section */}
            {session ? (
              <div className="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                <div className="flex items-center gap-1.5 text-sm font-medium text-emerald-600">
                  <UserIcon className="w-4 h-4" />
                  <span className="hidden sm:inline">{isAdmin ? t('adminStatus') : t('userStatus')}</span>
                </div>
                <div className="w-px h-4 bg-slate-300"></div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 text-sm text-slate-500 hover:text-rose-500 transition-colors"
                  title={t('logout')}
                >
                  <ArrowRightOnRectangleIcon className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm font-medium transition-colors"
              >
                <UserIcon className="w-4 h-4" />
                <span className="hidden sm:inline">{t('loginAdmin')}</span>
              </button>
            )}

            {/* Language Toggle */}
            <div className="flex bg-slate-200/60 p-1 rounded-lg">
              <button 
                onClick={() => i18n.changeLanguage('zh')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  i18n.language === 'zh' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                中
              </button>
              <button 
                onClick={() => i18n.changeLanguage('en')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  i18n.language === 'en' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                EN
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 md:px-8 py-6 md:py-8">
        <Routes>
          <Route path="/" element={<ExplorePage />} />
          <Route path="/graph/:id" element={<GraphPage />} />
          <Route path="/people" element={<PeoplePage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>

      <AuthModal isOpen={isAuthModalOpen} onClose={() => setAuthModalOpen(false)} />
      
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-slate-400 text-sm mt-auto">
        © {new Date().getFullYear()} Histree MVP. Exploring history through graphs.
      </footer>
    </div>
  );
}

export default App;
