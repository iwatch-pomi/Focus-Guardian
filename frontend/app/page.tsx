import { Suspense } from "react";
import { api } from "@/lib/api";
import { StatCard } from "@/components/ui/StatCard";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { AvatarTimeline } from "@/components/avatar/AvatarTimeline";
import { FocusChart } from "@/components/charts/FocusChart";
import { ActivityBreakdown } from "@/components/charts/ActivityBreakdown";
import { EnergyGauge } from "@/components/charts/EnergyGauge";
import { FOCUS_COLORS } from "@/lib/labels";

async function fetchAll() {
  const [snapshots, avatarFrames, energy, stats, predictions] = await Promise.allSettled([
    api.snapshots(50),
    api.avatarTimeline(24),
    api.energy(),
    api.stats(8),
    api.predictions(),
  ]);

  return {
    snapshots: snapshots.status === "fulfilled" ? snapshots.value : [],
    avatarFrames: avatarFrames.status === "fulfilled" ? avatarFrames.value : [],
    energy: energy.status === "fulfilled" ? energy.value : null,
    stats: stats.status === "fulfilled" ? stats.value : null,
    predictions: predictions.status === "fulfilled" ? predictions.value : [],
  };
}

export const revalidate = 60; // ISR: refresh every 60s

export default async function Dashboard() {
  const { snapshots, avatarFrames, energy, stats, predictions } = await fetchAll();

  const latestFocusLevel =
    snapshots.length > 0 ? snapshots[0].focus_level : null;
  const focusColor = latestFocusLevel ? FOCUS_COLORS[latestFocusLevel] : "#9CA3AF";

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span style={{ color: focusColor }}>Focus</span> Guardian
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            ライフ・オペレーティングシステム — ローカル処理・プライバシー保護
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-500">稼働中</span>
        </div>
      </header>

      {/* Prediction warnings */}
      {predictions.length > 0 && <AlertBanner warnings={predictions} />}

      {/* Key stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="集中効率"
          value={stats ? `${stats.focus_efficiency_pct}` : "—"}
          unit="%"
          accent="#34D399"
          subtext="深い作業 / 総追跡時間"
        />
        <StatCard
          label="最大ドローダウン"
          value={stats ? stats.max_drawdown_minutes : "—"}
          unit="分"
          accent="#F97316"
          subtext="集中途切れ → 復帰の最長時間"
        />
        <StatCard
          label="ボラティリティ"
          value={stats ? stats.avg_volatility_score.toFixed(1) : "—"}
          unit="回/h"
          accent="#FCD34D"
          subtext="予定外コンテキスト切替"
        />
        <StatCard
          label="追跡スナップショット"
          value={snapshots.length}
          unit="件"
          accent="#93C5FD"
          subtext="直近50件"
        />
      </div>

      {/* Avatar timeline */}
      <AvatarTimeline frames={avatarFrames} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <FocusChart snapshots={snapshots} />
        </div>
        <EnergyGauge energy={energy} />
      </div>

      {/* Activity breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ActivityBreakdown snapshots={snapshots} />

        {/* Privacy notice */}
        <div className="card flex flex-col gap-3 justify-center">
          <h2 className="text-xs uppercase tracking-widest text-slate-500">
            プライバシー設計
          </h2>
          <ul className="text-xs text-slate-400 space-y-2">
            <li className="flex gap-2">
              <span className="text-emerald-400">✓</span>
              生画像はメモリ上のみで処理・即座に破棄
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-400">✓</span>
              PIRセンサーが人を検知した時のみカメラ起動
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-400">✓</span>
              ログは行動ラベル・アバターのみ保存
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-400">✓</span>
              全処理はローカルデバイス完結
            </li>
          </ul>
        </div>
      </div>

      <footer className="text-center text-xs text-slate-700 py-4">
        Focus Guardian v0.1.0 — すべてのデータはローカルに保存されます
      </footer>
    </main>
  );
}
