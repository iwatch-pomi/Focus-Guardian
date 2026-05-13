"""Privacy-first image processor.

Raw images are held in memory only and discarded immediately after AI inference.
Nothing is written to disk.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image


def encode_for_api(image: "Image") -> str:
    """Encode PIL image to base64 JPEG for Claude Vision — stays in memory only."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    buf.seek(0)
    data = base64.standard_b64encode(buf.read()).decode()
    buf.close()
    return data


def anonymize_to_pixel_art_state(activity_category: str, focus_level: int) -> str:
    """Map activity + focus level to a pixel-art avatar state code.

    No image data is involved — this derives a display state purely from
    the already-classified labels.
    """
    state_map: dict[tuple[str, int], str] = {
        ("deep_work", 5): "sitting_peak_glow",
        ("deep_work", 4): "sitting_focused",
        ("deep_work", 3): "sitting_neutral",
        ("shallow_work", 3): "sitting_typing",
        ("shallow_work", 2): "sitting_browsing",
        ("communication", 3): "sitting_talking",
        ("break", 2): "standing_stretch",
        ("break", 1): "reclining",
        ("distracted", 2): "sitting_phone",
        ("distracted", 1): "slouching",
        ("away", 1): "empty_desk",
    }
    return state_map.get((activity_category, focus_level), "sitting_neutral")


def focus_to_color(focus_level: int) -> str:
    """Map focus level (1-5) to a hex color for the avatar theme."""
    palette = {5: "#6EE7B7", 4: "#34D399", 3: "#FCD34D", 2: "#F97316", 1: "#EF4444"}
    return palette.get(focus_level, "#9CA3AF")
