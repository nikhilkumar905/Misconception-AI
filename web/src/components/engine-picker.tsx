"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, Cpu, KeyRound, Sparkles } from "lucide-react";
import { useEngine } from "./engine-context";
import { cx } from "./ui";

export function EnginePicker() {
  const { providers, providersError, provider, model, setProvider, setModel, current } = useEngine();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  const modelLabel = current?.models.find((m) => m.id === model)?.label ?? model;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="dialog"
        className="flex items-center gap-2.5 rounded-lg bg-white/8 px-3 py-1.5 text-left ring-1 ring-white/15 transition-colors hover:bg-white/12 focus-visible:outline-2 focus-visible:outline-accent-400"
      >
        <Cpu className="size-4 text-accent-400" aria-hidden />
        <span className="hidden leading-tight sm:block">
          <span className="block text-[11px] text-brand-200">{providersError ? "Engine" : current?.label ?? "Loading…"}</span>
          <span className="block max-w-36 truncate text-sm font-medium">{providersError ? "API offline" : modelLabel}</span>
        </span>
        <span
          className={cx(
            "size-2 rounded-full",
            providersError ? "bg-bad-200" : current?.has_key ? "bg-emerald-400" : "bg-amber-400",
          )}
          aria-hidden
        />
        <ChevronDown className="size-4 text-brand-200" aria-hidden />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Choose model"
          className="absolute right-0 z-50 mt-2 w-[min(20rem,calc(100vw-2rem))] overflow-hidden rounded-xl border border-line bg-surface text-ink shadow-xl"
        >
          <div className="border-b border-line bg-canvas px-4 py-3">
            <p className="text-sm font-semibold text-night-900">Analysis engine</p>
            <p className="text-xs text-subtle">Used by the mining lab and the concept tutor.</p>
          </div>

          {providersError ? (
            <p className="px-4 py-4 text-sm text-bad-700">{providersError}</p>
          ) : (
            <>
              <div className="flex gap-1 p-2" role="tablist" aria-label="Provider">
                {providers?.map((p) => (
                  <button
                    key={p.provider}
                    role="tab"
                    aria-selected={p.provider === provider}
                    onClick={() => setProvider(p.provider)}
                    className={cx(
                      "flex-1 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                      p.provider === provider ? "bg-night-900 text-white" : "text-muted hover:bg-slate-100",
                    )}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              {current && !current.has_key && (
                <p className="mx-2 mb-2 flex items-start gap-2 rounded-lg bg-warn-50 px-3 py-2 text-xs text-warn-700">
                  <KeyRound className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                  Set <code className="font-mono">{current.key_env}</code> in <code className="font-mono">.env</code> and restart the API to use {current.label}.
                </p>
              )}

              <ul className="max-h-72 overflow-y-auto px-2 pb-2">
                {current?.models.map((m) => (
                  <li key={m.id}>
                    <button
                      onClick={() => {
                        setModel(m.id);
                        setOpen(false);
                      }}
                      className={cx(
                        "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                        m.id === model ? "bg-brand-50 text-brand-700" : "hover:bg-slate-50",
                      )}
                    >
                      <span className="flex-1">
                        <span className="block font-medium">{m.label}</span>
                        <span className="block font-mono text-[11px] text-subtle">{m.id}</span>
                      </span>
                      {m.reasoning && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-accent-100 px-2 py-0.5 text-[11px] font-medium text-accent-700">
                          <Sparkles className="size-3" aria-hidden /> Reasoning
                        </span>
                      )}
                      {m.id === model && <Check className="size-4 text-brand-600" aria-hidden />}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
