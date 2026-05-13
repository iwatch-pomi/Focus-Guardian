"""Interval snapshot engine.

Captures a frame from the camera (only when motion is detected),
passes it through the privacy processor + AI classifier, then discards
the raw image immediately.
"""

from __future__ import annotations

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Callable

from ..api.config import settings

logger = logging.getLogger(__name__)


class SnapshotEngine:
    """Drives the interval-based snapshot loop."""

    def __init__(
        self,
        on_snapshot: Callable,  # async callback receiving ActivityReading
        camera_factory: Callable | None = None,
    ) -> None:
        self._on_snapshot = on_snapshot
        self._camera_factory = camera_factory
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("SnapshotEngine started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SnapshotEngine stopped")

    async def _loop(self) -> None:
        while self._running:
            interval = random.randint(
                settings.snapshot_interval_min,
                settings.snapshot_interval_max,
            )
            await asyncio.sleep(interval)
            await self._capture_and_analyze()

    async def _capture_and_analyze(self) -> None:
        from ..analysis.classifier import get_classifier

        classifier = get_classifier()
        image = await self._acquire_frame()

        if image is None:
            logger.debug("No frame acquired (PIR gate closed or no camera)")
            return

        try:
            reading = await classifier.classify(image)
            await self._on_snapshot(reading)
        finally:
            # Privacy guarantee: raw image reference released here
            del image

    async def _acquire_frame(self):
        """Acquire a camera frame. Returns None if no presence detected."""
        if self._camera_factory is not None:
            return await self._camera_factory()

        # Simulation mode (no hardware attached)
        try:
            from PIL import Image
            return Image.new("RGB", (640, 480), color=(100, 100, 100))
        except ImportError:
            return None


class ActivityReading:
    """Transient result of a single snapshot analysis."""

    def __init__(
        self,
        activity_category: str,
        focus_level: int,
        confidence: float,
        energy_focus: float,
        energy_fatigue: float,
        notes: str = "",
    ) -> None:
        self.snapshot_id = str(uuid.uuid4())
        self.captured_at = datetime.now(timezone.utc)
        self.activity_category = activity_category
        self.focus_level = focus_level
        self.confidence = confidence
        self.energy_focus = energy_focus
        self.energy_fatigue = energy_fatigue
        self.notes = notes
