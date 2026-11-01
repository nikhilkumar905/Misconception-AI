"use client";

import { ChartColumn, Cpu, Scale } from "lucide-react";
import { api, pct, type ModelResult } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { Card, ErrorNotice, PageHeader, Skeleton, cx } from "@/components/ui";

const METRICS: { key: keyof ModelResult; label: string }[] = [
  { key: "overall_accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1_score", label: "F1" },
  { key: "correct_only_accuracy", label: "Clean-code accuracy" },
];

// Series colours: violet and aqua read clearly side by side and in print.
const SERIES = ["bg-gradient-to-r from-brand-700 to-brand-500", "bg-gradient-to-r from-accent-700 to-accent-400"];
const SERIES_DOT = ["bg-brand-600", "bg-accent-500"];

export default function ResultsPage() {
  const { data: results, error, retry } = useApi("results", api.results);

  return (
    <>
      <PageHeader
        icon={ChartColumn}
        eyebrow="Results"
        title="Enhanced Methodology evaluation"
        description="50 balanced bags per model: 35 bags with a ground-truth misconception and 15 bags of correct code only."
      />

      {error && <ErrorNotice message={error} onRetry={retry} />}

      {/* Per-model scorecards */}
      <div className="stagger grid gap-6 lg:grid-cols-2">
        {(results ?? [undefined, undefined]).map((r, i) => (
          <Card key={r?.label ?? i} interactive className="overflow-hidden">
            <div className="flex items-center gap-3 border-b border-line bg-canvas px-5 py-4">
              <span className={cx("size-3 rounded-sm", SERIES_DOT[i])} aria-hidden />
              {r ? (
                <>
                  <div>
                    <p className="font-semibold text-night-900">{r.label}</p>
                    <p className="font-mono text-xs text-subtle">{r.model}</p>
                  </div>
                  <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-200">
                    <Cpu className="size-3" aria-hidden /> {r.provider}
                  </span>
                </>
              ) : (
                <Skeleton className="h-9 w-48" />
              )}
            </div>
            <dl className="grid grid-cols-2 divide-line sm:grid-cols-3 [&>div]:border-line">
              {[
                ["Accuracy", r && pct(r.overall_accuracy)],
                ["Precision", r && pct(r.precision)],
                ["Recall", r && pct(r.recall)],
                ["F1 score", r && pct(r.f1_score)],
                ["Clean-code accuracy", r && `${pct(r.correct_only_accuracy)}`],
                ["False alarms", r && `${r.fp}`],
              ].map(([label, value]) => (
                <div key={label} className="border-r border-b p-4 last:border-r-0">
                  <dt className="text-xs text-subtle">{label}</dt>
                  <dd className="mt-1 text-2xl font-semibold tracking-tight text-night-900 tabular-nums">
                    {value ?? <Skeleton className="h-7 w-16" />}
                  </dd>
                </div>
              ))}
            </dl>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        {/* Grouped bars */}
        <Card className="p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold text-night-900">Metric comparison</h2>
            <div className="flex gap-4 text-xs text-muted">
              {results?.map((r, i) => (
                <span key={r.label} className="inline-flex items-center gap-1.5">
                  <span className={cx("size-2.5 rounded-sm", SERIES_DOT[i])} aria-hidden /> {r.label}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-6 space-y-5">
            {METRICS.map(({ key, label }) => (
              <div key={key}>
                <p className="mb-1.5 text-sm text-muted">{label}</p>
                <div className="space-y-1.5">
                  {(results ?? [undefined, undefined]).map((r, i) => {
                    const v = r ? (r[key] as number) : 0;
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <div className="h-3.5 flex-1 rounded-full bg-slate-100">
                          <div
                            className={cx("grow-x h-full rounded-full transition-[width] duration-700", SERIES[i])}
                            style={{ width: `${v * 100}%` }}
                            role="img"
                            aria-label={r ? `${r.label} ${label} ${pct(v)}` : undefined}
                          />
                        </div>
                        <span className="w-14 text-right font-mono text-xs text-ink tabular-nums">{r ? pct(v) : "—"}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Confusion counts */}
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <h2 className="border-b border-line px-5 py-4 font-semibold text-night-900">Confusion counts</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-canvas text-left text-xs text-subtle">
                  <tr>
                    <th className="px-5 py-2.5 font-medium">Model</th>
                    {["TP", "FP", "FN", "TN"].map((h) => (
                      <th key={h} className="px-3 py-2.5 text-right font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {results?.map((r) => (
                    <tr key={r.label}>
                      <td className="px-5 py-3 font-medium text-night-900">{r.label}</td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums text-ok-700">{r.tp}</td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums text-bad-700">{r.fp}</td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums text-warn-700">{r.fn}</td>
                      <td className="px-3 py-3 text-right font-mono tabular-nums text-ok-700">{r.tn}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="border-t border-line px-5 py-3 text-xs leading-relaxed text-subtle">
              <b className="text-muted">TP</b> found &amp; matched · <b className="text-muted">FP</b> false alarm or wrong label ·{" "}
              <b className="text-muted">FN</b> missed · <b className="text-muted">TN</b> clean code confirmed
            </p>
          </Card>

          <div className="flex gap-3 rounded-xl border border-accent-400/50 bg-gradient-to-br from-accent-100/70 to-brand-50 p-5">
            <Scale className="mt-0.5 size-5 shrink-0 text-accent-700" aria-hidden />
            <div>
              <p className="font-semibold text-night-900">Precision by design</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">
                The verification gate is deliberately conservative: when the model can&apos;t establish that code is wrong, it
                answers NONE instead of inventing a misconception — trading some recall for high precision and clean-code accuracy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
