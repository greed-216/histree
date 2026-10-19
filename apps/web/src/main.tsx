import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, '') || '/'}>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

// Load the local-only diagnostic controls only for an explicitly requested test URL.
if (new URLSearchParams(window.location.search).get('scroll-debug') === '1') {
  const script = document.createElement('script')
  script.src = `${import.meta.env.BASE_URL}diagnostics/scroll-runtime.js`
  document.body.appendChild(script)
}
