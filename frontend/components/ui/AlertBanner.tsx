"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import type { PredictionWarning } from "@/lib/api";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

interface AlertBannerProps {
  warnings: PredictionWarning[];
}

export function AlertBanner({ warnings }: AlertBannerProps) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const visible = warnings.filter((w) => !dismissed.has(w.prediction_id));
  if (visible.length === 0) return null;

  const top = visible[0];

  return (
    <div className="rounded-xl border border-orange-500/40 bg-orange-500/10 px-4 py-3 flex items-start gap-3">
      <AlertTriangle className="text-orange-400 mt-0.5 shrink-0" size={18} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-orange-300">{top.pattern_description}</p>
        <p className="text-xs text-slate-500 mt-0.5">
          リスク窓:{" "}
          {format(new Date(top.risk_window_start), "HH:mm", { locale: ja })} –{" "}
          {format(new Date(top.risk_window_end), "HH:mm", { locale: ja })}
          {"　"}リスクスコア: {Math.round(top.risk_score * 100)}%
        </p>
      </div>
      <button
        onClick={() => setDismissed((prev) => new Set([...prev, top.prediction_id]))}
        className="text-slate-600 hover:text-slate-400 transition-colors"
      >
        <X size={16} />
      </button>
    </div>
  );
}
