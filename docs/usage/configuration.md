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
  "macaddress": "04:7F:0E:3A:4F:31",
  "printerwidth": 384,
  "print_density": 75,
  "post_print_feed_mm": 5.0,
  "discovery_names": ["MiaoMiaoJi", "Paperang", "Paperang_P2S"],
  "print_defaults": {
    "text": {
      "font_family": "sans",
      "font_size": null,
      "min_font_size": null,
      "autofit": false,
      "orientation": "normal",
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null
    },
    "paragraph": {
      "font_family": "sans",
      "font_size": null,
      "min_font_size": null,
      "autofit": false,
      "orientation": "normal",
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null
    },
    "image": {
      "mode": "sticker",
      "conversion": null,
      "orientation": "normal"
    },
    "compose": {
      "font_family": "sans",
      "font_size": null,
      "horizontal_padding_px": null,
      "vertical_padding_px": null,
      "line_spacing_px": null,
      "layout": "text-above",
      "spacer_height_px": null,
      "image_mode": "sticker",
      "image_conversion": null
    }
  }
}
```

## Field Meaning

### `model`

Logical printer model identifier used by the driver registry.

In the current release, the only valid value is `paperang_p1`.

### `macaddress`

Optional BLE MAC address. When present, the CLI can connect directly instead of scanning.

For `paperang_p1`, this project currently exposes BLE only. There is no supported local/cable transport setting in the standalone config.

### `printerwidth`

Current render width in pixels. For P1 the practical default is `384`.

### `print_density`

Heat density sent to the printer after connect. The known-good value for the current working behavior is `75`.

### `post_print_feed_mm`

Desired post-print paper exit in millimeters.

Internally, Paperang P1 currently maps this into calibrated printer feed command units.

### `discovery_names`

BLE device names accepted during discovery.

### `print_defaults`

Optional nested render defaults for P1 print jobs.

Active milestone-1 fields:

- `text.font_family`, `paragraph.font_family`: one of `sans`, `mono`, or `serif`
- `text.font_size`, `paragraph.font_size`: default text size override
- `text.min_font_size`, `paragraph.min_font_size`: lower bound for rotated-label autofit
- `text.autofit`, `paragraph.autofit`: enable shrink-to-fit for rotated text jobs
- `text.orientation`, `paragraph.orientation`: `normal`, `rotate-90-cw`, or `rotate-90-ccw`
- `image.mode`, `image.conversion`, `image.orientation`: default image conversion and 90-degree image orientation
- `compose.font_family`, `compose.font_size`, `compose.horizontal_padding_px`, `compose.vertical_padding_px`, `compose.line_spacing_px`, `compose.layout`, `compose.spacer_height_px`, `compose.image_mode`, `compose.image_conversion`: default ordinary compose settings

Rotated compose rendering and compose autofit are not implemented in the current release, so the config schema does not expose those fields yet.

## Precedence Rules

The effective styling for one print job resolves in this order:

1. explicit CLI flags or `PaperangP1` method arguments
2. matching values from `print_defaults`
3. current built-in defaults

Examples:

- `paperang print text ... --font-family mono` overrides `print_defaults.text.font_family`
- `paperang print image ... --orientation rotate-90-ccw` overrides `print_defaults.image.orientation`
- if `print compose` is called without `--layout`, it can now inherit `print_defaults.compose.layout`

## Working Defaults

The default Paperang P1 profile currently reflects the proven working behavior from the root project:

- width `384`
- density `75`
- post-print feed `5.0 mm`
- ordinary text and paragraph orientation `normal`
- ordinary image mode `sticker`

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
4. Keep `model` as `paperang_p1` for now.
5. Only change `post_print_feed_mm` if you want more or less paper exit after text.
6. Add `print_defaults` only after you have a working dry-run baseline.

## Why This Is Separate From The Root Config

The root project already has a known-good runtime configuration, but `paperang-cli` is supposed to be a standalone package.

Keeping an independent config means:

- cleaner packaging
- cleaner tests
- no accidental coupling to the legacy root scripts
- a better place to add future multi-model settings later
