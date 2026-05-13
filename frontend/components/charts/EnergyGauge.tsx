"use client";

import type { EnergySnapshot } from "@/lib/api";

interface EnergyGaugeProps {
  energy: EnergySnapshot | null;
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span style={{ color }}>{Math.round(value)}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function EnergyGauge({ energy }: EnergyGaugeProps) {
  if (!energy) {
    return (
      <div className="card text-center text-slate-600 py-6 text-sm">
        エネルギーデータなし
      </div>
    );
  }

  return (
    <div className="card flex flex-col gap-4">
      <h2 className="text-xs uppercase tracking-widest text-slate-500">
        エネルギーマッピング
      </h2>
      <Bar label="集中スコア" value={energy.focus_score} color="#34D399" />
      <Bar label="疲労スコア" value={energy.fatigue_score} color="#F97316" />

      <div className="mt-1 p-3 rounded-lg border border-slate-800 bg-slate-900/40 text-xs">
        {energy.recommended_break ? (
          <p className="text-orange-400">
            ⚠️ 休憩を推奨します —{" "}
            <span className="text-slate-400">疲労が高まっています</span>
          </p>
        ) : (
          <p className="text-emerald-400">
            ✓ 継続OK —{" "}
            <span className="text-slate-400">
              推定集中維持: {energy.estimated_optimal_work_minutes}分
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
