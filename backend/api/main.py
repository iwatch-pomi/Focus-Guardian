"""Focus Guardian — FastAPI application entry point."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.config import settings
from ..db.database import AsyncSessionLocal, EnergyLogORM, SnapshotORM, get_db, init_db
from ..models.schemas import (
    AvatarFrame,
    EnergySnapshot,
    SessionSummary,
    Snapshot,
    TimeStats,
    VolatilityAlert,
)
from ..privacy.processor import anonymize_to_pixel_art_state, focus_to_color
from ..sensing.snapshot import ActivityReading, SnapshotEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_current_session_id: str = str(uuid.uuid4())
_snapshot_engine: SnapshotEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    global _snapshot_engine
    _snapshot_engine = SnapshotEngine(on_snapshot=_persist_reading)
    await _snapshot_engine.start()
    yield
    if _snapshot_engine:
        await _snapshot_engine.stop()


app = FastAPI(
    title="Focus Guardian API",
    version="0.1.0",
    description="ローカルファーストの集中力管理ライフ・オペレーティングシステム",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _persist_reading(reading: ActivityReading) -> None:
    async with AsyncSessionLocal() as db:
        snap = SnapshotORM(
            session_id=_current_session_id,
            captured_at=reading.captured_at,
            activity_category=reading.activity_category,
            focus_level=reading.focus_level,
            confidence=reading.confidence,
            notes=reading.notes,
        )
        energy = EnergyLogORM(
            session_id=_current_session_id,
            measured_at=reading.captured_at,
            focus_score=reading.energy_focus,
            fatigue_score=reading.energy_fatigue,
            recommended_break=int(reading.energy_fatigue > 70 or reading.energy_focus < 30),
            estimated_optimal_work_minutes=max(5, min(90, int(reading.energy_focus * 0.9))),
        )
        db.add(snap)
        db.add(energy)
        await db.commit()
    logger.info(
        "Snapshot persisted: %s (focus=%d, conf=%.2f)",
        reading.activity_category,
        reading.focus_level,
        reading.confidence,
    )


DbDep = Annotated[AsyncSession, Depends(get_db)]


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "session_id": _current_session_id}


@app.get("/snapshots", response_model=list[Snapshot])
async def list_snapshots(db: DbDep, limit: int = 50) -> list[SnapshotORM]:
    result = await db.execute(
        select(SnapshotORM)
        .where(SnapshotORM.session_id == _current_session_id)
        .order_by(SnapshotORM.captured_at.desc())
        .limit(limit)
    )
    return result.scalars().all()  # type: ignore[return-value]


@app.get("/avatar/timeline", response_model=list[AvatarFrame])
async def avatar_timeline(db: DbDep, limit: int = 24) -> list[AvatarFrame]:
    """Return avatar states instead of raw images — privacy safe."""
    result = await db.execute(
        select(SnapshotORM)
        .where(SnapshotORM.session_id == _current_session_id)
        .order_by(SnapshotORM.captured_at.desc())
        .limit(limit)
    )
    snaps = result.scalars().all()
    return [
        AvatarFrame(
            timestamp=s.captured_at,
            activity_category=s.activity_category,  # type: ignore[arg-type]
            focus_level=s.focus_level,  # type: ignore[arg-type]
            pixel_art_state=anonymize_to_pixel_art_state(s.activity_category, s.focus_level),
            color_theme=focus_to_color(s.focus_level),
        )
        for s in snaps
    ]


@app.get("/energy/current", response_model=EnergySnapshot | None)
async def current_energy(db: DbDep) -> EnergyLogORM | None:
    result = await db.execute(
        select(EnergyLogORM)
        .where(EnergyLogORM.session_id == _current_session_id)
        .order_by(EnergyLogORM.measured_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return EnergySnapshot(  # type: ignore[return-value]
        measured_at=row.measured_at,
        focus_score=row.focus_score,
        fatigue_score=row.fatigue_score,
        recommended_break=bool(row.recommended_break),
        estimated_optimal_work_minutes=row.estimated_optimal_work_minutes,
    )


@app.get("/analysis/stats", response_model=TimeStats)
async def time_stats(db: DbDep, hours: int = 8) -> TimeStats:
    from ..analysis.technical import TechnicalAnalyzer

    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=hours)

    result = await db.execute(
        select(SnapshotORM)
        .where(
            SnapshotORM.session_id == _current_session_id,
            SnapshotORM.captured_at >= period_start,
        )
        .order_by(SnapshotORM.captured_at.asc())
    )
    snaps = result.scalars().all()

    analyzer = TechnicalAnalyzer()
    for s in snaps:
        analyzer.ingest(
            {
                "id": s.id,
                "captured_at": s.captured_at,
                "activity_category": s.activity_category,
                "focus_level": s.focus_level,
                "energy_focus": 50.0,
                "energy_fatigue": 50.0,
            }
        )
    return analyzer.compute_time_stats(period_start, period_end)


@app.get("/analysis/predictions", response_model=list)
async def predictions(db: DbDep) -> list:
    from ..analysis.technical import TechnicalAnalyzer

    result = await db.execute(
        select(SnapshotORM)
        .where(SnapshotORM.session_id == _current_session_id)
        .order_by(SnapshotORM.captured_at.asc())
    )
    snaps = result.scalars().all()

    analyzer = TechnicalAnalyzer()
    for s in snaps:
        analyzer.ingest(
            {
                "id": s.id,
                "captured_at": s.captured_at,
                "activity_category": s.activity_category,
                "focus_level": s.focus_level,
                "energy_focus": 50.0,
                "energy_fatigue": 50.0,
            }
        )
    return [w.model_dump() for w in analyzer.predict_risk_windows()]


@app.post("/snapshot/manual", response_model=dict)
async def trigger_manual_snapshot() -> dict:
    """Manually trigger a snapshot (for testing / on-demand capture)."""
    if _snapshot_engine is None:
        raise HTTPException(status_code=503, detail="Snapshot engine not running")
    await _snapshot_engine._capture_and_analyze()
    return {"status": "triggered", "session_id": _current_session_id}
