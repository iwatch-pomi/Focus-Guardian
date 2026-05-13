"""Pydantic schemas for Focus Guardian data models."""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field


class ActivityCategory(str, enum.Enum):
    DEEP_WORK = "deep_work"        # 深い集中作業
    SHALLOW_WORK = "shallow_work"  # メール・雑務
    COMMUNICATION = "communication"
    BREAK = "break"
    DISTRACTED = "distracted"      # 脱線
    AWAY = "away"                  # 離席
    UNKNOWN = "unknown"


class FocusLevel(int, enum.Enum):
    PEAK = 5       # ピーク集中
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


class SnapshotBase(BaseModel):
    captured_at: datetime
    activity_category: ActivityCategory
    focus_level: FocusLevel
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""


class SnapshotCreate(SnapshotBase):
    pass


class Snapshot(SnapshotBase):
    id: int
    session_id: str

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    session_id: str
    date: datetime
    total_tracked_minutes: int
    deep_work_minutes: int
    distracted_minutes: int
    break_minutes: int
    peak_focus_periods: list[FocusPeriod]
    drawdown_periods: list[DrawdownPeriod]
    energy_score: float = Field(ge=0.0, le=100.0)


class FocusPeriod(BaseModel):
    start: datetime
    end: datetime
    duration_minutes: int
    avg_focus_level: float


class DrawdownPeriod(BaseModel):
    """集中が途切れてから復帰するまでの停滞時間。"""
    start: datetime
    end: datetime | None
    duration_minutes: int | None
    trigger_category: ActivityCategory


class VolatilityAlert(BaseModel):
    """予定外の行動（脱線）をリアルタイムで通知。"""
    alert_id: str
    triggered_at: datetime
    previous_category: ActivityCategory
    current_category: ActivityCategory
    message: str
    severity: str = Field(pattern="^(info|warning|critical)$")


class EnergySnapshot(BaseModel):
    """姿勢・音から推定した集中度・疲労度。"""
    measured_at: datetime
    focus_score: float = Field(ge=0.0, le=100.0)
    fatigue_score: float = Field(ge=0.0, le=100.0)
    recommended_break: bool
    estimated_optimal_work_minutes: int


class PredictionWarning(BaseModel):
    """過去パターンから浪費が発生しそうな時間帯を事前警告。"""
    prediction_id: str
    predicted_at: datetime
    risk_window_start: datetime
    risk_window_end: datetime
    risk_score: float = Field(ge=0.0, le=1.0)
    pattern_description: str


class AvatarFrame(BaseModel):
    """生画像の代わりに表示するアバター状態。"""
    timestamp: datetime
    activity_category: ActivityCategory
    focus_level: FocusLevel
    pixel_art_state: str  # アバター状態コード (e.g., "sitting_focused", "slouching")
    color_theme: str      # HEX カラー (集中度に応じて変化)


class TimeStats(BaseModel):
    """タイムテクニカル分析サマリー。"""
    period_start: datetime
    period_end: datetime
    max_drawdown_minutes: int
    avg_volatility_score: float
    total_focus_minutes: int
    focus_efficiency_pct: float  # deep_work / total_tracked * 100
    benchmark_percentile: float | None  # 匿名ベンチマーク比較
