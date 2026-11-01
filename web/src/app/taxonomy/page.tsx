"use client";

import { useMemo, useState } from "react";
import { BookOpenText, ChevronDown, Search, X } from "lucide-react";
import { api, humanize } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { Card, ErrorNotice, Markdown, PageHeader, Skeleton, cx, inputClass } from "@/components/ui";

export default function TaxonomyPage() {
  const { data: bank, error, retry } = useApi("taxonomy", api.taxonomy);
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState<string[]>([]);

  const topConstructs = useMemo(() => {
    const counts = new Map<string, number>();
    bank?.forEach((m) => m.constructs.forEach((c) => counts.set(c, (counts.get(c) ?? 0) + 1)));
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 14).map(([c]) => c);
  }, [bank]);

  const filtered = useMemo(() => {
    const s = query.toLowerCase().trim();
    return (bank ?? []).filter((m) => {
      const text = `${m.description} ${m.constructs.join(" ")}`.toLowerCase();
      if (s && !text.includes(s) && String(m.id) !== s) return false;
      if (picked.length && !picked.some((p) => m.constructs.includes(p))) return false;
      return true;
    });
  }, [bank, query, picked]);

  const toggle = (c: string) => setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p, c]));

  return (
    <>
      <PageHeader
        icon={BookOpenText}
        eyebrow="Taxonomy"
        title="Python misconception bank"
        description="The standardized misconceptions the retrieval step draws from, each with related constructs and a worked example."
      />

      {error && <ErrorNotice message={error} onRetry={retry} />}

      <Card className="mb-6 p-4 sm:p-5">
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-subtle" aria-hidden />
          <input
            aria-label="Search misconceptions"
            placeholder="Search by keyword or ID — e.g. range, slicing, tuple, recursion"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={cx(inputClass, "py-2.5 pl-9")}
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {topConstructs.map((c) => {
            const on = picked.includes(c);
            return (
              <button
                key={c}
                onClick={() => toggle(c)}
                aria-pressed={on}
                className={cx(
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                  on ? "border-night-900 bg-night-900 text-white" : "border-line text-muted hover:border-brand-200 hover:text-night-900",
                )}
              >
                {humanize(c)}
              </button>
            );
          })}
          {(picked.length > 0 || query) && (
            <button
              onClick={() => {
                setPicked([]);
                setQuery("");
              }}
              className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs text-brand-600 hover:underline"
            >
              <X className="size-3" aria-hidden /> Clear filters
            </button>
          )}
        </div>
        <p className="mt-3 text-xs text-subtle">{bank ? `Showing ${filtered.length} of ${bank.length}` : "Loading…"}</p>
      </Card>

      <div className="grid items-start gap-4 md:grid-cols-2">
        {!bank && !error && Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        {filtered.map((m) => (
          <details key={m.id} className="group rounded-xl border border-line bg-surface transition-all hover:border-brand-200 hover:shadow-sm open:shadow-md">
            <summary className="flex cursor-pointer list-none gap-3 p-4 [&::-webkit-details-marker]:hidden">
              <span className="h-fit rounded-md bg-night-900 px-2 py-0.5 font-mono text-xs font-medium text-accent-400">#{m.id}</span>
              <span className="flex-1">
                <span className="block text-sm font-medium leading-snug text-night-900">{m.description}</span>
                <span className="mt-2 flex flex-wrap gap-1">
                  {m.constructs.map((c) => (
                    <span key={c} className="rounded bg-brand-50 px-1.5 py-0.5 text-[11px] text-brand-700">
                      {humanize(c)}
                    </span>
                  ))}
                </span>
              </span>
              <ChevronDown className="mt-0.5 size-4 shrink-0 text-subtle transition-transform group-open:rotate-180" aria-hidden />
            </summary>
            <div className="border-t border-line px-4 py-4 text-sm">
              <Markdown>{m.example || "No example available."}</Markdown>
            </div>
          </details>
        ))}
        {bank && filtered.length === 0 && (
          <p className="col-span-full rounded-xl border border-dashed border-line p-10 text-center text-sm text-muted">
            No misconceptions match these filters.
          </p>
        )}
      </div>
    </>
  );
}
