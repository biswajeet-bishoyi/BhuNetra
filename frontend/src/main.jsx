import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

import { LangProvider } from './i18n'

// Support remote backend (e.g. Render / Vercel / Railway) when frontend is hosted statically
const rawBackendUrl =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  (typeof window !== 'undefined' && window.__BHUNETRA_API_URL__) ||
  '';
const API_BASE_URL = rawBackendUrl ? rawBackendUrl.replace(/\/+$/, '') : '';

if (API_BASE_URL && typeof window !== 'undefined') {
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    if (typeof input === 'string') {
      if (input.startsWith('/api/') || input.startsWith('/static-data/')) {
        return originalFetch(`${API_BASE_URL}${input}`, init);
      }
    } else if (input instanceof Request && input.url) {
      try {
        const parsed = new URL(input.url, window.location.origin);
        if (parsed.pathname.startsWith('/api/') || parsed.pathname.startsWith('/static-data/')) {
          const newUrl = `${API_BASE_URL}${parsed.pathname}${parsed.search}`;
          return originalFetch(new Request(newUrl, input), init);
        }
      } catch (e) {
        // Fallback to original
      }
    }
    return originalFetch(input, init);
  };
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LangProvider>
      <App />
    </LangProvider>
  </React.StrictMode>,
)
