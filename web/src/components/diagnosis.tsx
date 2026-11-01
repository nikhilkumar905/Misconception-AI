"use client";

import { Bug, CircleCheckBig, Network, Route, ShieldCheck, TriangleAlert } from "lucide-react";
import type { Candidate, Diagnosis } from "@/lib/api";
import { humanize } from "@/lib/api";
import { Collapsible, CopyButton, Markdown, cx } from "./ui";

export function CandidateList({ candidates }: { candidates: Candidate[] }) {
  return (
    <ul className="space-y-3">
      {candidates.map((c) => (
        <li key={c.id} className="flex gap-3">
          <span className="mt-0.5 h-fit shrink-0 rounded-md bg-night-900 px-1.5 py-0.5 font-mono text-[11px] font-medium text-accent-400">#{c.id}</span>
          <div>
            <p className="text-ink">{c.description}</p>
            {c.constructs.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {c.constructs.slice(0, 4).map((k) => (
                  <span key={k} className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-muted">
                    {humanize(k)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function DiagnosisView({ result }: { result: Diagnosis }) {
  if (!result.parse_success) {
    return (
      <div className="space-y-3">
        <div className="flex items-start gap-3 rounded-xl border border-warn-200 bg-warn-50 p-4 text-sm text-warn-700">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          The model answered, but not in the expected format. Try again or switch model.
        </div>
        <Collapsible icon={Route} title="Raw model output">
          <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs text-muted">{result.raw_response}</pre>
        </Collapsible>
      </div>
    );
  }

  const found = result.misconception_found;

  return (
    <div className="space-y-3">
      <div
        className={cx(
          "rise overflow-hidden rounded-xl border bg-surface shadow-[0_10px_30px_-18px_rgba(15,23,42,0.35)]",
          found ? "border-bad-200" : "border-ok-200",
        )}
      >
        <div className={cx("flex items-center gap-2 px-5 py-3 text-sm font-semibold", found ? "bg-bad-50 text-bad-700" : "bg-ok-50 text-ok-700")}>
          {found ? <Bug className="size-4" aria-hidden /> : <CircleCheckBig className="size-4" aria-hidden />}
          {found ? "Misconception identified" : "Clean code — no misconception detected"}
          <span className="ml-auto">
            <CopyButton text={[result.description, result.explanation].filter(Boolean).join("\n\n")} label="Copy diagnosis" />
          </span>
        </div>
        <div className="space-y-3 px-5 py-4">
          {found ? (
            <h3 className="text-lg font-semibold leading-snug text-night-900">{result.description}</h3>
          ) : (
            <p className="text-sm text-muted">The code is correct or uses an acceptable alternative approach.</p>
          )}
          {result.explanation && <Markdown className="text-sm">{result.explanation}</Markdown>}
        </div>
      </div>

      {result.trace && (
        <Collapsible icon={Route} title="Execution trace" defaultOpen={found}>
          <Markdown>{result.trace}</Markdown>
        </Collapsible>
      )}
      {result.verification && (
        <Collapsible icon={ShieldCheck} title="Verification gate" defaultOpen={!found}>
          <Markdown>{result.verification}</Markdown>
        </Collapsible>
      )}
      {result.retrieved_candidates.length > 0 && (
        <Collapsible icon={Network} title={`Taxonomy candidates (${result.retrieved_candidates.length})`}>
          <CandidateList candidates={result.retrieved_candidates} />
        </Collapsible>
      )}
    </div>
  );
}
