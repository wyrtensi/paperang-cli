# Changelog

## [Unreleased]

### Added
- `paperang --json capabilities` command for runtime platform capability detection
- Cross-platform support: macOS config path (`~/Library/Application Support`), Linux XDG path
- `docs/PLATFORMS.md` as the single source of truth for platform support
- macOS and Linux installation sections in `docs/installation.md`
- macOS and Linux troubleshooting sections in `docs/troubleshooting.md`
- Python 3.11 and 3.13 to CI matrix

### Changed
- CI matrix expanded to 3 OS × 5 Python = 15 test jobs + 3 smoke jobs
- `pyproject.toml` classifiers now include `Operating System :: MacOS` and `Operating System :: POSIX :: Linux`
- README now includes bash-equivalent commands for macOS/Linux

### Platform Impact
- macOS: config path changed from `~/.config/` (XDG fallback) to `~/Library/Application Support/`
- Linux: no change (XDG_CONFIG_HOME still used)
- Windows: no change (APPDATA still used)
- Real BLE printing tested only on Windows; macOS/Linux are software-validated

## 0.1.8 - 2026-06-01

### Added

- Paperang P2 software support over USB and BLE through `paperang-p2-lib`.
- Public `PaperangP2` Python facade, P2 API contract output, model-aware driver registration, and P2 hardware smoke-check documentation.

### Changed

- Configuration now accepts model-specific transport selection and defaults P2 rendering to a `576`-pixel print width.
- Probe output now reports model-specific local transport support.

### Fixed

- `PaperangP2()` now uses the P2 render width when no config file is supplied.
- Default P2 BLE connection scans now prefer the `Paperang` name prefix so `Paperang_P2S` devices can be found without an explicit MAC address.
- Font fallback rendering now preserves the requested size on hosts without the preferred TTF files, allowing `largest-fitting` to shrink long words consistently on macOS.

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
