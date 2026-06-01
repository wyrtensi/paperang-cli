# Smart Layout and JSON Presets Design

## Goal

Make Paperang P1 print layout measurable, scenario-driven, and agent-friendly.

The operator should be able to:

- pick a real-life preset instead of tuning raw knobs every time
- override the preset through JSON without editing Python code
- trust dry-run output to report the effective font, wrapping result, and estimated printed length before paper use
- calibrate physical length empirically when the printer's real printable width differs from the initial model estimate

## Current Gaps

The current implementation has a solid rendering baseline, but it still behaves like a low-level styling surface:

- text autofit only shrinks rotated text to satisfy width after rotation
- there is no length budget in millimeters or centimeters for any print mode
- image printing already behaves like fit-to-width with unbounded length, but the user cannot ask for fit-within-length or inspect predicted length
- compose supports only the ordinary vertical path and does not expose layout metrics beyond the existing print summary
- wrapping rules are implicit and not documented for explicit line breaks or overlong tokens
- the only JSON control surface is persistent config; there is no one-shot style JSON override for a single print request
- there is no preset catalog for common scenarios such as labels, planner strips, or photo captions

## Non-Goals

This design deliberately does not include the following in the first implementation cycle:

- rotated compose rendering
- dictionary-based hyphenation
- a visual WYSIWYG preview renderer
- automatic machine learning from previous successful prints
- model support beyond `paperang_p1`

Those can be layered on later without invalidating the data model below.

## Design Summary

The feature is built around four ideas:

1. Extend the existing config and driver pipeline with a shared layout vocabulary for length budgeting, wrapping, and scenario presets.
2. Add a per-invocation JSON override path so an agent can send structured layout intent without mutating persistent config.
3. Generalize text autofit into a real fit loop that renders with actual font metrics, actual wrapping, and actual orientation before accepting a result.
4. Return measurable dry-run metadata so humans and agents can reason about printed length before paper use.

The implementation remains safety-first:

- dry-run remains the required validation path before any real print
- the real print must use the same resolved preset, JSON override, orientation, font family, font size, fit mode, and feed settings as the dry-run
- image and compose printing remain marked experimental for physical output quality

## JSON Control Surface

All new behavior is controlled through JSON-backed settings. CLI flags remain available, but the new features are designed so they can be driven entirely from JSON.

### Persistent Config

Extend `paperang-cli.config.example.json` and the config schema with two new areas:

1. `calibration`
2. richer `print_defaults` plus `presets`

Proposed shape:

```json
{
  "model": "paperang_p1",
  "macaddress": "04:7F:0E:3A:4F:31",
  "printerwidth": 384,
  "print_density": 75,
  "post_print_feed_mm": 5.0,
  "calibration": {
    "printable_width_mm": 44.0,
    "advance_mm_per_px": 0.1217
  },
  "print_defaults": {
    "text": {
      "font_family": "sans",
      "font_size": null,
      "min_font_size": null,
      "font_fit": "manual",
      "autofit": false,
      "orientation": "normal",
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null,
      "max_length_mm": null,
      "overflow_policy": "shrink-to-fit",
      "break_long_words": false
    },
    "paragraph": {
      "font_family": "sans",
      "font_size": null,
      "min_font_size": null,
      "font_fit": "manual",
      "autofit": false,
      "orientation": "normal",
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null,
      "max_length_mm": null,
      "overflow_policy": "shrink-to-fit",
      "break_long_words": false
    },
    "image": {
      "mode": "sticker",
      "conversion": null,
      "orientation": "normal",
      "max_length_mm": null,
      "fit_mode": "fit-width"
    },
    "compose": {
      "font_family": "sans",
      "font_size": null,
      "min_font_size": null,
      "font_fit": "manual",
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null,
      "layout": "text-above",
      "spacer_height_px": null,
      "image_mode": "sticker",
      "image_conversion": null,
      "max_length_mm": null,
      "overflow_policy": "report-only",
      "break_long_words": false
    }
  },
  "presets": {
    "address-label": {
      "target": "paragraph",
      "description": "Long address-style label printed along the paper path.",
      "paragraph": {
        "font_family": "mono",
        "font_size": 30,
        "min_font_size": 14,
        "autofit": true,
        "orientation": "rotate-90-cw",
        "max_length_mm": 90.0,
        "overflow_policy": "shrink-to-fit",
        "break_long_words": false
      }
    }
  }
}
```

Rules:

- `calibration.printable_width_mm` must be greater than zero.
- `calibration.advance_mm_per_px` must be greater than zero.
- `overflow_policy` for text and paragraph is `error` or `shrink-to-fit`.
- `fit_mode` for image is `fit-width` or `fit-within-length`.
- `overflow_policy` for compose is `report-only` or `error` in the first milestone.
- `presets` is a mapping of user-defined profiles that can extend or override built-in scenario presets.

