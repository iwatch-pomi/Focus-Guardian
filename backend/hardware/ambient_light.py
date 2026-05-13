"""Ambient light controller.

Maps focus state to RGB LED color, providing non-intrusive status feedback.

Focus level colors (mirrors frontend palette):
  5 - Peak focus   → Emerald green  #6EE7B7
  4 - High focus   → Green          #34D399
  3 - Medium       → Amber          #FCD34D
  2 - Low          → Orange         #F97316
  1 - Minimal      → Red            #EF4444
  away / break     → Dim blue       #93C5FD
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_FOCUS_COLOR_MAP: dict[int, tuple[int, int, int]] = {
    5: (110, 231, 183),  # #6EE7B7
    4: (52, 211, 153),   # #34D399
    3: (252, 211, 77),   # #FCD34D
    2: (249, 115, 22),   # #F97316
    1: (239, 68, 68),    # #EF4444
}
_BREAK_COLOR: tuple[int, int, int] = (147, 197, 253)   # #93C5FD
_AWAY_COLOR: tuple[int, int, int] = (30, 30, 30)       # near-off


class AmbientLight:
    """Controls an RGB LED strip or NeoPixel via GPIO (or simulates it)."""

    def __init__(self, simulation: bool = True) -> None:
        self._simulation = simulation
        self._current_rgb: tuple[int, int, int] = (0, 0, 0)

        if not simulation:
            self._init_hardware()

    def _init_hardware(self) -> None:
        try:
            import board
            import neopixel

            self._pixels = neopixel.NeoPixel(board.D18, 1, brightness=0.3)
            logger.info("NeoPixel ambient light initialized")
        except (ImportError, ValueError) as exc:
            logger.warning("NeoPixel not available (%s) — simulation mode", exc)
            self._simulation = True

    def set_focus_level(self, focus_level: int, activity_category: str) -> None:
        """Update ambient light to reflect current focus state."""
        if activity_category == "away":
            rgb = _AWAY_COLOR
        elif activity_category == "break":
            rgb = _BREAK_COLOR
        else:
            rgb = _FOCUS_COLOR_MAP.get(focus_level, (156, 163, 175))

        self._set_rgb(rgb)

    def pulse_alert(self) -> None:
        """Brief red pulse for volatility/distraction alerts."""
        import threading
        import time

        def _pulse() -> None:
            self._set_rgb((255, 0, 0))
            time.sleep(0.5)
            self._set_rgb(self._current_rgb)

        threading.Thread(target=_pulse, daemon=True).start()

    def _set_rgb(self, rgb: tuple[int, int, int]) -> None:
        self._current_rgb = rgb
        if self._simulation:
            logger.debug("AmbientLight [simulation] RGB=%s", rgb)
            return
        try:
            self._pixels[0] = rgb
        except Exception as exc:
            logger.error("AmbientLight set failed: %s", exc)

    @property
    def current_hex(self) -> str:
        r, g, b = self._current_rgb
        return f"#{r:02X}{g:02X}{b:02X}"
