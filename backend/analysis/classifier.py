"""Activity classifier using Claude Vision API.

Raw image bytes are passed directly to the API and never written to disk.
Prompt caching is enabled for the system prompt to reduce latency and cost.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import anthropic

from ..api.config import settings
from ..privacy.processor import encode_for_api
from ..sensing.snapshot import ActivityReading

if TYPE_CHECKING:
    from PIL.Image import Image

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are Focus Guardian's activity classifier running on a user's local device.

Your task: analyze a snapshot image and classify the user's current activity.

Return ONLY a JSON object with these fields:
{
  "activity_category": one of ["deep_work", "shallow_work", "communication", "break", "distracted", "away", "unknown"],
  "focus_level": integer 1-5 (5 = peak focus, 1 = minimal),
  "confidence": float 0.0-1.0,
  "energy_focus": float 0.0-100.0 (estimated focus energy),
  "energy_fatigue": float 0.0-100.0 (estimated fatigue),
  "notes": short human-readable reason (max 60 chars)
}

Classification guidelines:
- deep_work: sustained concentration on a single cognitively demanding task
- shallow_work: email, admin, low-effort browsing
- communication: meetings, calls, messaging
- break: intentional rest, stretching, eating
- distracted: phone, social media, unintended context switching
- away: empty desk or no person visible
- unknown: cannot determine

Privacy note: this image is processed in memory only and discarded immediately."""


class ActivityClassifier:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def classify(self, image: "Image") -> ActivityReading:
        import json

        b64 = encode_for_api(image)

        try:
            response = await self._client.messages.create(
                model="claude-opus-4-7",
                max_tokens=256,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},  # prompt caching
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": "Classify this snapshot."},
                        ],
                    }
                ],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(raw)
        except Exception as exc:
            logger.warning("Classification failed (%s), using fallback", exc)
            data = {
                "activity_category": "unknown",
                "focus_level": 3,
                "confidence": 0.0,
                "energy_focus": 50.0,
                "energy_fatigue": 50.0,
                "notes": "classification unavailable",
            }

        return ActivityReading(
            activity_category=data.get("activity_category", "unknown"),
            focus_level=int(data.get("focus_level", 3)),
            confidence=float(data.get("confidence", 0.0)),
            energy_focus=float(data.get("energy_focus", 50.0)),
            energy_fatigue=float(data.get("energy_fatigue", 50.0)),
            notes=data.get("notes", ""),
        )
