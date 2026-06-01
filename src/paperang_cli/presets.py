"""Built-in scenario presets for print layout selection."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "receipt-note": {
        "target": "paragraph",
        "description": "Short receipt-style note or checklist.",
        "paragraph": {
            "font_family": "sans",
            "font_size": 24,
            "autofit": True,
            "max_length_mm": 80.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "address-label": {
        "target": "paragraph",
        "description": "Long address-style label printed along the paper path.",
        "paragraph": {
            "font_family": "mono",
            "font_size": 30,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "rotate-90-cw",
            "max_length_mm": 90.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "fridge-note": {
        "target": "paragraph",
        "description": "General home note for groceries, meal plans, reminders, or quick messages.",
        "paragraph": {
            "font_family": "sans",
            "font_size": 24,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "normal",
            "line_spacing_px": 2,
            "max_length_mm": 120.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "chore-list": {
        "target": "paragraph",
        "description": "Readable household checklist for chores, packing, or recurring routines.",
        "paragraph": {
            "font_family": "sans",
            "font_size": 22,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "normal",
            "line_spacing_px": 4,
            "max_length_mm": 140.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "pantry-label": {
        "target": "paragraph",
        "description": "Jar, spice, or pantry container label for everyday home organization.",
        "paragraph": {
            "font_family": "mono",
            "font_size": 26,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "rotate-90-cw",
            "max_length_mm": 65.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "cable-tag": {
        "target": "paragraph",
        "description": "Narrow charger, cable, or power-brick tag for home desks and drawers.",
        "paragraph": {
            "font_family": "mono",
            "font_size": 22,
            "min_font_size": 12,
            "autofit": True,
            "orientation": "rotate-90-cw",
            "max_length_mm": 45.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "storage-bin": {
        "target": "paragraph",
        "description": "Long shelf, drawer, or storage box label for closets and utility spaces.",
        "paragraph": {
            "font_family": "sans",
            "font_size": 28,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "rotate-90-cw",
            "max_length_mm": 110.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": False,
        },
    },
    "logo-strip": {
        "target": "image",
        "description": "Long monochrome logo or banner art.",
        "image": {
            "orientation": "rotate-90-cw",
            "mode": "sticker",
            "fit_mode": "fit-width",
        },
    },
}


def get_builtin_presets() -> dict[str, dict[str, Any]]:
    return deepcopy(BUILTIN_PRESETS)