import Link from "next/link";

const roadmapItems = [
  "Shipped: live idea submission, multi-step analysis pipeline, result cards, scoring radar, and public frontend.",
  "Shipped: real-time search-backed analysis with structured outputs, cached results, and background polling.",
  "Next: sharper explanations, more reliable structured responses, and side-by-side idea comparisons.",
  "Next: public contribution docs, cleaner deployment pipeline, and expanded external testing.",
];

const contributionItems = [
  "Code — frontend polish, backend reliability, structured output handling, and test coverage.",
  "Feedback — use it on a real idea and tell us what the analysis got wrong or missed.",
  "Distribution — incubators, accelerators, research communities, or founder networks who want to plug this in.",
];

export default function AboutPage() {
  return (
    <main className="relative overflow-x-clip px-4 py-10 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute left-0 top-24 h-64 w-64 rounded-full bg-emerald-400/10 blur-3xl" />
        <div className="absolute right-0 top-40 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-5xl space-y-6">
        <header className="rounded-3xl border border-slate-300/15 bg-slate-950/55 p-6 backdrop-blur md:p-9">
          <p className="mb-3 inline-flex rounded-full border border-emerald-400/40 bg-emerald-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-300">
            Open Project
          </p>
          <h1 className="text-3xl font-semibold leading-tight text-slate-50 md:text-5xl">
            Idea Stress-Test Engine
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300 md:text-base">
            Real-time, search-grounded analysis of business ideas — across
            market demand, competitive pressure, monetization fit, and failure
            risk. Built for founders who want signal, not reassurance.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              href="/"
              className="rounded-full border border-slate-200/15 bg-slate-900/50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-200 transition hover:border-emerald-300/40 hover:text-emerald-200"
            >
              Back to app
            </Link>
            <a
              href="#contributions"
              className="rounded-full border border-cyan-300/25 bg-cyan-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-cyan-100 transition hover:border-cyan-200/45 hover:bg-cyan-400/15"
            >
              Contribution guide
            </a>
          </div>
        </header>

        <div className="grid gap-5 md:grid-cols-2">
          <section
            id="what-this-is"
            className="rounded-3xl border border-slate-300/15 bg-[rgba(7,14,22,0.82)] p-6 backdrop-blur"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              What this is
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-50">
              Structured pressure-testing before you commit.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Most idea feedback is opinion. This runs your concept through a
              structured analysis pipeline grounded in live search data —
              surfacing real market signals, competitive blind spots, and
              monetization friction before you invest time or capital.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              Free to use. Limit: 2 analyses per device per day.
            </p>
          </section>

          <section
            id="contributions"
            className="rounded-3xl border border-slate-300/15 bg-[rgba(7,14,22,0.82)] p-6 backdrop-blur"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Contribute
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-50">
              Fork it. Improve it. Ship it.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              The repo is open. Pull requests are welcome. If you find a way to
              make the analysis sharper, the output cleaner, or the pipeline
              faster — open a PR or reach out directly.
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-300">
              {contributionItems.map((item) => (
                <li
                  key={item}
                  className="rounded-2xl border border-slate-300/10 bg-slate-950/45 px-4 py-3"
                >
                  {item}
                </li>
              ))}
            </ul>
          </section>

          <section
            id="progress"
            className="rounded-3xl border border-slate-300/15 bg-[rgba(7,14,22,0.82)] p-6 backdrop-blur"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Progress
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-50">
              What is built and what is next.
            </h2>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-300">
              {roadmapItems.map((item) => (
                <li
                  key={item}
                  className="rounded-2xl border border-slate-300/10 bg-slate-950/45 px-4 py-3"
                >
                  {item}
                </li>
              ))}
            </ul>
          </section>

          <section
            id="support"
            className="rounded-3xl border border-emerald-300/20 bg-gradient-to-br from-emerald-400/12 to-cyan-400/12 p-6"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-200/90">
              Participation
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-50">
              Feedback and improvements are welcome.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-200/90">
              The project is public so contributors can improve the analysis
              quality, tighten the product experience, and make deployment
              easier for the next person who clones it.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-slate-200/90">
              If you want to help, start with documentation fixes, bug reports,
              tests, or targeted pull requests.
            </p>
            <a
              href="#contributions"
              className="mt-4 block text-xl font-semibold text-emerald-300 break-all transition hover:text-emerald-200"
            >
              Start with the contribution guide
            </a>
          </section>
        </div>
      </section>
    </main>
  );
}
