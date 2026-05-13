import type { ActivityCategory } from "./api";

export const CATEGORY_LABELS: Record<ActivityCategory, string> = {
  deep_work: "深い集中",
  shallow_work: "浅い作業",
  communication: "コミュニケーション",
  break: "休憩",
  distracted: "脱線",
  away: "離席",
  unknown: "不明",
};

export const CATEGORY_COLORS: Record<ActivityCategory, string> = {
  deep_work: "#34D399",
  shallow_work: "#60A5FA",
  communication: "#A78BFA",
  break: "#93C5FD",
  distracted: "#F97316",
  away: "#6B7280",
  unknown: "#9CA3AF",
};

export const FOCUS_LABELS: Record<number, string> = {
  5: "ピーク集中",
  4: "高集中",
  3: "普通",
  2: "低集中",
  1: "最低限",
};

export const FOCUS_COLORS: Record<number, string> = {
  5: "#6EE7B7",
  4: "#34D399",
  3: "#FCD34D",
  2: "#F97316",
  1: "#EF4444",
};

export const AVATAR_STATE_EMOJI: Record<string, string> = {
  sitting_peak_glow: "🧘",
  sitting_focused: "💻",
  sitting_neutral: "🪑",
  sitting_typing: "⌨️",
  sitting_browsing: "👀",
  sitting_talking: "🗣️",
  standing_stretch: "🧍",
  reclining: "😴",
  sitting_phone: "📱",
  slouching: "😩",
  empty_desk: "🪑",
};
