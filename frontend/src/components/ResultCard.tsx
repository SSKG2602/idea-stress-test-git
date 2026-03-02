interface Props {
  title: string;
  children: React.ReactNode;
}

export default function ResultCard({ title, children }: Props) {
  return (
    <div className="rounded-2xl border border-slate-300/15 bg-[rgba(8,14,22,0.8)] p-5 shadow-[0_10px_30px_rgba(2,6,23,0.32)] backdrop-blur space-y-3">
      <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-300">{title}</h2>
      {children}
    </div>
  );
}
