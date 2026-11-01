"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, CircleAlert, Copy, RotateCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function PageHeader({
  icon: Icon,
  eyebrow,
  title,
  description,
  children,
}: {
  icon: LucideIcon;
  eyebrow: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rise mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex max-w-3xl gap-4">
        <span className="hidden size-12 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-600 via-night-800 to-night-950 text-accent-400 shadow-lg shadow-brand-600/25 ring-1 ring-white/10 sm:grid">
          <Icon className="size-6" aria-hidden />
        </span>
        <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">{eyebrow}</p>
        <h1 className="text-3xl font-semibold tracking-tight text-night-900">{title}</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-muted">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

export function Card({ className, interactive, children }: { className?: string; interactive?: boolean; children: React.ReactNode }) {
  return (
    <div
      className={cx(
        "rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        interactive && "transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-[0_10px_30px_-12px_rgba(15,23,42,0.25)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

const badgeTones = {
  brand: "bg-brand-50 text-brand-700 ring-brand-200",
  ok: "bg-ok-50 text-ok-700 ring-ok-200",
  bad: "bg-bad-50 text-bad-700 ring-bad-200",
  warn: "bg-warn-50 text-warn-700 ring-warn-200",
  gold: "bg-accent-100 text-accent-700 ring-accent-400/50",
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function Badge({
  tone = "brand",
  icon: Icon,
  children,
}: {
  tone?: keyof typeof badgeTones;
  icon?: LucideIcon;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        badgeTones[tone],
      )}
    >
      {Icon && <Icon className="size-3.5" aria-hidden />}
      {children}
    </span>
  );
}

export function Collapsible({
  icon: Icon,
  title,
  defaultOpen,
  children,
}: {
  icon: LucideIcon;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  return (
    <details open={defaultOpen} className="group rounded-xl border border-line bg-surface">
      <summary className="flex cursor-pointer list-none items-center gap-2.5 px-4 py-3 text-sm font-medium text-night-900 select-none [&::-webkit-details-marker]:hidden">
        <span className="grid size-7 place-items-center rounded-lg bg-brand-50 text-brand-600">
          <Icon className="size-4" aria-hidden />
        </span>
        {title}
        <ChevronDown className="ml-auto size-4 text-subtle transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <div className="border-t border-line px-4 py-4 text-sm">{children}</div>
    </details>
  );
}

export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cx("prose-md", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}

/** Render `backtick` spans as inline code without a full markdown pass. */
export function InlineCode({ text }: { text: string }) {
  return (
    <>
      {text.split(/(`[^`]+`)/g).map((part, i) =>
        part.startsWith("`") && part.endsWith("`") ? (
          <code key={i} className="rounded bg-black/[0.06] px-1 font-mono text-[0.85em]">
            {part.slice(1, -1)}
          </code>
        ) : (
          part
        ),
      )}
    </>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cx("relative overflow-hidden rounded-lg bg-slate-200/70", className)}>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.4s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
    </div>
  );
}

export function ErrorNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-bad-200 bg-bad-50 px-4 py-3 text-sm text-bad-700">
      <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <p className="flex-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 font-medium hover:bg-bad-200/50 focus-visible:outline-2 focus-visible:outline-bad-700"
        >
          <RotateCw className="size-3.5" aria-hidden /> Retry
        </button>
      )}
    </div>
  );
}

export function Button({
  variant = "primary",
  icon: Icon,
  loading,
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  icon?: LucideIcon;
  loading?: boolean;
}) {
  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500",
        "disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" &&
          "shine bg-gradient-to-r from-brand-600 via-brand-500 to-brand-600 text-white shadow-md shadow-brand-600/25 hover:shadow-lg hover:shadow-brand-600/30 active:scale-[0.98]",
        variant === "secondary" && "border border-line bg-surface text-night-900 hover:bg-brand-50",
        variant === "ghost" && "text-muted hover:bg-slate-100 hover:text-night-900",
        className,
      )}
    >
      {loading ? (
        <span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden />
      ) : (
        Icon && <Icon className="size-4" aria-hidden />
      )}
      {children}
    </button>
  );
}

export const inputClass =
  "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-subtle shadow-[inset_0_1px_1px_rgba(15,23,42,0.03)] focus:border-brand-500 focus:outline-none focus:ring-3 focus:ring-brand-100";

export function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-night-900">
        {label}
      </label>
      {children}
    </div>
  );
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1600);
        } catch {}
      }}
      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-current/80 transition-colors hover:bg-black/5 focus-visible:outline-2 focus-visible:outline-brand-500"
    >
      {copied ? <Check className="size-3.5" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
      {copied ? "Copied" : label}
    </button>
  );
}

/** Fade and lift children into view the first time they scroll on screen. */
export function Reveal({ className, delay = 0, children }: { className?: string; delay?: number; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.15 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div ref={ref} className={cx("reveal", visible && "is-visible", className)} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

/** Animate a number from 0 to `value`, keeping the given decimals and suffix. */
export function CountUp({ value, decimals = 0, suffix = "" }: { value: number; decimals?: number; suffix?: string }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 1100;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = duration ? Math.min((now - start) / duration, 1) : 1;
      setShown(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return (
    <>
      {shown.toFixed(decimals)}
      {suffix}
    </>
  );
}
