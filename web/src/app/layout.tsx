import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { EngineProvider } from "@/components/engine-context";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: { default: "MisconAI Studio", template: "%s · MisconAI" },
  description: "Diagnose programming misconceptions in student Python code with execution tracing, verification and taxonomy RAG.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <EngineProvider>
          <SiteHeader />
          <main className="mx-auto w-full max-w-7xl min-w-0 flex-1 px-4 py-8 sm:px-6 sm:py-10">{children}</main>
          <footer className="border-t border-line bg-surface">
            <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-5 text-xs text-subtle sm:flex-row sm:items-center sm:justify-between sm:px-6">
              <span>MisconAI · Enhanced Methodology — trace, verify, retrieve.</span>
              <span>Built on the open-source MCMiner framework · MIT License</span>
            </div>
          </footer>
        </EngineProvider>
      </body>
    </html>
  );
}
