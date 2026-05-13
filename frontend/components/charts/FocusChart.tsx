"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import type { Snapshot } from "@/lib/api";
import { FOCUS_COLORS } from "@/lib/labels";

interface FocusChartProps {
  snapshots: Snapshot[];
}

export function FocusChart({ snapshots }: FocusChartProps) {
  const data = [...snapshots]
    .reverse()
    .map((s) => ({
      time: format(new Date(s.captured_at), "HH:mm", { locale: ja }),
      focus: s.focus_level,
      color: FOCUS_COLORS[s.focus_level],
    }));

  return (
    <div className="card">
      <h2 className="text-xs uppercase tracking-widest text-slate-500 mb-4">
        集中レベル推移
      </h2>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="focusGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34D399" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
          <XAxis dataKey="time" tick={{ fill: "#475569", fontSize: 10 }} />
          <YAxis domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fill: "#475569", fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: "#12121a", border: "1px solid #1e1e2e", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8" }}
            itemStyle={{ color: "#34D399" }}
          />
          <Area
            type="monotone"
            dataKey="focus"
            stroke="#34D399"
            strokeWidth={2}
            fill="url(#focusGrad)"
            dot={{ r: 3, fill: "#34D399" }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