### Per-Invocation JSON

Add `--style-json PATH|-` to `print text`, `print paragraph`, `print image`, and `print compose`.

- `PATH` reads a JSON file.
- `-` reads JSON from standard input.
- the object shape matches one preset entry
- the object may include `preset` to inherit from a named preset and then override it inline
- invalid JSON or invalid schema is treated like config validation failure

Example one-shot style JSON:

```json
{
  "preset": "address-label",
  "paragraph": {
    "max_length_mm": 75.0,
    "font_size": 28
  }
}
```

### CLI Additions

Add one new option to all printing commands:

- `--style-json PATH|-`

The preset name travels inside the JSON object itself. This keeps the new control plane JSON-first and avoids two competing preset-selection paths.

### Precedence

The effective layout for one operation resolves in this order:

1. explicit CLI flags
2. per-invocation `--style-json`
3. named preset embedded inside `--style-json`
4. matching `print_defaults` values from config
5. current built-in defaults

This order must be the same for dry-run and real print so the safety contract remains stable.

### JSON Simplification Constraints

The first implementation should explicitly avoid three sources of maintenance pain:

- no separate `--preset` flag; JSON is the only new control path
- operation-specific field validation must reject text-only keys on image jobs and image-only keys on text jobs
- compose remains a single explicit operation, but its resolution logic must treat text-related and image-related keys as separate allowlists even if the serialized JSON remains flat in the first milestone

This keeps the public shape close to the current CLI while still enforcing stricter validation internally.

## Built-In Scenario Presets

Ship a built-in preset catalog in code and allow config JSON to add or override entries.

The first catalog should include both ordinary vertical printing and along-the-paper printing:

| Preset | Target | Intent | Key defaults |
| --- | --- | --- | --- |
| `receipt-note` | `paragraph` | short receipt-style notes, checklists, reminders | normal orientation, sans, compact paragraph, shrink-to-fit, medium length budget |
| `address-label` | `paragraph` | mailing address or shipping note | rotated orientation, mono, long length budget, whole-word wrapping by default |
| `fridge-note` | `paragraph` | grocery list, meal plan, reminder, or quick home note | normal orientation, sans, readable spacing, larger length budget |
| `chore-list` | `paragraph` | household checklist, packing list, or recurring routine | normal orientation, sans, readable spacing, larger length budget |
| `pantry-label` | `paragraph` | jar, spice, or pantry container label | rotated orientation, mono, medium length budget, shrink-to-fit |
| `cable-tag` | `paragraph` | narrow charger, cable, or power-brick tag | rotated orientation, mono, tight length budget, shrink-to-fit |
| `storage-bin` | `paragraph` | long shelf, drawer, or storage box label | rotated orientation, sans, longer length budget, shrink-to-fit |
| `logo-strip` | `image` | long logo or monochrome banner art | rotated orientation, sticker mode, fit-width, unbounded length |

Preset design rules:

- presets represent user intent, not raw technical modes
- every preset must still resolve down to existing command surfaces: text, paragraph, image, or compose
- presets may set a default target command, but the command itself remains explicit in the CLI
- a preset can omit fields and rely on `print_defaults`
- the dry-run result must report the applied preset name

## Architecture

The implementation should stay modular instead of growing `config.py` and `print_cmd.py` into large switchboards.

### 1. Config Schema Layer

Keep config parsing and validation in `config.py`, but add new dataclasses for:

- calibration settings
- text length budgeting fields
- image fit fields
- compose overflow reporting fields

This layer validates JSON shape and scalar values, but it does not perform merging across presets, JSON overrides, and CLI flags.

### 2. Built-In Preset Catalog

Add a new `presets.py` module with the built-in scenario catalog.

Responsibilities:

- define the built-in preset names and descriptions
- return JSON-like dictionaries safe to merge with config-defined presets
- provide one authoritative source for docs, tests, and the CLI/API contract

### 3. Style Resolution Layer

Add a new `style_resolution.py` module that merges:

- built-in presets
- config-defined presets
- `print_defaults`
- `--style-json`
- explicit CLI flags

Responsibilities:

- load and validate one-shot style JSON
- resolve preset inheritance deterministically
- normalize operation-specific settings before the driver is called
- keep the precedence rules in one place so CLI and Python API do not diverge

Validation must be allowlist-based per operation. A style payload for `print image` cannot silently carry `font_size`, `min_font_size`, `autofit`, or `break_long_words`, and a text payload cannot silently carry image conversion keys.

