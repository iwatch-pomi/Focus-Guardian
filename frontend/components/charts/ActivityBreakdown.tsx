"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { Snapshot } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/labels";

interface ActivityBreakdownProps {
  snapshots: Snapshot[];
}

export function ActivityBreakdown({ snapshots }: ActivityBreakdownProps) {
  const counts: Record<string, number> = {};
  for (const s of snapshots) {
    counts[s.activity_category] = (counts[s.activity_category] ?? 0) + 1;
  }

  const data = Object.entries(counts).map(([cat, count]) => ({
    name: CATEGORY_LABELS[cat as keyof typeof CATEGORY_LABELS] ?? cat,
    value: count,
    color: CATEGORY_COLORS[cat as keyof typeof CATEGORY_COLORS] ?? "#9CA3AF",
  }));

  if (data.length === 0) {
    return (
      <div className="card text-center text-slate-600 py-10 text-sm">
        データがまだありません
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-xs uppercase tracking-widest text-slate-500 mb-4">
        行動内訳
      </h2>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            innerRadius={50}
            outerRadius={80}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#12121a", border: "1px solid #1e1e2e", borderRadius: 8 }}
            itemStyle={{ color: "#e2e8f0" }}
            formatter={(v: number) => [`${v} 回`, ""]}
          />
          <Legend
            formatter={(value) => (
              <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
