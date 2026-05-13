"""Camera controller with physical privacy shutter support.

Integrates PIR gating: the camera is opened only when the PIR sensor reports
human presence, ensuring no frames are captured in an empty room.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from .pir_sensor import PIRSensor

if TYPE_CHECKING:
    from PIL.Image import Image

logger = logging.getLogger(__name__)


class PrivacyCamera:
    """Camera with PIR-gated capture and immediate-discard semantics."""

    def __init__(
        self,
        pir: PIRSensor | None = None,
        resolution: tuple[int, int] = (640, 480),
        simulation: bool = False,
    ) -> None:
        self._pir = pir or PIRSensor(simulation=simulation)
        self._resolution = resolution
        self._simulation = simulation

    async def capture(self) -> "Image | None":
        """Capture a frame only if a person is detected.

        Returns None when the PIR gate is closed (no presence).
        The returned Image object lives in memory only — callers must del it
        after use and must NOT write it to disk.
        """
        if not self._pir.is_present():
            logger.debug("PIR gate closed — skipping capture")
            return None

        if self._simulation:
            return self._simulate_frame()

        return await asyncio.to_thread(self._capture_hardware)

    def _capture_hardware(self) -> "Image | None":
        try:
            from picamera2 import Picamera2

            cam = Picamera2()
            config = cam.create_still_configuration(
                main={"size": self._resolution}
            )
            cam.configure(config)
            cam.start()
            import time
            time.sleep(0.5)  # warm-up
            frame = cam.capture_array()
            cam.stop()
            cam.close()

            from PIL import Image
            return Image.fromarray(frame)
        except Exception as exc:
            logger.error("Hardware capture failed: %s", exc)
            return None

    def _simulate_frame(self) -> "Image":
        import random
        from PIL import Image, ImageDraw

        img = Image.new("RGB", self._resolution, color=(
            random.randint(80, 120),
            random.randint(80, 120),
            random.randint(80, 120),
        ))
        draw = ImageDraw.Draw(img)
        # Draw a rough desk silhouette for simulation
        w, h = self._resolution
        draw.rectangle([w // 4, h // 2, 3 * w // 4, h], fill=(60, 60, 60))
        draw.ellipse([w // 3, h // 4, 2 * w // 3, h // 2], fill=(200, 180, 160))
        return img
