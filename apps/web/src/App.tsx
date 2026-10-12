import { SourcePage, EvidencePage } from './pages/SourcesPage';
import { MAPS_ENABLED } from './lib/features';
import { lazy, Suspense } from 'react';
import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { UserIcon, AcademicCapIcon, MapIcon } from '@heroicons/react/24/outline';
import { useScrollRestoration } from './hooks/useScrollRestoration';
const MapEditorPage = lazy(() => import('./pages/MapEditorPage').then(m => ({ default: m.MapEditorPage })));
const AnnotationEditorPage = lazy(() => import('./pages/AnnotationEditorPage').then(m => ({ default: m.AnnotationEditorPage })));
const VisualExplorePage = lazy(() => import('./pages/VisualExplorePage').then(m => ({ default: m.VisualExplorePage })));
import { GuidePage, GuideIndexPage, FiveDynastiesOverviewPage, LegacyZhouGuideRedirect } from './pages/GuidePage';
import { HistoryScrollPage } from './pages/HistoryScrollPage';
import { ExplorePage } from './pages/ExplorePage';
const TimelinePage = lazy(() => import('./pages/TimelinePage').then(m => ({ default: m.TimelinePage })));
const GraphPage = lazy(() => import('./pages/GraphPage').then(m => ({ default: m.GraphPage })));
import { PeoplePage } from './pages/PeoplePage';
import { EventsPage } from './pages/EventsPage';
import { TopicPage } from './pages/TopicPage';
import { EntryPage } from './pages/EntryPage';
import { SearchPage } from './pages/SearchPage';
const AskPage = lazy(() => import('./pages/AskPage').then(m => ({ default: m.AskPage })));

function App() {
  const location = useLocation();
  useScrollRestoration();

  const navLinkClass = (path: string) => 
    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      location.pathname === path || (path !== '/' && location.pathname.startsWith(path))
        ? 'nav-active'
        : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
    }`;

  return (
    <div className="site-shell min-h-screen flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="site-header sticky top-0 z-40">
        <div className="site-header-inner mx-auto px-4 md:px-8 min-h-16 py-3 flex flex-wrap gap-3 items-center justify-between">
          <div className="contents md:flex md:items-center md:gap-4">
            <Link to="/" className="brand-link" aria-label="Histree 历史之树首页">
              <img className="brand-logo" src={`${import.meta.env.BASE_URL}brand/histree-logo.png`} alt="Histree" width="2172" height="724" />
            </Link>
            
            <nav aria-label="主导航" className="order-3 w-full md:order-none md:w-auto flex flex-wrap items-center gap-1">
              <Link to="/" className={navLinkClass('/')}>
                <MapIcon className="w-4 h-4" />
                探索
              </Link>
              <Link to="/learn" className={navLinkClass('/learn')}>导读</Link>
              <Link to="/people" className={navLinkClass('/people')}>
                <UserIcon className="w-4 h-4" />
                人物
              </Link>
              <Link to="/events" className={navLinkClass('/events')}>
                <AcademicCapIcon className="w-4 h-4" />
                事件
              </Link>
              <Link to="/graph" className={navLinkClass('/graph')}>图谱</Link>
              {MAPS_ENABLED && <Link to="/map" className={navLinkClass('/map')}>地图</Link>}
              <Link to="/search" className={navLinkClass('/search')}>搜索</Link>
              <Link to="/ask" className={navLinkClass('/ask')}>问史料</Link>
            </nav>
          </div>

        </div>
      </header>

      {/* Main Content */}
      <main className={`site-main flex-1 w-full mx-auto px-4 md:px-8 py-6 md:py-8 ${location.pathname.startsWith('/graph')?'site-main-graph':''}`}>
        <Suspense fallback={<p className="py-12 text-center">加载中…</p>}><Routes>
          <Route path="/sources/:id" element={<SourcePage />} />
          <Route path="/evidence/:subject/:id" element={<EvidencePage />} />
          <Route path="/learn" element={<GuideIndexPage />} />
          <Route path="/learn/five-dynasties" element={<FiveDynastiesOverviewPage />} />
          <Route path="/learn/five-dynasties/later-zhou" element={<GuidePage />} />
          <Route path="/learn/five-dynasties/later-zhou/:chapter" element={<GuidePage key={location.pathname} />} />
          <Route path="/learn/later-zhou" element={<LegacyZhouGuideRedirect />} />
          <Route path="/learn/later-zhou/:chapter" element={<LegacyZhouGuideRedirect />} />
          <Route path="/topics/:slug" element={<TopicPage />} />
          <Route path="/people/:id" element={<EntryPage />} />
          <Route path="/events/:id" element={<EntryPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/ask" element={<AskPage key={location.search} />} />
          <Route path="/" element={<ExplorePage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/timeline/scroll" element={<HistoryScrollPage />} />
          <Route path="/graph" element={<VisualExplorePage mode="graph" />} />
          <Route path="/map" element={MAPS_ENABLED ? <VisualExplorePage mode="map" /> : <Navigate to="/graph" replace />} />
          <Route path="/map/edit" element={MAPS_ENABLED ? <MapEditorPage /> : <Navigate to="/graph" replace />} />
          <Route path="/map/annotations" element={MAPS_ENABLED ? <AnnotationEditorPage /> : <Navigate to="/graph" replace />} />
          <Route path="/graph/:id" element={<GraphPage />} />
          <Route path="/people" element={<PeoplePage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="*" element={<div className="py-12 text-center">页面不存在。<Link className="text-teal-700" to="/">返回专题探索</Link></div>} />
        </Routes></Suspense>
      </main>


      
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-slate-400 text-sm mt-auto">
        © {new Date().getFullYear()} Histree 历史之树
      </footer>
    </div>
  );
}

export default App;
