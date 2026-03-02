import Link from "next/link";
import type { Metadata } from "next";
import UsageTracker from "@/components/UsageTracker";
import "./globals.css";

export const metadata: Metadata = {
  title: "Idea Stress-Test Engine",
  description: "Multi-agent AI analysis for your business idea.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="flex min-h-screen flex-col">
          <UsageTracker />
          <div className="flex-1">{children}</div>
          <footer className="border-t border-slate-300/10 bg-slate-950/55 px-4 py-6 backdrop-blur sm:px-6 lg:px-8">
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 text-sm text-slate-300 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Project Info
                </p>
                <Link
                  href="/about#contributions"
                  className="font-medium text-emerald-300 transition hover:text-emerald-200"
                >
                  Contribution guide
                </Link>
              </div>

              <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-300">
                <Link href="/about#contributions" className="transition hover:text-emerald-300">
                  Contribute
                </Link>
                <Link href="/about#progress" className="transition hover:text-emerald-300">
                  Progress
                </Link>
                <Link href="/about#support" className="transition hover:text-emerald-300">
                  Support
                </Link>
                <Link href="/privacy" className="transition hover:text-emerald-300">
                  Privacy
                </Link>
              </nav>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
