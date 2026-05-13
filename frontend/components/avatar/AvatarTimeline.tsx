"use client";

import { format } from "date-fns";
import { ja } from "date-fns/locale";
import type { AvatarFrame } from "@/lib/api";
import { AVATAR_STATE_EMOJI, CATEGORY_LABELS, FOCUS_LABELS } from "@/lib/labels";

interface AvatarTimelineProps {
  frames: AvatarFrame[];
}

export function AvatarTimeline({ frames }: AvatarTimelineProps) {
  if (frames.length === 0) {
    return (
      <div className="card text-center text-slate-600 py-10 text-sm">
        スナップショットがまだありません
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-xs uppercase tracking-widest text-slate-500 mb-4">
        アバタータイムライン（プライバシー保護済み）
      </h2>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {frames.map((frame) => (
          <AvatarCell key={frame.timestamp} frame={frame} />
        ))}
      </div>
    </div>
  );
}

function AvatarCell({ frame }: { frame: AvatarFrame }) {
  const emoji = AVATAR_STATE_EMOJI[frame.pixel_art_state] ?? "🪑";
  const time = format(new Date(frame.timestamp), "HH:mm", { locale: ja });

  return (
    <div className="flex flex-col items-center gap-1 shrink-0 w-16">
      {/* Pixel avatar block */}
      <div
        className="w-14 h-14 rounded-lg flex items-center justify-center text-2xl
                   border-2 transition-all duration-300"
        style={{
          borderColor: frame.color_theme,
          boxShadow: `0 0 12px ${frame.color_theme}44`,
          backgroundColor: `${frame.color_theme}15`,
        }}
        title={`${CATEGORY_LABELS[frame.activity_category]} — ${FOCUS_LABELS[frame.focus_level]}`}
      >
        {emoji}
      </div>
      <span className="text-xs text-slate-600 tabular-nums">{time}</span>
      {/* Focus dot */}
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: frame.color_theme }}
      />
    </div>
  );
}
