"""Time technical analysis engine.

Implements:
- タイムドローダウン (Time Drawdown): time elapsed between focus loss and recovery
- ボラティリティ (Volatility): rate of unexpected context switches
- エネルギーマッピング (Energy Mapping): focus/fatigue scoring over time
- 未来予測 (Prediction): risk window detection from historical patterns
"""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone

from ..models.schemas import (
    ActivityCategory,
    DrawdownPeriod,
    EnergySnapshot,
    FocusPeriod,
    PredictionWarning,
    TimeStats,
    VolatilityAlert,
)

_FOCUS_CATEGORIES = {ActivityCategory.DEEP_WORK, ActivityCategory.SHALLOW_WORK}
_DISTRACTION_CATEGORIES = {ActivityCategory.DISTRACTED}

_HIGH_VOLATILITY_THRESHOLD = 3  # context switches per 30-min window


class TechnicalAnalyzer:
    """Stateful analyzer — feed snapshots incrementally via `ingest`."""

    def __init__(self) -> None:
        self._snapshots: list[dict] = []
        self._current_drawdown_start: datetime | None = None
        self._current_category: ActivityCategory = ActivityCategory.UNKNOWN

    def ingest(self, snapshot: dict) -> list[VolatilityAlert]:
        """Add a new snapshot and return any volatility alerts triggered."""
        self._snapshots.append(snapshot)
        alerts: list[VolatilityAlert] = []

        cat = ActivityCategory(snapshot["activity_category"])
        prev = self._current_category

        # Drawdown tracking
        if prev in _FOCUS_CATEGORIES and cat not in _FOCUS_CATEGORIES:
            self._current_drawdown_start = snapshot["captured_at"]
        elif prev not in _FOCUS_CATEGORIES and cat in _FOCUS_CATEGORIES:
            self._current_drawdown_start = None

        # Volatility alert: unexpected switch into distraction
        if prev in _FOCUS_CATEGORIES and cat in _DISTRACTION_CATEGORIES:
            alert = VolatilityAlert(
                alert_id=f"vol_{snapshot['id']}",
                triggered_at=snapshot["captured_at"],
                previous_category=prev,
                current_category=cat,
                message="集中が途切れました — 脱線を検知しました",
                severity="warning",
            )
            alerts.append(alert)

        self._current_category = cat
        return alerts

    def compute_drawdown_periods(self) -> list[DrawdownPeriod]:
        """Identify all drawdown windows from the snapshot history."""
        periods: list[DrawdownPeriod] = []
        in_drawdown = False
        drawdown_start: datetime | None = None
        trigger: ActivityCategory = ActivityCategory.UNKNOWN

        for snap in self._snapshots:
            cat = ActivityCategory(snap["activity_category"])
            if not in_drawdown and cat not in _FOCUS_CATEGORIES:
                in_drawdown = True
                drawdown_start = snap["captured_at"]
                trigger = cat
            elif in_drawdown and cat in _FOCUS_CATEGORIES:
                end = snap["captured_at"]
                assert drawdown_start is not None
                duration = int((end - drawdown_start).total_seconds() / 60)
                periods.append(
                    DrawdownPeriod(
                        start=drawdown_start,
                        end=end,
                        duration_minutes=duration,
                        trigger_category=trigger,
                    )
                )
                in_drawdown = False

        # Open drawdown (not yet recovered)
        if in_drawdown and drawdown_start:
            now = datetime.now(timezone.utc)
            duration = int((now - drawdown_start).total_seconds() / 60)
            periods.append(
                DrawdownPeriod(
                    start=drawdown_start,
                    end=None,
                    duration_minutes=duration,
                    trigger_category=trigger,
                )
            )
        return periods

    def compute_focus_periods(self) -> list[FocusPeriod]:
        periods: list[FocusPeriod] = []
        in_focus = False
        focus_start: datetime | None = None
        focus_levels: list[int] = []

        for snap in self._snapshots:
            cat = ActivityCategory(snap["activity_category"])
            if not in_focus and cat in _FOCUS_CATEGORIES:
                in_focus = True
                focus_start = snap["captured_at"]
                focus_levels = [snap["focus_level"]]
            elif in_focus:
                if cat in _FOCUS_CATEGORIES:
                    focus_levels.append(snap["focus_level"])
                else:
                    end = snap["captured_at"]
                    assert focus_start is not None
                    duration = int((end - focus_start).total_seconds() / 60)
                    periods.append(
                        FocusPeriod(
                            start=focus_start,
                            end=end,
                            duration_minutes=duration,
                            avg_focus_level=statistics.mean(focus_levels),
                        )
                    )
                    in_focus = False

        return periods

    def compute_energy_snapshot(self) -> EnergySnapshot | None:
        if not self._snapshots:
            return None
        recent = self._snapshots[-5:]  # last 5 readings
        avg_focus = statistics.mean(s.get("energy_focus", 50.0) for s in recent)
        avg_fatigue = statistics.mean(s.get("energy_fatigue", 50.0) for s in recent)
        recommended_break = avg_fatigue > 70.0 or avg_focus < 30.0
        optimal_minutes = max(5, min(90, int(avg_focus * 0.9)))
        return EnergySnapshot(
            measured_at=datetime.now(timezone.utc),
            focus_score=round(avg_focus, 1),
            fatigue_score=round(avg_fatigue, 1),
            recommended_break=recommended_break,
            estimated_optimal_work_minutes=optimal_minutes,
        )

    def compute_time_stats(self, period_start: datetime, period_end: datetime) -> TimeStats:
        window = [
            s for s in self._snapshots if period_start <= s["captured_at"] <= period_end
        ]
        if not window:
            return TimeStats(
                period_start=period_start,
                period_end=period_end,
                max_drawdown_minutes=0,
                avg_volatility_score=0.0,
                total_focus_minutes=0,
                focus_efficiency_pct=0.0,
                benchmark_percentile=None,
            )

        drawdowns = self.compute_drawdown_periods()
        max_dd = max((d.duration_minutes or 0 for d in drawdowns), default=0)

        # Volatility = context switches per hour
        switches = sum(
            1 for i in range(1, len(window))
            if window[i]["activity_category"] != window[i - 1]["activity_category"]
        )
        hours = max(1, int((period_end - period_start).total_seconds() / 3600))
        volatility = switches / hours

        total_tracked = len(window)
        deep_work_count = sum(
            1 for s in window if s["activity_category"] == ActivityCategory.DEEP_WORK.value
        )
        efficiency = (deep_work_count / total_tracked * 100) if total_tracked else 0.0

        return TimeStats(
            period_start=period_start,
            period_end=period_end,
            max_drawdown_minutes=max_dd,
            avg_volatility_score=round(volatility, 2),
            total_focus_minutes=total_tracked * 10,  # ~10 min per interval
            focus_efficiency_pct=round(efficiency, 1),
            benchmark_percentile=None,  # populated by benchmark service
        )

    def predict_risk_windows(self) -> list[PredictionWarning]:
        """Simple hour-of-day pattern model: flag hours with high historical distraction."""
        import uuid

        if len(self._snapshots) < 20:
            return []

        hour_distraction: Counter[int] = Counter()
        hour_total: Counter[int] = Counter()
        for snap in self._snapshots:
            h = snap["captured_at"].hour
            hour_total[h] += 1
            if snap["activity_category"] in (
                ActivityCategory.DISTRACTED.value,
                ActivityCategory.AWAY.value,
            ):
                hour_distraction[h] += 1

        warnings: list[PredictionWarning] = []
        now = datetime.now(timezone.utc)
        for h, total in hour_total.items():
            if total < 3:
                continue
            risk = hour_distraction[h] / total
            if risk > 0.5:
                window_start = now.replace(hour=h, minute=0, second=0, microsecond=0)
                warnings.append(
                    PredictionWarning(
                        prediction_id=str(uuid.uuid4()),
                        predicted_at=now,
                        risk_window_start=window_start,
                        risk_window_end=window_start + timedelta(hours=1),
                        risk_score=round(risk, 2),
                        pattern_description=f"{h}時台は過去に集中が途切れやすい傾向があります",
                    )
                )
        return sorted(warnings, key=lambda w: w.risk_score, reverse=True)