### 4. Render Layer

Keep rendering in `render.py`, but extend it to:

- estimate printed length in millimeters from the rendered pixel height and paper-advance calibration
- preserve explicit line breaks
- wrap text line by line
- break overlong tokens when configured
- run a real fit loop for text and paragraph jobs
- optionally scale images down to fit a length budget
- return metrics alongside the bitstream

### 5. Driver and Result Layer

Extend the rendered payload and `PrintResult` so dry-run and real print share the same metrics envelope:

- rendered height in pixels
- estimated length in millimeters
- configured max length in millimeters
- whether the job satisfied the length budget
- applied preset name

The driver still owns safety checks and transport behavior. The new layout system only changes how the render job is resolved and reported.

## Data Flow

1. CLI or Python API receives a print request plus optional preset name, style JSON, and scalar overrides.
2. The resolution layer selects the matching preset, merges config defaults and one-shot JSON, then applies CLI/API overrides.
3. The render layer draws the content using actual font metrics, actual wrapping, actual padding, and actual orientation.
4. The render layer computes height and estimated physical length using calibration.
5. If the content exceeds the configured length budget, the render layer applies the requested policy:
   - shrink the font for text and paragraph when policy is `shrink-to-fit`
   - scale the image for image mode when fit mode is `fit-within-length`
   - report or error for compose depending on compose overflow policy
6. The driver returns a `PrintResult` that includes both transport metadata and the resolved layout metrics.
7. A matching real print uses the same resolved layout values as the dry-run.

## Text Wrapping and Fit Behavior

### Hard Line Breaks

Explicit `\n` line breaks are always preserved.

The renderer treats the input as hard lines first, then wraps each hard line independently. This keeps addresses, product titles, and manually authored multi-line labels stable.

### Soft Wrapping

The default wrapping mode is word-based wrapping within the available line width after padding.

The first milestone does not add a selectable wrap algorithm matrix. It standardizes one predictable behavior:

- keep explicit line breaks
- wrap on whitespace
- preserve line order
- keep the renderer deterministic across dry-run and real print

### Overlong Tokens

If a single token exceeds the available width:

- when `break_long_words` is `true`, split it by characters until the segment fits
- when `break_long_words` is `false`, leave the token intact and let the fit loop either shrink the font or fail with an overflow error

This is enough for identifiers, URLs, SKUs, and compact code-like labels without introducing full hyphenation logic.

### Font-Sensitive Fit Loop

The fit loop must behave like the human slider workflow described in planning:

1. start from the requested or preset font size
2. render with the actual font family and actual wrapping rules
3. apply orientation
4. measure the final canvas
5. accept it if the width and length constraints are satisfied
6. otherwise decrease the size and try again down to `min_font_size`

Important details:

- font family matters because the measured bounding boxes differ between `sans`, `mono`, and `serif`
- padding and line spacing remain part of the fit calculation
- rotated and non-rotated text use the same fit loop; only the final orientation transform differs
- the first acceptable size wins to keep behavior deterministic and easy to explain

Linear downward search is acceptable in the first iteration because the typical font-size range is small and the behavior is easier to debug than a more clever search.

## Image Behavior

Image handling keeps today's working behavior as the default:

- rotate first if requested
- fit to printer width
- keep aspect ratio
- allow unbounded length unless configured otherwise

Add one new explicit mode:

- `fit-width`: current behavior
- `fit-within-length`: after fitting to width and measuring length, scale down again until the job fits the configured `max_length_mm`

This avoids breaking the current long-banner workflow while giving the user an opt-in way to constrain long images.

Dry-run must always report the final estimated length for images, regardless of mode.

## Compose Behavior

Compose keeps its current vertical-only rendering path in the first milestone.

What changes now:

- presets can target compose jobs
- compose dry-run gains the same length metrics as the other modes
- compose inherits the text wrapping rules for its text block
- compose can optionally fail when the rendered job exceeds `max_length_mm`

What does not change yet:

- no rotated compose
- no full compose auto-shrink that simultaneously rebalances text and image

This keeps the first implementation bounded while still making compose measurable and preset-driven.

## Calibration and Physical Measurement

The repo currently knows the printer width in pixels, but real hardware needs two independent physical calibration values:

- printable width in millimeters across the thermal head
- paper advance in millimeters per rendered pixel row

The design therefore uses two layers:

1. a model seed for Paperang P1
2. a user calibration override

### Model Seed

Seed `calibration.printable_width_mm` and `calibration.advance_mm_per_px` with practical Paperang P1 baseline values.

Current measured planning baseline:

