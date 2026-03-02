import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="relative overflow-x-clip px-4 py-10 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 opacity-50">
        <div className="absolute left-10 top-24 h-64 w-64 rounded-full bg-cyan-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-4xl space-y-6">
        <header className="rounded-3xl border border-slate-300/15 bg-slate-950/55 p-6 backdrop-blur md:p-9">
          <p className="mb-3 inline-flex rounded-full border border-slate-300/20 bg-slate-900/50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-300">
            Privacy
          </p>
          <h1 className="text-3xl font-semibold leading-tight text-slate-50 md:text-5xl">
            Privacy
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300 md:text-base">
            This project is still evolving. Treat submitted ideas as product input to a public beta
            style system, and avoid entering highly sensitive confidential information.
          </p>
        </header>

        <section className="rounded-3xl border border-slate-300/15 bg-[rgba(7,14,22,0.82)] p-6 backdrop-blur">
          <div className="space-y-4 text-sm leading-relaxed text-slate-300">
            <p>
              Submitted idea text may be processed through the application backend and external model
              providers in order to generate analysis results.
            </p>
            <p>
              The project should be treated as an early public product experience, not as a secure
              document vault for sensitive company information.
            </p>
            <p>
              For privacy-related questions or contribution discussions, review
              the{" "}
              <Link href="/about#contributions" className="font-medium text-emerald-300 hover:text-emerald-200">
                contribution guide
              </Link>
              {" "}and avoid submitting sensitive information.
            </p>
          </div>
          <div className="mt-6">
            <Link
              href="/about"
              className="rounded-full border border-slate-200/15 bg-slate-900/50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-200 transition hover:border-emerald-300/40 hover:text-emerald-200"
            >
              Back to about
            </Link>
          </div>
        </section>
      </section>
    </main>
  );
}
