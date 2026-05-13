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
        # OpenCV（Windows / Linux / Mac 共通）を優先して試みる
        try:
            import cv2
            from PIL import Image

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("No camera found via OpenCV")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
            ret, frame = cap.read()
            cap.release()
            if not ret:
                raise RuntimeError("OpenCV frame capture failed")
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        except ImportError:
            pass  # opencv-python 未インストール → picamera2 を試みる
        except Exception as exc:
            logger.warning("OpenCV capture failed: %s — trying picamera2", exc)

        # Raspberry Pi 向け fallback
        try:
            import time
            from picamera2 import Picamera2
            from PIL import Image

            cam = Picamera2()
            cam.configure(cam.create_still_configuration(main={"size": self._resolution}))
            cam.start()
            time.sleep(0.5)
            frame = cam.capture_array()
            cam.stop()
            cam.close()
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
