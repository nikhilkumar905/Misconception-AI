"use client";

import { useEffect, useState } from "react";
import { CircleCheck, Bug, Check, FlaskConical, Play, RotateCcw, ScanSearch, StickyNote } from "lucide-react";
import { api, type Diagnosis, type Preset } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { useEngine } from "@/components/engine-context";
import { DiagnosisView } from "@/components/diagnosis";
import { Button, Card, ErrorNotice, Field, PageHeader, Skeleton, cx, inputClass } from "@/components/ui";

const ANALYSIS_STEPS = ["Retrieving taxonomy candidates", "Tracing execution", "Running verification gate", "Writing diagnosis"];

export default function LabPage() {
  const { data: presets, error: presetsError, retry } = useApi("presets", api.presets);
  const { provider, model, current } = useEngine();

  const [selected, setSelected] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<Diagnosis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  // Advance the progress indicator while the model works; the last step holds until the response lands.
  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => setStep((s) => Math.min(s + 1, ANALYSIS_STEPS.length - 1)), 2200);
    return () => clearInterval(id);
  }, [loading]);

  // Load the first example once presets arrive.
  const [initialised, setInitialised] = useState(false);
  if (presets && !initialised) {
    setInitialised(true);
    applyPreset(presets[0]);
  }

  function applyPreset(p: Preset) {
    setSelected(p.name);
    setTitle(p.title);
    setDescription(p.desc);
    setCode(p.code);
    setResult(null);
    setError(null);
  }

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStep(0);
    setError(null);
    setResult(null);
    try {
      setResult(await api.analyzeCode({ provider, model, title, description, code }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const preset = presets?.find((p) => p.name === selected);
  const lineCount = Math.max(code.split("\n").length, 12);

  return (
    <>
      <PageHeader
        icon={FlaskConical}
        eyebrow="Mining lab"
        title="Diagnose a student submission"
        description="Paste student code or start from an example. MisconAI traces it, verifies it and names the misconception — or confirms the code is clean."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input */}
        <Card className="p-5 sm:p-6">
          <p className="text-sm font-medium text-night-900">Examples</p>
          {presetsError ? (
            <div className="mt-2">
              <ErrorNotice message={presetsError} onRetry={retry} />
            </div>
          ) : (
            <div className="mt-2 flex flex-wrap gap-2">
              {presets
                ? presets.map((p) => (
                    <button
                      key={p.name}
                      type="button"
                      onClick={() => applyPreset(p)}
                      aria-pressed={selected === p.name}
                      className={cx(
                        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors",
                        "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand-500",
                        selected === p.name
                          ? "border-night-900 bg-night-900 text-white"
                          : "border-line bg-surface text-muted hover:border-brand-200 hover:text-night-900",
                      )}
                    >
                      {p.expect_clean ? (
                        <CircleCheck className={cx("size-3.5", selected === p.name ? "text-emerald-300" : "text-ok-700")} aria-hidden />
                      ) : (
                        <Bug className={cx("size-3.5", selected === p.name ? "text-red-300" : "text-bad-700")} aria-hidden />
                      )}
                      {p.name}
                    </button>
                  ))
                : Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-8 w-28 rounded-full" />)}
            </div>
          )}
          {preset && (
            <p className="mt-3 flex items-start gap-2 rounded-lg bg-accent-100/60 px-3 py-2 text-xs text-accent-700">
              <StickyNote className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {preset.notes}
            </p>
          )}

          <form onSubmit={analyze} className="mt-5 space-y-4">
            <Field label="Problem title" htmlFor="title">
              <input id="title" className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} />
            </Field>
            <Field label="Problem description" htmlFor="desc">
              <textarea id="desc" rows={3} className={cx(inputClass, "resize-y")} value={description} onChange={(e) => setDescription(e.target.value)} />
            </Field>
            <Field label="Student code" htmlFor="code">
              <div className="overflow-hidden rounded-lg border border-night-800 bg-night-950 shadow-inner focus-within:ring-3 focus-within:ring-brand-200">
              <div className="flex items-center gap-2 border-b border-white/10 bg-white/[0.03] px-3 py-2">
                <span className="flex gap-1.5" aria-hidden>
                  <span className="size-2.5 rounded-full bg-red-400/70" />
                  <span className="size-2.5 rounded-full bg-amber-300/70" />
                  <span className="size-2.5 rounded-full bg-emerald-400/70" />
                </span>
                <span className="ml-2 font-mono text-xs text-slate-400">student.py</span>
                <span className="ml-auto font-mono text-[11px] text-slate-500">
                  {code.split("\n").length} lines · {code.length} chars
                </span>
              </div>
              <div className="flex">
                <div aria-hidden className="select-none border-r border-white/10 px-3 py-3 text-right font-mono text-[13px] leading-6 text-slate-500">
                  {Array.from({ length: lineCount }, (_, i) => (
                    <div key={i}>{i + 1}</div>
                  ))}
                </div>
                <textarea
                  id="code"
                  spellCheck={false}
                  rows={lineCount}
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value);
                    setSelected(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                      e.preventDefault();
                      e.currentTarget.form?.requestSubmit();
                      return;
                    }
                    if (e.key === "Tab") {
                      e.preventDefault();
                      const t = e.currentTarget;
                      const { selectionStart: s, selectionEnd: end } = t;
                      setCode(code.slice(0, s) + "    " + code.slice(end));
                      requestAnimationFrame(() => t.setSelectionRange(s + 4, s + 4));
                    }
                  }}
                  className="w-full resize-none bg-transparent px-3 py-3 font-mono text-[13px] leading-6 text-slate-100 caret-accent-400 outline-none"
                />
              </div>
              </div>
            </Field>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Button type="submit" icon={Play} loading={loading} disabled={!code.trim() || !current}>
                {loading ? "Analyzing…" : "Analyze code"}
              </Button>
              {presets && (
                <Button type="button" variant="ghost" icon={RotateCcw} onClick={() => applyPreset(presets[0])} disabled={loading}>
                  Reset
                </Button>
              )}
              <kbd className="hidden rounded border border-line bg-canvas px-1.5 py-0.5 font-mono text-[11px] text-subtle sm:inline">Ctrl + Enter</kbd>
              <span className="ml-auto text-xs text-subtle">
                Engine: <span className="font-medium text-muted">{current?.label}</span> · <span className="font-mono">{model}</span>
              </span>
            </div>
          </form>
        </Card>

        {/* Output */}
        <div aria-live="polite">
          {error && <ErrorNotice message={error} />}

          {loading && (
            <Card className="rise p-6">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-night-900">Analyzing with {model}</p>
                <span className="font-mono text-xs text-subtle">
                  {step + 1}/{ANALYSIS_STEPS.length}
                </span>
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-500 transition-[width] duration-700"
                  style={{ width: `${((step + 1) / ANALYSIS_STEPS.length) * 100}%` }}
                />
              </div>
              <ol className="mt-5 space-y-3">
                {ANALYSIS_STEPS.map((s, i) => (
                  <li
                    key={s}
                    className={cx(
                      "flex items-center gap-3 text-sm transition-colors",
                      i < step ? "text-ok-700" : i === step ? "font-medium text-night-900" : "text-subtle",
                    )}
                  >
                    <span
                      className={cx(
                        "grid size-5 place-items-center rounded-full ring-1",
                        i < step ? "bg-ok-50 ring-ok-200" : i === step ? "bg-brand-50 ring-brand-200" : "bg-surface ring-line",
                      )}
                      aria-hidden
                    >
                      {i < step ? (
                        <Check className="size-3" />
                      ) : i === step ? (
                        <span className="size-2 animate-ping rounded-full bg-brand-500" />
                      ) : (
                        <span className="size-1.5 rounded-full bg-slate-300" />
                      )}
                    </span>
                    {s}
                  </li>
                ))}
              </ol>
              <div className="mt-6 space-y-2">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </Card>
          )}

          {result && !loading && <DiagnosisView result={result} />}

          {!result && !loading && !error && (
            <div className="grid h-full min-h-80 place-items-center rounded-xl border-2 border-dashed border-line bg-gradient-to-b from-surface/80 to-brand-50/40 p-8 text-center">
              <div className="max-w-sm">
                <span className="float-slow mx-auto grid size-14 place-items-center rounded-2xl bg-gradient-to-br from-night-800 to-night-950 text-accent-400 shadow-lg shadow-night-900/25">
                  <ScanSearch className="size-6" aria-hidden />
                </span>
                <p className="mt-4 font-semibold text-night-900">The diagnosis appears here</p>
                <p className="mt-1 text-sm text-muted">
                  Pick an example and press <span className="font-medium text-night-900">Analyze code</span>. You&apos;ll get the
                  execution trace, the verification check and the taxonomy entries the model compared against.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
