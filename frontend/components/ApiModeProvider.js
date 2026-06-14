'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { fetchStats } from '@/lib/api';

// Probes the backend once on load and shares the result with the whole app:
//   ready  - the probe has finished
//   live   - the API is reachable (otherwise the app runs in demo mode)
//   stats  - payload from /api/stats when live (records, cities, ...)
const ApiModeContext = createContext({ ready: false, live: false, stats: null });

export function ApiModeProvider({ children }) {
  const [state, setState] = useState({ ready: false, live: false, stats: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const stats = await fetchStats();
      if (!cancelled) setState({ ready: true, live: !!stats, stats });
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return <ApiModeContext.Provider value={state}>{children}</ApiModeContext.Provider>;
}

export const useApiMode = () => useContext(ApiModeContext);
