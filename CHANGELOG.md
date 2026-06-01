# Changelog

## 0.1.7 - 2026-06-01

### Added

- JSON-driven style selection through `--style-json`, built-in presets, and bundled scenario examples for common labels, notes, and composed layouts.
- Length-aware dry-run metadata for print jobs, including `estimated_length_mm`, `max_length_mm`, and `fits_length_limit`.
- Human-first agent guidance and synchronized skill bundles for scenario-based styling workflows.

### Changed

- Text, paragraph, and compose styling now support `font_fit="largest-fitting"` and whole-word wrapping by default with `break_long_words=false`.
- Rotated text and image length planning now uses `printable_width_mm`, while ordinary orientation and ordinary compose continue to use `advance_mm_per_px`.
- User-facing docs, CLI contract files, and skill references were expanded and synchronized around smart layout, presets, and temporary `--style-json` overrides.

### Fixed

- Boolean style fields such as `autofit` and `break_long_words` now require real booleans in config and JSON payloads instead of truthiness coercion.
- Invalid `--style-json` payloads now fail as normal `CONFIG_ERROR` responses instead of leaking raw validation errors.
- Driver and render paths now preserve length metrics and style resolution consistently across text, image, and compose operations.
