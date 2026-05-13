"""PIR motion sensor — Privacy Gatekeeper.

The camera is activated ONLY when human presence is detected by the PIR sensor.
On non-Raspberry Pi environments this module runs in simulation mode.
"""

from __future__ import annotations

import asyncio
import logging
import time

logger = logging.getLogger(__name__)

_SIMULATION_PRESENCE_RATIO = 0.85  # 85% chance of presence in simulation


class PIRSensor:
    """Abstraction over a GPIO-connected PIR sensor (or simulation)."""

    def __init__(self, gpio_pin: int = 17, simulation: bool = False) -> None:
        self._pin = gpio_pin
        self._simulation = simulation
        self._gpio = None
        self._present = False

        if not simulation:
            self._init_gpio()

    def _init_gpio(self) -> None:
        try:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self._pin, GPIO.IN)
            GPIO.add_event_detect(
                self._pin,
                GPIO.BOTH,
                callback=self._gpio_callback,
                bouncetime=200,
            )
            self._gpio = GPIO
            logger.info("PIR sensor initialized on GPIO pin %d", self._pin)
        except (ImportError, RuntimeError):
            logger.warning("RPi.GPIO not available — falling back to simulation mode")
            self._simulation = True

    def _gpio_callback(self, channel: int) -> None:
        import RPi.GPIO as GPIO
        self._present = bool(GPIO.input(channel))
        logger.debug("PIR event: presence=%s", self._present)

    def is_present(self) -> bool:
        if self._simulation:
            import random
            return random.random() < _SIMULATION_PRESENCE_RATIO
        return self._present

    async def wait_for_presence(self, timeout_seconds: float = 60.0) -> bool:
        """Async wait until presence detected or timeout."""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.is_present():
                return True
            await asyncio.sleep(1.0)
        return False

    def cleanup(self) -> None:
        if self._gpio is not None:
            try:
                self._gpio.cleanup(self._pin)
            except Exception:
                pass
