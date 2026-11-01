"use client";

import Link from "next/link";
import { ArrowRight, BookOpenText, FlaskConical, Library, MessagesSquare, Route, ScanSearch, ShieldCheck, Tag, Target } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { Card, CountUp, Reveal, Skeleton } from "@/components/ui";

const STEPS = [
  { icon: ScanSearch, title: "Retrieve", body: "Code constructs — loops, indexing, operators — are matched against the misconception bank. The most relevant definitions are injected into the prompt." },
  { icon: Route, title: "Trace", body: "The model mentally executes the code on a concrete input and records exactly where behaviour diverges from the task." },
  { icon: ShieldCheck, title: "Verify", body: "A correctness gate asks whether the code is actually valid or an acceptable alternative. If so, the answer is forced to NONE." },
  { icon: Tag, title: "Diagnose", body: "Only then is a misconception named — phrased as “The student believes…” with a teaching explanation." },
];

const EXAMPLES = [
  ["range", "range(n) assumed to run 1…n"],
  ["tuples", "calling .append() on a tuple"],
  ["operators", "if x = 0: instead of =="],
  ["boolean logic", "x == a or b read as “x is a or b”"],
];

export default function OverviewPage() {
  const { data: results } = useApi("results", api.results);
  const best = results?.reduce((a, b) => (b.precision > a.precision ? b : a));

  const stats = [
    { icon: Target, label: "Peak precision", value: best && <CountUp value={best.precision * 100} decimals={1} suffix="%" />, note: best?.label },
    {
      icon: ShieldCheck,
      label: "Clean-code accuracy",
      value: best && <CountUp value={best.correct_only_accuracy * 100} decimals={1} suffix="%" />,
      note: "Correct code left unflagged",
    },
    { icon: Library, label: "Misconceptions indexed", value: <CountUp value={67} />, note: "Standardized taxonomy" },
    { icon: MessagesSquare, label: "Concept questions", value: <CountUp value={75} />, note: "Across 24 topics" },
  ];

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="rise relative overflow-hidden rounded-3xl bg-night-950 px-6 py-12 text-white shadow-2xl shadow-brand-700/25 ring-1 ring-white/10 sm:px-12 sm:py-16">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:linear-gradient(white_1px,transparent_1px),linear-gradient(90deg,white_1px,transparent_1px)] [background-size:32px_32px]"
        />
        <div aria-hidden className="aurora pointer-events-none absolute -top-32 -right-24 size-[28rem] rounded-full bg-brand-500/40 blur-3xl" />
        <div aria-hidden className="aurora pointer-events-none absolute -bottom-40 left-1/4 size-96 rounded-full bg-accent-500/25 blur-3xl [animation-delay:-6s]" />
        <div aria-hidden className="aurora pointer-events-none absolute top-1/3 -left-24 size-72 rounded-full bg-fuchsia-500/20 blur-3xl [animation-delay:-12s]" />
        <div className="relative grid items-center gap-10 lg:grid-cols-[1.15fr_1fr] [&>*]:min-w-0">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-accent-400 ring-1 ring-white/15">
              <span className="size-1.5 rounded-full bg-accent-400" /> Enhanced Methodology
            </p>
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Find the <span className="text-gradient-gold">why</span> behind buggy student code.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-brand-100/85">
              MisconAI reads a Python submission, simulates it step by step, rules out false alarms and names the underlying
              misconception from a 67-entry taxonomy.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/lab"
                className="shine inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-accent-400 to-accent-500 px-5 py-2.5 text-sm font-semibold text-night-950 shadow-lg shadow-accent-500/30 transition-all hover:-translate-y-0.5 hover:shadow-accent-500/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-400"
              >
                <FlaskConical className="size-4" aria-hidden /> Analyze student code
              </Link>
              <Link
                href="/tutor"
                className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 backdrop-blur transition-all hover:-translate-y-0.5 hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-400"
              >
                <MessagesSquare className="size-4" aria-hidden /> Try the concept tutor
              </Link>
            </div>
          </div>

          <div className="spin-border rounded-2xl bg-night-900/70 p-5 font-mono text-[13px] leading-6 shadow-2xl shadow-black/40 backdrop-blur-xl transition-transform duration-500 hover:-translate-y-1 lg:rotate-1 lg:hover:rotate-0">
            <div className="mb-3 flex gap-1.5" aria-hidden>
              <span className="size-2.5 rounded-full bg-rose-400/80" />
              <span className="size-2.5 rounded-full bg-amber-300/80" />
              <span className="size-2.5 rounded-full bg-emerald-400/80" />
            </div>
            <pre className="overflow-x-auto text-slate-200">
              <span className="text-sky-300">def</span> <span className="text-accent-400">factorial</span>(n):{"\n"}
              {"    "}fact = <span className="text-emerald-300">1</span>{"\n"}
              {"    "}<span className="text-sky-300">for</span> i <span className="text-sky-300">in</span> range(n):{"\n"}
              {"        "}fact = fact * i{"\n"}
              {"    "}<span className="text-sky-300">return</span> fact<span className="caret ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-accent-400" />
            </pre>
            <div className="rise mt-4 rounded-lg border border-rose-300/30 bg-gradient-to-r from-rose-500/20 to-fuchsia-500/10 px-3 py-2.5 font-sans text-sm [animation-delay:600ms]">
              <p className="text-xs font-semibold uppercase tracking-wider text-red-300">Misconception identified</p>
              <p className="mt-1 text-slate-100">The student believes <code className="font-mono">range(n)</code> produces 1 to n inclusive.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section aria-label="Key figures" className="stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ icon: Icon, label, value, note }) => (
          <Card key={label} interactive className="p-5">
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="grid size-7 place-items-center rounded-lg bg-brand-50 text-brand-600">
                <Icon className="size-4" aria-hidden />
              </span>
              {label}
            </div>
            {value ? (
              <p className="mt-2 text-3xl font-semibold tracking-tight text-night-900 tabular-nums">{value}</p>
            ) : (
              <Skeleton className="mt-3 h-8 w-24" />
            )}
            <p className="mt-1 text-xs text-subtle">{note ?? " "}</p>
          </Card>
        ))}
      </section>

      {/* Pipeline */}
      <Reveal>
        <h2 className="text-2xl font-semibold tracking-tight text-night-900">How the Enhanced Methodology works</h2>
        <p className="mt-1 text-muted">Four steps that force the model to reason before it diagnoses.</p>
        <ol className="stagger mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <li key={title}>
              <Card interactive className="group h-full p-5">
                <div className="flex items-center justify-between">
                  <span className="grid size-10 place-items-center rounded-lg bg-gradient-to-br from-night-800 to-night-950 text-accent-400 shadow-md shadow-night-900/20 transition-transform group-hover:scale-110">
                    <Icon className="size-5" aria-hidden />
                  </span>
                  <span className="font-mono text-2xl font-semibold text-brand-100 transition-colors group-hover:text-accent-400">0{i + 1}</span>
                </div>
                <h3 className="mt-4 font-semibold text-night-900">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{body}</p>
              </Card>
            </li>
          ))}
        </ol>
      </Reveal>

      {/* Definition */}
      <Reveal className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-xl font-semibold tracking-tight text-night-900">What counts as a misconception?</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            A systematic false belief about language semantics — reproducible across problems and distinct from a typo or a
            misread prompt.
          </p>
          <ul className="mt-5 divide-y divide-line">
            {EXAMPLES.map(([tag, text]) => (
              <li key={tag} className="flex items-center gap-3 py-2.5 text-sm">
                <span className="w-28 shrink-0 rounded-md bg-gradient-to-r from-brand-50 to-accent-100 px-2 py-0.5 text-center text-xs font-medium text-brand-700">{tag}</span>
                <span className="font-mono text-[13px] text-ink">{text}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="flex flex-col justify-between gap-6 p-6">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-night-900">Explore the taxonomy</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Browse all 67 standardized misconceptions with their related constructs and worked examples — the same entries
              the retrieval step injects into every analysis.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/taxonomy" className="shine inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-600 to-brand-500 px-4 py-2.5 text-sm font-medium text-white shadow-md shadow-brand-600/25 transition-transform hover:-translate-y-0.5">
              <BookOpenText className="size-4" aria-hidden /> Open taxonomy
            </Link>
            <Link href="/results" className="inline-flex items-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-night-900 hover:bg-brand-50">
              View results <ArrowRight className="size-4" aria-hidden />
            </Link>
          </div>
        </Card>
      </Reveal>
    </div>
  );
}
