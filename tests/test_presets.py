from __future__ import annotations

from paperang_cli.presets import get_builtin_presets


def test_builtin_presets_include_expected_scenarios():
    presets = get_builtin_presets()

    assert presets["receipt-note"]["target"] == "paragraph"
    assert presets["address-label"]["target"] == "paragraph"
    assert presets["address-label"]["paragraph"]["orientation"] == "rotate-90-cw"
    assert presets["fridge-note"]["target"] == "paragraph"
    assert presets["fridge-note"]["paragraph"]["orientation"] == "normal"
    assert presets["chore-list"]["target"] == "paragraph"
    assert presets["chore-list"]["paragraph"]["line_spacing_px"] == 4
    assert presets["pantry-label"]["target"] == "paragraph"
    assert presets["pantry-label"]["paragraph"]["orientation"] == "rotate-90-cw"
    assert presets["cable-tag"]["target"] == "paragraph"
    assert presets["cable-tag"]["paragraph"]["max_length_mm"] == 45.0
    assert presets["storage-bin"]["target"] == "paragraph"
    assert presets["storage-bin"]["paragraph"]["max_length_mm"] == 110.0
    assert presets["logo-strip"]["target"] == "image"
    assert presets["logo-strip"]["image"]["orientation"] == "rotate-90-cw"


def test_get_builtin_presets_returns_independent_copy():
    first = get_builtin_presets()
    second = get_builtin_presets()

    first["receipt-note"]["paragraph"]["font_size"] = 999
    first["fridge-note"]["paragraph"]["font_size"] = 777

    assert second["receipt-note"]["paragraph"]["font_size"] != 999
    assert second["fridge-note"]["paragraph"]["font_size"] != 777