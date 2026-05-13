import { clsx } from "clsx";

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  accent?: string;
  subtext?: string;
}

export function StatCard({ label, value, unit, accent = "#34D399", subtext }: StatCardProps) {
  return (
    <div className="card flex flex-col gap-1">
      <span className="text-xs text-slate-500 uppercase tracking-widest">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className="stat-value" style={{ color: accent }}>
          {value}
        </span>
        {unit && <span className="text-sm text-slate-500">{unit}</span>}
      </div>
      {subtext && <span className="text-xs text-slate-600 mt-1">{subtext}</span>}
    </div>
  );
}
