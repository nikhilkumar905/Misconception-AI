"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenText, BrainCircuit, ChartColumn, FlaskConical, House, MessagesSquare } from "lucide-react";
import { cx } from "./ui";
import { EnginePicker } from "./engine-picker";

const NAV = [
  { href: "/", label: "Overview", icon: House },
  { href: "/lab", label: "Mining lab", icon: FlaskConical },
  { href: "/tutor", label: "Concept tutor", icon: MessagesSquare },
  { href: "/results", label: "Results", icon: ChartColumn },
  { href: "/taxonomy", label: "Taxonomy", icon: BookOpenText },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 bg-night-900/95 text-white shadow-[0_1px_0_rgba(255,255,255,0.06),0_8px_24px_-12px_rgba(7,21,40,0.5)] backdrop-blur-md supports-[backdrop-filter]:bg-night-900/85">
      <div className="aurora-line h-[3px]" />
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 sm:px-6">
        <Link href="/" className="group flex shrink-0 items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-accent-400">
          <span className="grid size-9 place-items-center rounded-lg bg-gradient-to-br from-white/15 to-white/5 ring-1 ring-white/15 transition-transform group-hover:rotate-6">
            <BrainCircuit className="size-5 text-accent-400" aria-hidden />
          </span>
          <span className="leading-tight">
            <span className="block text-[15px] font-semibold tracking-tight">MisconAI</span>
            <span className="block text-[11px] font-medium tracking-wide text-brand-200">Misconception Studio</span>
          </span>
        </Link>

        <nav aria-label="Main" className="hidden flex-1 items-center gap-1 lg:flex">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cx(
                  "relative inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  "focus-visible:outline-2 focus-visible:outline-accent-400",
                  active ? "bg-white/10 text-white" : "text-brand-100/75 hover:-translate-y-px hover:bg-white/5 hover:text-white",
                )}
              >
                <Icon className="size-4" aria-hidden />
                {label}
                {active && <span className="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-gradient-to-r from-brand-500 to-accent-400 shadow-[0_0_12px_rgba(69,227,203,0.7)]" />}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto lg:ml-0">
          <EnginePicker />
        </div>
      </div>

      {/* Compact navigation for small screens */}
      <nav aria-label="Main mobile" className="flex gap-1 overflow-x-auto border-t border-white/10 px-3 py-2 lg:hidden">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cx(
                "inline-flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm",
                active ? "bg-white/15 text-white" : "text-brand-100/80",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
