# Configuration

## Resolution Order

The CLI resolves configuration in this order:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. the per-user default config path
4. built-in defaults

Default paths:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Linux and macOS: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json`, or `~/.config/paperang-cli/paperang-cli.config.json`

This is intentional. It keeps installed packages writable without using `site-packages` and keeps the standalone project independent from the legacy repository runtime config.

## Current Schema

```json
{
  "model": "paperang_p1",
  "default_printer": "p1-main",
  "printers": {
    "p1-main": {
      "model": "paperang_p1",
      "transport": "ble",
      "macaddress": "04:7F:0E:3A:4F:31"
    },
    "p2-main": {
      "model": "paperang_p2",
      "transport": "ble",
      "macaddress": "01:54:8D:17:B3:F2"
    }
  },
  "transport": null,
  "macaddress": "04:7F:0E:3A:4F:31",
  "printerwidth": 384,
  "print_density": 75,
  "post_print_feed_mm": 5.0,
  "calibration": {
    "printable_width_mm": 44.0,
    "advance_mm_per_px": 0.1217
  },
  "discovery_names": ["MiaoMiaoJi", "Paperang", "Paperang_P2", "Paperang_P2S"],
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

## Field Meaning

### `model`

Logical printer model identifier used by the driver registry.

In the current release, valid values are `paperang_p1` and `paperang_p2`.

### `default_printer` And `printers`

Optional named printer profiles for machines that use more than one Paperang.

When `printers` is present, each profile must contain its own `model`. Use the global CLI option `--printer NAME` to select a profile for any command:

```powershell
paperang --json --printer p1-main status
paperang --json --printer p2-main print text "P2 note" --dry-run
```

If `--printer` is omitted, `default_printer` is used. If `default_printer` is omitted, the first profile in the JSON object is used.

Top-level `post_print_feed_mm`, `discovery_names`, `print_defaults`, and `presets` are shared by profiles unless a profile overrides them. Model-specific physical defaults such as width, density, and calibration are resolved from each selected profile's `model`, so a P2 profile does not inherit P1 width or paper-advance calibration by accident.

The older single-printer fields (`model`, `transport`, `macaddress`, and the rest) remain supported when `printers` is absent.

### `transport`

Optional live-transport override.

- For `paperang_p1`, keep this unset or use `ble`.
- For `paperang_p2`, use `ble` for the supported and physically validated FF00/A5 path.
- For `paperang_p2`, `usb` is still available as an experimental software path.
- If `model` is `paperang_p2` and `transport` is omitted, the runtime currently defaults to `usb` for backward compatibility. Set `transport` to `ble` for the supported P2 path.

### `macaddress`

Optional BLE MAC address. When present, the CLI can connect directly instead of scanning.

For `paperang_p1`, this project currently exposes BLE only. For `paperang_p2`, this field matters when transport resolves to BLE and is ignored when the experimental USB path is selected.

### `printerwidth`

Current render width in pixels. For P1 the practical default is `384`. For P2, the model-specific default is `576` when `printerwidth` is omitted.

### `print_density`

Heat density sent to the printer after connect.

Model-specific default values are:

- `paperang_p1`: `75`
- `paperang_p2`: `95`

### `post_print_feed_mm`

Desired post-print paper exit in millimeters.

Model-specific built-in defaults are:

- `paperang_p1`: `5.0 mm`
- `paperang_p2`: `12.0 mm`

Internally, Paperang P1 currently maps this into calibrated printer feed command units. Paperang P2 BLE FF00/A5 maps this to a blank raster feed in millimeters, because the validated FF00 path does not expose a separate confirmed feed command yet.

### `calibration`

Physical planning constants used for dry-run reporting and length-aware fitting.

- `printable_width_mm`: measured printable width of the full `384 px` head. Rotated `rotate-90-cw` and `rotate-90-ccw` text and image jobs use this value for `estimated_length_mm` and `max_length_mm` planning along the paper path.
- `advance_mm_per_px`: measured vertical paper advance per rendered pixel. Ordinary orientation jobs and ordinary compose length planning use this value.

For the current Paperang P1 baseline in this repo, the working planning defaults are `44.0 mm` and `0.1217 mm/px`.

For Paperang P2, the current measured default is `0.08472 mm/px`, based on an approximately `61 mm` printed distance over `720 px`.

To re-measure P2, use the native `576 px` calibration strip generated by `scripts/make-p2-calibration-strip.py`. The bundled `calibration-strip-p2-720.png` has a `720 px` marker-to-marker distance; measure the printed vertical tip-to-tip distance in millimeters and set:

```text
advance_mm_per_px = measured_mm / 720
```

Do not use the older `384 px` P1 strip to measure P2 advance unless you account for P2 width scaling.

### `discovery_names`

BLE device names accepted during discovery.

The default list includes `Paperang_P2` because some P2 units advertise that exact BLE name while exposing the `ff00` profile with `A5...5A` protocol frames instead of the upstream Nordic UART profile.

### `print_defaults`

Optional nested render defaults for supported print jobs.

Active milestone-1 fields:

- `text.font_family`, `paragraph.font_family`: one of `sans`, `mono`, or `serif`
- `text.font_size`, `paragraph.font_size`: default text size override
- `text.min_font_size`, `paragraph.min_font_size`: lower bound for rotated-label autofit
- `text.font_fit`, `paragraph.font_fit`: `manual` or `largest-fitting`; when `largest-fitting` is active, the renderer searches downward for the biggest fitting size
- `text.autofit`, `paragraph.autofit`: enable shrink-to-fit for rotated text jobs
- `text.orientation`, `paragraph.orientation`: `normal`, `rotate-90-cw`, or `rotate-90-ccw`
- `text.max_length_mm`, `paragraph.max_length_mm`: optional physical budget along the paper path
- `text.overflow_policy`, `paragraph.overflow_policy`: `error` or `shrink-to-fit`
- `text.break_long_words`, `paragraph.break_long_words`: whether to force long unspaced words to wrap by character chunks; default `false` keeps the token intact so `largest-fitting` can shrink it onto one line or fail cleanly
- `image.mode`, `image.conversion`, `image.orientation`: default image conversion and 90-degree image orientation
- `image.max_length_mm`: optional physical budget along the paper path
- `image.fit_mode`: `fit-width` or `fit-within-length`
- `compose.font_family`, `compose.font_size`, `compose.min_font_size`, `compose.font_fit`, `compose.horizontal_padding_px`, `compose.vertical_padding_px`, `compose.line_spacing_px`, `compose.layout`, `compose.spacer_height_px`, `compose.image_mode`, `compose.image_conversion`: default ordinary compose settings
- `compose.max_length_mm`: optional physical compose budget for reporting or hard failure
- `compose.overflow_policy`: `report-only` or `error`
- `compose.break_long_words`: whether to force the text section to split long words while wrapping; default `false` preserves whole tokens unless you opt in

### `presets`

Optional named scenario presets. These are merged with built-in presets and can be selected per invocation through `--style-json`.

Rotated compose rendering and compose autofit are not implemented in the current release, so the config schema does not expose those fields yet.

Agent-driven print requests should use the nearest built-in scenario or shipped example as the default starting point when one fits, then apply small per-invocation `--style-json` overrides as needed. Scenarios are reusable bases, not absolute modes.

## Precedence Rules

The effective styling for one print job resolves in this order:

1. explicit CLI flags or `PaperangP1` method arguments
2. per-invocation `--style-json` operation block
3. preset selected inside `--style-json`
4. matching values from `print_defaults`
5. current built-in defaults

Examples:

- `paperang print text ... --font-family mono` overrides `print_defaults.text.font_family`
- `paperang print paragraph ... --style-json .\address-label.json` can inherit a preset and still let `--font-size` win on top
- `paperang print image ... --orientation rotate-90-ccw` overrides `print_defaults.image.orientation`
- if `print compose` is called without `--layout`, it can now inherit `print_defaults.compose.layout`

## One-Off Overrides Vs Saved Defaults

Use `print_defaults` when you want a persistent baseline for future jobs.

Use `--style-json` when you want a task-specific choice without changing your saved defaults. This is the recommended path for agent-driven or exploratory work.

Built-in presets and shipped example payloads are starting points, not a whitelist. A good workflow is:

1. choose the nearest preset or example as a base
2. add only the overrides needed for this task
3. save the same idea into `print_defaults` only if you explicitly want it to become the future default

For human-friendly text defaults, ordinary word wrapping with `break_long_words=false` is the normal baseline. Enable `break_long_words=true` only when you explicitly want character-level splitting for long unspaced tokens.

## Working Defaults

The default Paperang P1 profile currently reflects the proven working behavior from the root project:

- width `384`
- density `75`
- post-print feed `5.0 mm`
- ordinary text and paragraph orientation `normal`
- ordinary image mode `sticker`

For `paperang_p2`, the runtime switches the default render width to `576`, uses density `95`, uses `advance_mm_per_px=0.08472`, scales built-in text font and padding defaults from the P1 `384 px` head to the P2 `576 px` head, uses a larger `12.0 mm` post-print feed by default, and resolves transport to `usb` unless you explicitly choose BLE. Use BLE for the supported P2 path; the default USB path remains for backward-compatible experimentation.

## Font Families And Rotation

The current release intentionally limits font selection to generic families so configuration stays portable:

- `sans`
- `mono`
- `serif`

Those names map to system fonts with platform-specific fallbacks. They are not a promise of pixel-identical output across operating systems.

The current release supports rotated printing for:

- `print text`
- `print paragraph`
- `print image`

Rotated `print compose` is not implemented yet.

## Recommended Workflow

1. Run `paperang config init`.
2. Open the reported config path.
3. Replace `macaddress` with your real printer address.
4. Keep `model` as `paperang_p1` for BLE P1 use, or switch to `paperang_p2` and set `transport` to `ble` when configuring a supported P2 path.
5. Only change `post_print_feed_mm` if you want more or less paper exit after text.
6. Add `print_defaults` only after you have a working dry-run baseline.
7. Measure and tune `calibration` if you need trustworthy dry-run centimeter estimates.

## Why This Is Separate From The Root Config

The root project already has a known-good runtime configuration, but `paperang-cli` is supposed to be a standalone package.

Keeping an independent config means:

- cleaner packaging
- cleaner tests
- no accidental coupling to the legacy root scripts
- a better place to add future multi-model settings later
