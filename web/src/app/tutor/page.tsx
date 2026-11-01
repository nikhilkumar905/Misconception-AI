"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  BookOpen,
  BrainCircuit,
  CircleCheckBig,
  GraduationCap,
  Lightbulb,
  MessagesSquare,
  Network,
  Route,
  Search,
  SendHorizontal,
  ShieldCheck,
  Trash2,
  User,
} from "lucide-react";
import { api, type Diagnosis, type Question } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { useEngine } from "@/components/engine-context";
import { CandidateList } from "@/components/diagnosis";
import { Button, Card, Collapsible, ErrorNotice, InlineCode, Markdown, PageHeader, Skeleton, cx, inputClass } from "@/components/ui";

type Turn = { answer: string; diagnosis?: Diagnosis; error?: string };

export default function TutorPage() {
  const { data: questions, error: qError, retry } = useApi("questions", api.questions);
  const { provider, model, current } = useEngine();

  const [topic, setTopic] = useState("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [history, setHistory] = useState<Record<number, Turn[]>>({});
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const threadEnd = useRef<HTMLDivElement>(null);

  const topics = useMemo(() => ["All", ...Array.from(new Set(questions?.map((q) => q.topic))).sort()], [questions]);
  const filtered = useMemo(
    () =>
      (questions ?? []).filter(
        (q) =>
          (topic === "All" || q.topic === topic) &&
          (!query.trim() || q.question.toLowerCase().includes(query.toLowerCase()) || String(q.id) === query.trim()),
      ),
    [questions, topic, query],
  );

  const question: Question | undefined = questions?.find((q) => q.id === selectedId) ?? questions?.[0];
  const turns = question ? history[question.id] ?? [] : [];
  const answeredCount = Object.values(history).filter((t) => t.length > 0).length;

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turns.length, pending]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!question || !draft.trim() || pending) return;
    const answer = draft.trim();
    const qid = question.id;
    setDraft("");
    setPending(true);
    setHistory((h) => ({ ...h, [qid]: [...(h[qid] ?? []), { answer }] }));
    let update: Partial<Turn>;
    try {
      update = { diagnosis: await api.analyzeAnswer({ provider, model, question_id: qid, answer }) };
    } catch (err) {
      update = { error: (err as Error).message };
    }
    setHistory((h) => {
      const list = [...(h[qid] ?? [])];
      list[list.length - 1] = { ...list[list.length - 1], ...update };
      return { ...h, [qid]: list };
    });
    setPending(false);
  }

  return (
    <>
      <PageHeader
        icon={MessagesSquare}
        eyebrow="Concept tutor"
        title="Check your Python mental model"
        description="Pick a question and answer in your own words. The tutor evaluates your reasoning — not keywords — and explains any misconception it finds."
      />

      {qError && <ErrorNotice message={qError} onRetry={retry} />}

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        {/* Question browser */}
        <Card className="flex flex-col overflow-hidden lg:sticky lg:top-24 lg:h-[calc(100vh-8rem)]">
          <div className="space-y-3 border-b border-line p-4">
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-subtle" aria-hidden />
              <input
                aria-label="Search questions"
                placeholder="Search questions…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className={cx(inputClass, "pl-9")}
              />
            </div>
            <select aria-label="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} className={inputClass}>
              {topics.map((t) => (
                <option key={t} value={t}>
                  {t === "All" ? "All topics" : t}
                </option>
              ))}
            </select>
            <div className="flex items-center justify-between text-xs text-subtle">
              <span>{questions ? `${filtered.length} of ${questions.length} questions` : "Loading…"}</span>
              {questions && <span className="font-medium text-ok-700">{answeredCount} answered</span>}
            </div>
            {questions && (
              <div className="h-1 overflow-hidden rounded-full bg-slate-100" aria-hidden>
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-brand-500 transition-[width] duration-500"
                  style={{ width: `${(answeredCount / questions.length) * 100}%` }}
                />
              </div>
            )}
          </div>
          <ul className="max-h-80 flex-1 overflow-y-auto p-2 lg:max-h-none">
            {!questions &&
              Array.from({ length: 8 }, (_, i) => (
                <li key={i} className="p-2">
                  <Skeleton className="h-10" />
                </li>
              ))}
            {filtered.map((q) => {
              const active = q.id === question?.id;
              const answered = (history[q.id]?.length ?? 0) > 0;
              return (
                <li key={q.id}>
                  <button
                    onClick={() => setSelectedId(q.id)}
                    aria-current={active}
                    className={cx(
                      "flex w-full gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                      active ? "bg-night-900 text-white" : "text-ink hover:bg-brand-50",
                    )}
                  >
                    <span className={cx("font-mono text-xs leading-5", active ? "text-accent-400" : "text-subtle")}>Q{q.id}</span>
                    <span className={cx("line-clamp-2 flex-1", active && "[&_code]:bg-white/15")}>
                      <InlineCode text={q.question} />
                    </span>
                    {answered && <CircleCheckBig className={cx("mt-0.5 size-3.5 shrink-0", active ? "text-emerald-300" : "text-ok-700")} aria-label="Answered" />}
                  </button>
                </li>
              );
            })}
            {questions && filtered.length === 0 && <li className="p-4 text-center text-sm text-subtle">No questions match.</li>}
          </ul>
        </Card>

        {/* Conversation */}
        <Card className="flex min-h-[560px] flex-col">
          {question ? (
            <>
              <div className="flex flex-wrap items-center gap-2 border-b border-line px-5 py-3">
                <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-200">{question.topic}</span>
                <span className="font-mono text-xs text-subtle">Question {question.id}</span>
                {turns.length > 0 && (
                  <button
                    onClick={() => setHistory((h) => ({ ...h, [question.id]: [] }))}
                    className="ml-auto inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:bg-slate-100"
                  >
                    <Trash2 className="size-3.5" aria-hidden /> Clear
                  </button>
                )}
              </div>

              <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6" aria-live="polite">
                <Bubble role="tutor">
                  <Markdown className="text-[15px] font-medium text-night-900">{question.question}</Markdown>
                  <p className="mt-2 text-xs text-subtle">Explain your answer and your reasoning in plain English.</p>
                </Bubble>

                {turns.map((t, i) => (
                  <div key={i} className="space-y-5">
                    <Bubble role="student">
                      <p className="whitespace-pre-wrap text-sm">{t.answer}</p>
                    </Bubble>
                    {t.diagnosis && (
                      <Bubble role="tutor">
                        <TutorReply d={t.diagnosis} />
                      </Bubble>
                    )}
                    {t.error && <ErrorNotice message={t.error} />}
                  </div>
                ))}

                {pending && (
                  <Bubble role="tutor">
                    <div className="flex items-center gap-1.5 py-1" aria-label="Thinking">
                      {[0, 1, 2].map((i) => (
                        <span key={i} className="size-2 animate-bounce rounded-full bg-brand-500" style={{ animationDelay: `${i * 150}ms` }} />
                      ))}
                    </div>
                  </Bubble>
                )}

                {turns.length > 0 && !pending && (
                  <Collapsible icon={BookOpen} title="Reference answer">
                    <Markdown>{question.correct_answer}</Markdown>
                  </Collapsible>
                )}
                <div ref={threadEnd} />
              </div>

              <form onSubmit={submit} className="border-t border-line p-4">
                <div className="flex items-end gap-2 rounded-xl border border-line bg-canvas p-2 focus-within:border-brand-500 focus-within:ring-3 focus-within:ring-brand-100">
                  <textarea
                    aria-label="Your answer"
                    rows={2}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        e.currentTarget.form?.requestSubmit();
                      }
                    }}
                    placeholder="e.g. “range(5) gives 0 to 4 because…”"
                    className="max-h-48 flex-1 resize-y bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-subtle"
                  />
                  <Button type="submit" icon={SendHorizontal} loading={pending} disabled={!draft.trim() || !current} aria-label="Send answer">
                    <span className="hidden sm:inline">Send</span>
                  </Button>
                </div>
                <p className="mt-2 px-1 text-xs text-subtle">Enter to send · Shift + Enter for a new line</p>
              </form>
            </>
          ) : (
            <div className="space-y-3 p-6">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="h-20" />
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

function Bubble({ role, children }: { role: "tutor" | "student"; children: React.ReactNode }) {
  const tutor = role === "tutor";
  return (
    <div className={cx("flex gap-3", !tutor && "flex-row-reverse")}>
      <span
        className={cx("grid size-8 shrink-0 place-items-center rounded-full", tutor ? "bg-gradient-to-br from-brand-600 to-night-900 text-accent-400 shadow-md shadow-brand-600/20" : "bg-gradient-to-br from-accent-100 to-brand-100 text-brand-700")}
        aria-hidden
      >
        {tutor ? <GraduationCap className="size-4" /> : <User className="size-4" />}
      </span>
      <div
        className={cx(
          "rise max-w-[85%] rounded-2xl px-4 py-3",
          tutor ? "rounded-tl-sm border border-line bg-surface shadow-sm" : "rounded-tr-sm bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-md shadow-brand-600/20",
        )}
      >
        {children}
      </div>
    </div>
  );
}

function TutorReply({ d }: { d: Diagnosis }) {
  if (!d.parse_success) {
    return <p className="text-sm text-warn-700">I couldn&apos;t read the model&apos;s response cleanly — please try again.</p>;
  }
  const correct = !d.misconception_found;
  return (
    <div className="space-y-3">
      <span
        className={cx(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset",
          correct ? "bg-ok-50 text-ok-700 ring-ok-200" : "bg-warn-50 text-warn-700 ring-warn-200",
        )}
      >
        {correct ? <CircleCheckBig className="size-3.5" aria-hidden /> : <Lightbulb className="size-3.5" aria-hidden />}
        {correct ? "Correct understanding" : "Misconception detected"}
      </span>
      {!correct && <p className="font-semibold text-night-900">{d.description}</p>}
      {d.explanation && <Markdown className="text-sm">{d.explanation}</Markdown>}

      <div className="space-y-2 pt-1">
        {d.trace && (
          <Collapsible icon={Route} title="How your reasoning was read">
            <Markdown>{d.trace}</Markdown>
          </Collapsible>
        )}
        {d.verification && (
          <Collapsible icon={ShieldCheck} title="What Python actually does">
            <Markdown>{d.verification}</Markdown>
          </Collapsible>
        )}
        {d.retrieved_candidates.length > 0 && (
          <Collapsible icon={Network} title="Related misconceptions">
            <CandidateList candidates={d.retrieved_candidates} />
          </Collapsible>
        )}
      </div>
      <p className="flex items-center gap-1.5 text-[11px] text-subtle">
        <BrainCircuit className="size-3" aria-hidden /> Enhanced RAG + chain-of-thought analysis
      </p>
    </div>
  );
}
