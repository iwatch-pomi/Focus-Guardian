"""Tests for the privacy processor."""

from ..privacy.processor import anonymize_to_pixel_art_state, focus_to_color


def test_pixel_art_state_peak() -> None:
    state = anonymize_to_pixel_art_state("deep_work", 5)
    assert state == "sitting_peak_glow"


def test_pixel_art_state_fallback() -> None:
    state = anonymize_to_pixel_art_state("unknown", 3)
    assert state == "sitting_neutral"


def test_focus_colors_valid_hex() -> None:
    for level in range(1, 6):
        color = focus_to_color(level)
        assert color.startswith("#")
        assert len(color) == 7


def test_focus_color_unknown_level() -> None:
    color = focus_to_color(99)
    assert color == "#9CA3AF"
