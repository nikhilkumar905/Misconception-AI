"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, type Provider } from "@/lib/api";
import { useApi } from "@/lib/use-api";

type EngineState = {
  providers: Provider[] | undefined;
  providersError: string | null;
  retryProviders: () => void;
  provider: string;
  model: string;
  setProvider: (p: string) => void;
  setModel: (m: string) => void;
  current: Provider | undefined;
};

const EngineContext = createContext<EngineState | null>(null);
const STORAGE_KEY = "misconai.engine";

export function EngineProvider({ children }: { children: React.ReactNode }) {
  const { data: providers, error, retry } = useApi("models", api.models);
  const [provider, setProviderState] = useState("groq");
  const [model, setModel] = useState("qwen/qwen3.8-27b");

  // Restore the last choice once the provider list is known (state adjusted during render).
  const [restored, setRestored] = useState(false);
  if (providers && !restored) {
    setRestored(true);
    let saved: { provider?: string; model?: string } | null = null;
    try {
      saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
    } catch {}
    const p = providers.find((x) => x.provider === saved?.provider);
    if (p && p.models.some((m) => m.id === saved?.model)) {
      setProviderState(p.provider);
      setModel(saved!.model!);
    } else {
      const firstWithKey = providers.find((x) => x.has_key) ?? providers[0];
      setProviderState(firstWithKey.provider);
      setModel(firstWithKey.models[0].id);
    }
  }

  useEffect(() => {
    if (!restored) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ provider, model }));
    } catch {}
  }, [restored, provider, model]);

  const value = useMemo<EngineState>(() => {
    const current = providers?.find((p) => p.provider === provider);
    return {
      providers,
      providersError: error,
      retryProviders: retry,
      provider,
      model,
      current,
      setModel,
      setProvider: (p) => {
        setProviderState(p);
        const next = providers?.find((x) => x.provider === p);
        if (next) setModel(next.models[0].id);
      },
    };
  }, [providers, error, retry, provider, model]);

  return <EngineContext.Provider value={value}>{children}</EngineContext.Provider>;
}

export function useEngine() {
  const ctx = useContext(EngineContext);
  if (!ctx) throw new Error("useEngine must be used inside <EngineProvider>");
  return ctx;
}
