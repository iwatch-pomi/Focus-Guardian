"""Tests for the time technical analysis engine."""

from datetime import datetime, timedelta, timezone

import pytest

from ..analysis.technical import TechnicalAnalyzer
from ..models.schemas import ActivityCategory


def _make_snap(
    i: int,
    category: str,
    focus_level: int = 3,
    base: datetime | None = None,
) -> dict:
    base = base or datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    return {
        "id": i,
        "captured_at": base + timedelta(minutes=i * 10),
        "activity_category": category,
        "focus_level": focus_level,
        "energy_focus": 60.0,
        "energy_fatigue": 40.0,
    }


class TestDrawdown:
    def test_single_drawdown(self) -> None:
        analyzer = TechnicalAnalyzer()
        snaps = [
            _make_snap(0, "deep_work", 5),
            _make_snap(1, "distracted", 1),
            _make_snap(2, "distracted", 1),
            _make_snap(3, "deep_work", 4),
        ]
        for s in snaps:
            analyzer.ingest(s)
        periods = analyzer.compute_drawdown_periods()
        assert len(periods) == 1
        assert periods[0].duration_minutes == 20  # 2 intervals × 10 min

    def test_no_drawdown_when_always_focused(self) -> None:
        analyzer = TechnicalAnalyzer()
        for i in range(5):
            analyzer.ingest(_make_snap(i, "deep_work", 5))
        assert analyzer.compute_drawdown_periods() == []


class TestVolatilityAlerts:
    def test_alert_on_distraction(self) -> None:
        analyzer = TechnicalAnalyzer()
        analyzer.ingest(_make_snap(0, "deep_work", 5))
        alerts = analyzer.ingest(_make_snap(1, "distracted", 1))
        assert len(alerts) == 1
        assert alerts[0].severity == "warning"

    def test_no_alert_on_break(self) -> None:
        analyzer = TechnicalAnalyzer()
        analyzer.ingest(_make_snap(0, "deep_work", 5))
        alerts = analyzer.ingest(_make_snap(1, "break", 2))
        assert alerts == []


class TestTimeStats:
    def test_efficiency_calculation(self) -> None:
        analyzer = TechnicalAnalyzer()
        base = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
        snaps = (
            [_make_snap(i, "deep_work", 5, base) for i in range(6)]
            + [_make_snap(i + 6, "distracted", 1, base) for i in range(2)]
        )
        for s in snaps:
            analyzer.ingest(s)
        stats = analyzer.compute_time_stats(base, base + timedelta(hours=2))
        assert stats.focus_efficiency_pct == pytest.approx(75.0)


class TestPredictions:
    def test_no_predictions_with_few_snaps(self) -> None:
        analyzer = TechnicalAnalyzer()
        for i in range(10):
            analyzer.ingest(_make_snap(i, "distracted", 1))
        assert analyzer.predict_risk_windows() == []

    def test_predicts_risky_hour(self) -> None:
        analyzer = TechnicalAnalyzer()
        base = datetime(2025, 1, 1, 14, 0, tzinfo=timezone.utc)  # 14:xx
        for i in range(25):
            cat = "distracted" if i % 2 == 0 else "deep_work"
            analyzer.ingest(_make_snap(i, cat, 3, base))
        warnings = analyzer.predict_risk_windows()
        assert len(warnings) > 0
