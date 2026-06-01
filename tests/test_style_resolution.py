from __future__ import annotations

import pytest

from paperang_cli.style_resolution import resolve_operation_style


def test_style_resolution_merges_defaults_preset_json_and_cli():
    resolved = resolve_operation_style(
        operation="paragraph",
        print_defaults={
            "font_family": "sans",
            "font_size": 24,
            "max_length_mm": None,
        },
        presets={
            "address-label": {
                "paragraph": {
                    "font_family": "mono",
                    "font_size": 30,
                    "orientation": "rotate-90-cw",
                    "max_length_mm": 90.0,
                }
            }
        },
        style_json_payload={"preset": "address-label", "paragraph": {"max_length_mm": 75.0}},
        cli_overrides={"font_size": 28},
    )

    assert resolved["font_family"] == "mono"
    assert resolved["font_size"] == 28
    assert resolved["orientation"] == "rotate-90-cw"
    assert resolved["max_length_mm"] == 75.0


def test_style_resolution_rejects_unknown_preset():
    with pytest.raises(ValueError, match="Unknown preset"):
        resolve_operation_style(
            operation="text",
            print_defaults={},
            presets={},
            style_json_payload={"preset": "missing"},
            cli_overrides={},
        )


@pytest.mark.parametrize("preset", [{}, ["address-label"], 123, ""])
def test_style_resolution_rejects_invalid_preset_name(preset):
    with pytest.raises(ValueError, match="style_json_payload.preset must be a non-empty string"):
        resolve_operation_style(
            operation="paragraph",
            print_defaults={},
            presets={},
            style_json_payload={"preset": preset},
            cli_overrides={},
        )


def test_style_resolution_rejects_operation_specific_unknown_keys():
    with pytest.raises(ValueError, match="Unsupported keys for image"):
        resolve_operation_style(
            operation="image",
            print_defaults={"fit_mode": "fit-width"},
            presets={},
            style_json_payload={"image": {"font_size": 20}},
            cli_overrides={},
        )


@pytest.mark.parametrize(
    ("operation", "operation_payload", "match"),
    [
        ("paragraph", {"orientation": "sideways"}, "resolved_style.paragraph.orientation"),
        ("image", {"fit_mode": "fill-page"}, "resolved_style.image.fit_mode"),
        ("compose", {"overflow_policy": "truncate"}, "resolved_style.compose.overflow_policy"),
    ],
)
def test_style_resolution_rejects_invalid_scalar_values(operation, operation_payload, match):
    with pytest.raises(ValueError, match=match):
        resolve_operation_style(
            operation=operation,
            print_defaults={},
            presets={},
            style_json_payload={operation: operation_payload},
            cli_overrides={},
        )


def test_style_resolution_supports_font_fit_and_compose_min_font_size():
    resolved = resolve_operation_style(
        operation="compose",
        print_defaults={
            "font_fit": "manual",
            "min_font_size": 10,
        },
        presets={
            "product-style": {
                "compose": {
                    "font_fit": "largest-fitting",
                    "min_font_size": 14,
                    "max_length_mm": 55.0,
                }
            }
        },
        style_json_payload={"preset": "product-style", "compose": {"max_length_mm": 60.0}},
        cli_overrides={},
    )

    assert resolved["font_fit"] == "largest-fitting"
    assert resolved["min_font_size"] == 14
    assert resolved["max_length_mm"] == 60.0


def test_style_resolution_rejects_non_boolean_style_json_flags():
    with pytest.raises(ValueError, match="style_json_payload.paragraph.break_long_words must be a boolean"):
        resolve_operation_style(
            operation="paragraph",
            print_defaults={"break_long_words": False},
            presets={},
            style_json_payload={"paragraph": {"break_long_words": "false"}},
            cli_overrides={},
        )


def test_style_resolution_rejects_non_boolean_preset_flags():
    with pytest.raises(ValueError, match="presets.address-label.paragraph.break_long_words must be a boolean"):
        resolve_operation_style(
            operation="paragraph",
            print_defaults={"break_long_words": False},
            presets={"address-label": {"paragraph": {"break_long_words": "false"}}},
            style_json_payload={"preset": "address-label"},
            cli_overrides={},
        )