- full rendered width `384 px` printed at about `44 mm`
- measured marker-to-marker advance of about `112 mm` across a `920 px` vertical gap
- `advance_mm_per_px = 112 / 920 = 0.1217`

This baseline is intentionally treated as a practical default, not a hardware guarantee.

### User Calibration

If measured paper output differs from the baseline, the user updates `calibration.printable_width_mm` and `calibration.advance_mm_per_px` in JSON.

The documented calibration workflow is manual in the first milestone:

- print a known-length dry-run-validated sample in normal orientation
- print a known-length dry-run-validated sample in rotated orientation
- measure the actual printed length between visible endpoints
- adjust `printable_width_mm` and `advance_mm_per_px` until dry-run estimates match the physical result closely enough

The calibration value is explicit JSON, not hidden local state.

If this manual loop proves too awkward, a dedicated calibration helper command can be added later without changing the underlying metric model.

### Calibration Print Protocol

The first practical protocol should use generated monochrome image strips rather than text.

Reasoning:

- image strips give exact known pixel dimensions
- simple black markers survive threshold conversion reliably
- the measurement does not depend on font metrics or wrapping

Recommended strip design:

- full render width: `384 px`
- white background
- a solid horizontal marker line near the start and another near the end
- visually distinct horizontal markers with stable left-right edges so printed width and paper advance can both be measured reliably
- quiet white margins above and below the markers so feed behavior does not affect the measurement target

Recommended sample set:

- `384 x 480 px` strip with a known marker gap
- `384 x 720 px` strip with a known marker gap

Why these lengths:

- `60 mm` is compact enough for easy test printing
- `90 mm` reduces relative measurement error when the user only has a ruler

Measurement rule:

- measure printed width across the full black line from left edge to right edge
- measure paper advance from the first horizontal marker line to the second horizontal marker line
- do not include extra blank feed beyond the lower marker

Calibration formulas:

$$
  ext{printable\_width\_mm} = \text{measured\_width\_mm}
$$

$$
  ext{advance\_mm\_per\_px} = \frac{\text{measured\_advance\_mm}}{\text{marker\_distance\_px}}
$$

$$
  ext{estimated\_length\_mm} = \text{render\_height\_px} \cdot \text{advance\_mm\_per\_px}
$$

Current measured example from this session:

- measured width about `44 mm` across `384 px`
- measured advance about `112 mm` across `920 px`
- resulting `advance_mm_per_px` is about `0.1217`

The rotated-orientation validation print is still useful, but the primary calibration constants should come from these fixed-size image strips because they isolate geometry from font behavior.

## Dry-Run Output Contract

Extend print results with layout metrics that make the resolved decision visible.

New result fields:

- `applied_preset`
- `render_height_px`
- `estimated_length_mm`
- `max_length_mm`
- `fits_length_budget`
- `printable_width_mm`
- `advance_mm_per_px`

These appear in:

- JSON output from print commands
- human-readable print summaries
- Python `PrintResult`

The effective styling payload should also expose the resolved fields so a user can see exactly what the preset and JSON overrides became after precedence resolution.

## Error Handling

Expected validation and runtime failures:

- unknown preset name
- invalid or unreadable `--style-json`
- invalid schema inside config or style JSON
- `max_length_mm <= 0`
- `printable_width_mm <= 0`
- `advance_mm_per_px <= 0`
- text cannot fit even at `min_font_size`
- compose exceeds `max_length_mm` when overflow policy is `error`
- unsupported field combinations, such as compose-specific keys passed to an image command

Config and style-validation failures should behave like existing config errors and keep the current exit semantics.

## Testing Strategy

Add or extend tests in the existing suites:

- `tests/test_config.py` for new schema validation
- `tests/test_render.py` for wrapping, fitting, estimation, and image fit modes
- `tests/test_driver_styles.py` for defaults, preset propagation, and reported metrics
- `tests/test_cli.py` for `--style-json` and output fields
- `tests/test_api.py` for Python facade parity if the public API accepts the new layout controls
- `tests/test_check_agent_skill.py` indirectly through synchronized contract updates

Contract and docs must be updated together:

- `docs/agents/cli-contract.md`
- `docs/agents/cli-contract.json`
- `skills/paperang-cli/references/cli-contract.md`
- `skills/paperang-cli/references/cli-contract.json`
- `docs/usage/commands.md`
- `docs/usage/configuration.md`

## Rollout Shape

Implementation should proceed in three slices:

1. config, presets, style resolution, text wrapping, text fit, and dry-run length metrics
2. image length budgeting and compose length enforcement/reporting
3. docs, contract updates, calibration workflow guidance, and final verification

This ordering gives users immediate value from text fitting and measurable dry-runs before expanding the more experimental image and compose flows.