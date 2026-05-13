/**
 * Focus Guardian API client.
 *
 * Always calls /api/v1/* (relative URL).
 * - Local dev:  Next.js rewrites to http://localhost:8000/api/v1/*
 * - Vercel:     vercel.json routes to the Python serverless function
 */

const BASE = "/api/v1";

export type ActivityCategory =
  | "deep_work"
  | "shallow_work"
  | "communication"
  | "break"
  | "distracted"
  | "away"
  | "unknown";

export type FocusLevel = 1 | 2 | 3 | 4 | 5;

export interface Snapshot {
  id: number;
  session_id: string;
  captured_at: string;
  activity_category: ActivityCategory;
  focus_level: FocusLevel;
  confidence: number;
  notes: string;
}

export interface AvatarFrame {
  timestamp: string;
  activity_category: ActivityCategory;
  focus_level: FocusLevel;
  pixel_art_state: string;
  color_theme: string;
}

export interface EnergySnapshot {
  measured_at: string;
  focus_score: number;
  fatigue_score: number;
  recommended_break: boolean;
  estimated_optimal_work_minutes: number;
}

export interface TimeStats {
  period_start: string;
  period_end: string;
  max_drawdown_minutes: number;
  avg_volatility_score: number;
  total_focus_minutes: number;
  focus_efficiency_pct: number;
  benchmark_percentile: number | null;
}

export interface PredictionWarning {
  prediction_id: string;
  predicted_at: string;
  risk_window_start: string;
  risk_window_end: string;
  risk_score: number;
  pattern_description: string;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  snapshots: (limit = 50) => get<Snapshot[]>(`/snapshots?limit=${limit}`),
  avatarTimeline: (limit = 24) => get<AvatarFrame[]>(`/avatar/timeline?limit=${limit}`),
  energy: () => get<EnergySnapshot | null>("/energy/current"),
  stats: (hours = 8) => get<TimeStats>(`/analysis/stats?hours=${hours}`),
  predictions: () => get<PredictionWarning[]>("/analysis/predictions"),
  triggerSnapshot: () =>
    fetch(`${BASE}/snapshot/manual`, { method: "POST" }).then((r) => r.json()),
};
