"use client";

import { useEffect, useState } from "react";

const cache = new Map<string, unknown>();

/** Fetch read-only API data once per session and share it across pages. */
export function useApi<T>(key: string, fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | undefined>(() => cache.get(key) as T | undefined);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (cache.has(key)) return;
    let cancelled = false;
    fetcher()
      .then((d) => {
        cache.set(key, d);
        if (!cancelled) {
          setData(d);
          setError(null);
        }
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt]);

  return { data, error, retry: () => setAttempt((a) => a + 1) };
}
