"""Resolve JSON style payloads and preset inheritance for one print operation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from paperang_cli.config import ComposePrintDefaults, ImagePrintDefaults, TextPrintDefaults
from paperang_cli.errors import ConfigError


_TEXT_KEYS = {
    "font_family",
    "font_size",
    "min_font_size",
    "font_fit",
    "autofit",
    "orientation",
    "horizontal_padding_px",
    "vertical_padding_px",
    "line_spacing_px",
    "max_length_mm",
    "overflow_policy",
    "break_long_words",
}
_IMAGE_KEYS = {
    "mode",
    "conversion",
    "orientation",
    "max_length_mm",
    "fit_mode",
}
_COMPOSE_KEYS = {
    "font_family",
    "font_size",
    "min_font_size",
    "font_fit",
    "horizontal_padding_px",
    "vertical_padding_px",
    "line_spacing_px",
    "layout",
    "spacer_height_px",
    "image_mode",
    "image_conversion",
    "max_length_mm",
    "overflow_policy",
    "break_long_words",
}
_BOOLEAN_KEYS = {
    "text": {"autofit", "break_long_words"},
    "paragraph": {"autofit", "break_long_words"},
    "image": set(),
    "compose": {"break_long_words"},
}
_ALLOWED_KEYS = {
    "text": _TEXT_KEYS,
    "paragraph": _TEXT_KEYS,
    "image": _IMAGE_KEYS,
    "compose": _COMPOSE_KEYS,
}


def _validate_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _validate_allowed_keys(payload: dict[str, Any], *, operation: str) -> None:
    allowed_keys = _ALLOWED_KEYS[operation]
    invalid_keys = sorted(set(payload) - allowed_keys)
    if invalid_keys:
        raise ValueError(f"Unsupported keys for {operation}: {', '.join(invalid_keys)}")


def _validate_boolean_keys(payload: dict[str, Any], *, operation: str, label: str) -> None:
    for key in _BOOLEAN_KEYS[operation]:
        if key in payload and not isinstance(payload[key], bool):
            raise ValueError(f"{label}.{key} must be a boolean")


def _validate_resolved_style(payload: dict[str, Any], *, operation: str) -> dict[str, Any]:
    label = f"resolved_style.{operation}"
    try:
        if operation in {"text", "paragraph"}:
            resolved_style = TextPrintDefaults.from_mapping(payload, label=label)
        elif operation == "image":
            resolved_style = ImagePrintDefaults.from_mapping(payload)
        else:
            resolved_style = ComposePrintDefaults.from_mapping(payload, label=label)
        resolved_style.validate(label=label)
    except (ConfigError, TypeError, ValueError) as exc:
        raise ValueError(str(exc)) from exc
    return asdict(resolved_style)


def resolve_operation_style(
    *,
    operation: str,
    print_defaults: dict[str, Any],
    presets: dict[str, dict[str, Any]],
    style_json_payload: dict[str, Any] | None,
    cli_overrides: dict[str, Any],
) -> dict[str, Any]:
    if operation not in _ALLOWED_KEYS:
        raise ValueError(f"Unsupported operation: {operation}")

    normalized_defaults = _validate_mapping(print_defaults, label="print_defaults")
    normalized_payload = _validate_mapping(style_json_payload, label="style_json_payload")
    normalized_overrides = _validate_mapping(cli_overrides, label="cli_overrides")

    resolved = dict(normalized_defaults)

    inherited_preset = normalized_payload.get("preset")
    if inherited_preset is not None:
        if not isinstance(inherited_preset, str) or not inherited_preset.strip():
            raise ValueError("style_json_payload.preset must be a non-empty string")
        inherited_preset = inherited_preset.strip()
        try:
            preset_definition = _validate_mapping(presets[inherited_preset], label=f"presets.{inherited_preset}")
        except KeyError as exc:
            raise ValueError(f"Unknown preset: {inherited_preset}") from exc
        preset_payload = _validate_mapping(preset_definition.get(operation), label=f"presets.{inherited_preset}.{operation}")
        _validate_allowed_keys(preset_payload, operation=operation)
        _validate_boolean_keys(preset_payload, operation=operation, label=f"presets.{inherited_preset}.{operation}")
        resolved.update(preset_payload)

    operation_payload = _validate_mapping(normalized_payload.get(operation), label=f"style_json_payload.{operation}")
    _validate_allowed_keys(operation_payload, operation=operation)
    _validate_boolean_keys(operation_payload, operation=operation, label=f"style_json_payload.{operation}")
    resolved.update(operation_payload)

    effective_overrides = {key: value for key, value in normalized_overrides.items() if value is not None}
    _validate_allowed_keys(effective_overrides, operation=operation)
    _validate_boolean_keys(effective_overrides, operation=operation, label="cli_overrides")
    resolved.update(effective_overrides)
    return _validate_resolved_style(resolved, operation=operation)
