# Command Reference

## Global Options

These options apply before the subcommand:

```powershell
paperang --config PATH --json --debug <command>
```

The installed package exposes both `paperang` and `paperang-cli`.

- Prefer `paperang` for day-to-day use.
- Use `paperang-cli` if the short command conflicts with something else.

### `--config PATH`

Use a specific JSON config file for this invocation.

### `--json`

Return structured output suitable for scripts and agents.

### `--debug`

Enable verbose logging. This is useful for BLE protocol investigation.

## `api list`

Non-printing command that lists known model-specific API entries and whether they are currently available.

Examples:

```powershell
paperang api list
paperang --json api list
```

Typical data returned:

- API identifier such as `p1` or `p2`
- matching model id
- whether the facade is available in the current package version
- current status such as `available`
- current or planned facade class name

## `api p1`

Non-printing command that shows the supported `PaperangP1` Python API surface exposed by the package.

Examples:

```powershell
paperang api p1
paperang --json api p1
```

Typical data returned:

- availability information for the model-specific facade
- import path for the public class
- current implementation module for the model-specific facade
- constructor options and defaults
- supported high-level methods
- current styling support such as generic font families and rotated print methods
- current safety requirements for real printing
- unsupported parity gaps versus `paperang-p2-lib`

## `api p2`

Non-printing command that shows the supported `PaperangP2` Python API surface exposed by the package.

Examples:

```powershell
paperang api p2
paperang --json api p2
```

Typical data returned:

- availability information for the model-specific facade
- import path for the public class
- transport selection details for `usb` and `ble`
- constructor options and defaults
- supported high-level methods
- parity gaps that explain what is still unavailable or unvalidated

## `status`

Non-printing command that connects to the configured printer and reports current information.

Example:

```powershell
paperang status
paperang --json status
paperang status --address 04:7F:0E:3A:4F:31
```

Typical data returned:

- model
- address
- connected flag
- battery percentage
- serial number
- firmware information
- print density
- power-off timeout
- hardware info

## `battery`

Non-printing command that connects to the printer and asks only for the current battery level.

Example:

```powershell
paperang battery
paperang --json battery
paperang battery --address 04:7F:0E:3A:4F:31
```

Typical data returned:

- model
- address
- transport
- connected flag
- battery percentage

## `mac`

Non-printing command that asks the printer for its own Bluetooth MAC address.

Example:

```powershell
paperang mac
paperang --json mac
paperang mac --address 04:7F:0E:3A:4F:31
```

Typical data returned:

- model
- address used for the connection
- transport
- connected flag
- printer-reported Bluetooth MAC address

## `probe`

Non-printing command that runs the usual live status query for the selected driver plus the printer-reported Bluetooth MAC query and returns them in one summary payload.

Example:

```powershell
paperang probe
paperang --json probe
paperang probe --address 04:7F:0E:3A:4F:31
```

Typical data returned:

- model
- address
- transport
- connected flag
- battery percentage
- serial number
- firmware information
- density
- power-off timeout
- hardware info
- printer-reported Bluetooth MAC address
- explicit local-transport support fields for the selected model

## `discover`

Non-printing command that scans for nearby supported devices.

Example:

```powershell
paperang discover
paperang --json discover
```

For `paperang_p1` and `paperang_p2` over BLE, this scans nearby devices. For `paperang_p2` over USB, it reports the connected USB printer when the upstream backend can open it.

## `print text`

Print a shorter text block using the default text rendering path.

Safe validation:

```powershell
paperang print text "test print" --dry-run
```

Useful styling overrides:

- `--font-fit manual|largest-fitting`
- `--font-family sans|mono|serif`
- `--min-font-size INT`
- `--autofit` or `--no-autofit`
- `--orientation normal|rotate-90-cw|rotate-90-ccw`
- `--style-json PATH|-` to load a JSON preset or structured override payload

`largest-fitting` is the human-oriented mode for "start big, then shrink until it fits". If `font_size` is omitted, the renderer starts from a large automatic ceiling and walks down to the biggest fitting result.

For human-oriented styling, start with the nearest preset or example payload when one fits, then override only the fields needed for this one job. Use saved `print_defaults` only when you intentionally want the same behavior for future jobs.

Real printing:

```powershell
paperang print text "test print" --allow-paper-use
paperang print text "test print" --allow-paper-use --feed-mm 6
paperang print text "test print" --allow-paper-use --font-size 40
paperang print text "long shipping label" --dry-run --orientation rotate-90-cw --font-family mono --autofit
paperang --json print text "shipping label" --dry-run --style-json .\label-style.json
```

Example `label-style.json`:

```json
{
	"text": {
		"font_family": "mono",
		"font_size": null,
		"min_font_size": 14,
		"font_fit": "largest-fitting",
		"orientation": "rotate-90-cw",
		"max_length_mm": 45.0,
		"overflow_policy": "shrink-to-fit",
		"break_long_words": false
	}
}
```

Leave `break_long_words` unset or `false` for ordinary word wrapping. Set it to `true` only when you want long unspaced tokens to be chunked by characters instead of forcing a smaller fitted font.

## `print paragraph`

Print a wrapped paragraph with a smaller default font.

Safe validation:

```powershell
paperang print paragraph "This is a test print paragraph." --dry-run
```

The same styling overrides as `print text` are available here, including rotated label rendering and rotated-label autofit.

For ordinary paragraphs, `font_fit="largest-fitting"` is most useful together with `max_length_mm`, because that gives the renderer an actual physical target to fill.

Human-friendly default guidance: labels and tags often want `largest-fitting`, while notes and lists usually want ordinary whole-word wrapping with `break_long_words=false`.

This command is the main entry point for JSON-driven scenario presets such as address labels:

```powershell
paperang --json print paragraph "221B Baker Street London" --dry-run --style-json .\address-label.json
```

Ready-made copies of the scenario payloads shown below ship in `skills/paperang-cli/examples/` in this repository.

That bundle now also includes broader home-note presets such as `fridge-note` and `chore-list`, plus label presets such as `pantry-label`, `cable-tag`, and `storage-bin`.

Example `address-label.json`:

```json
{
	"preset": "address-label",
	"paragraph": {
		"font_size": null,
		"min_font_size": 14,
		"font_fit": "largest-fitting",
		"max_length_mm": 75.0,
		"overflow_policy": "shrink-to-fit",
		"break_long_words": false
	}
}
```

Example `fridge-note.json`:

```json
{
	"preset": "fridge-note",
	"paragraph": {
		"font_size": null,
		"min_font_size": 14,
		"font_fit": "largest-fitting",
		"max_length_mm": 120.0,
		"line_spacing_px": 2,
		"overflow_policy": "shrink-to-fit",
		"break_long_words": false
	}
}
```

Real printing:

```powershell
paperang print paragraph "This is a test print paragraph." --allow-paper-use
paperang print paragraph "Longer test print paragraph..." --allow-paper-use --font-size 22 --feed-mm 5
```

## `print image`

Print a local image file after converting it to a monochrome printer bitstream.

Safe validation:

```powershell
paperang print image .\sample.png --dry-run
paperang --json print image .\sample.png --dry-run --mode sticker
paperang --json print image .\sample.png --dry-run --mode photo
paperang --json print image .\sample.png --dry-run --orientation rotate-90-cw
```

Real printing:

```powershell
paperang print image .\sample.png --allow-paper-use --mode sticker
paperang print image .\sample.png --allow-paper-use --mode photo
paperang print image .\sample.png --allow-paper-use --feed-mm 6
paperang print image .\sample.png --allow-paper-use --conversion edge
paperang --json print image .\banner.png --dry-run --style-json .\logo-strip.json
```

Example `logo-strip.json`:

```json
{
	"preset": "logo-strip",
	"image": {
		"fit_mode": "fit-within-length",
		"max_length_mm": 70.0
	}
}
```

Mode behavior:

- `--mode sticker` is the default and uses a hard threshold intended for logos, line art, stickers, and other already-high-contrast images
- `--mode photo` uses dithering and is the better starting point for photographs and smooth gradients
- `--style-json` can also set `fit_mode` and `max_length_mm` for long strip images that should be constrained along the paper path

## `print compose`

Print wrapped text together with a local image in one combined layout.

`print compose` still uses the ordinary vertical layout path in the current release.

- layout and image defaults can now come from `print_defaults.compose`
- rotated compose printing is not implemented yet

Safe validation:

```powershell
paperang print compose "Product title" .\badge.png --dry-run
paperang --json print compose "Product title" .\badge.png --dry-run --style-json .\product-style.json
```

Useful overrides:

- `--layout text-above|image-above`
- `--font-size INT`
- `--min-font-size INT`
- `--font-fit manual|largest-fitting`
- `--mode sticker|photo`
- `--conversion threshold|edge|dither`
- `--style-json PATH|-` for structured compose layout overrides

As with text and paragraph jobs, a scenario or example payload is usually the best starting point. Use per-invocation overrides for this compose job first, and only save the behavior into `print_defaults.compose` when you explicitly want it to become the future default.

Example `product-style.json`:

```json
{
	"compose": {
		"font_family": "mono",
		"font_size": null,
		"min_font_size": 14,
		"font_fit": "largest-fitting",
		"layout": "image-above",
		"image_mode": "photo",
		"max_length_mm": 55.0,
		"overflow_policy": "report-only",
		"break_long_words": false
	}
}
```

When a dry-run or real print returns length-aware metadata, JSON output now includes estimated paper length information and whether the configured length budget was met.
- `--conversion` remains available as a lower-level override for manual experimentation and debugging
- `--orientation rotate-90-cw|rotate-90-ccw` rotates the source image before it is fit to the active printer width

Current note:

- this path should be treated with the same caution as `print image`
- `--dry-run` validates rendering and packaging, not the final physical result
- transport behavior remains model-specific: `paperang_p1` uses BLE only, while `paperang_p2` uses USB by default or BLE when configured

## `print self-test`

Run the printer's built-in self-test page.

This command is intentionally treated more strictly than ordinary text or image printing because it consumes substantially more paper.

Safe validation:

```powershell
paperang print self-test --dry-run
paperang --json print self-test --dry-run
```

Real self-test:

```powershell
paperang print self-test --allow-large-paper-use
```

Current note:

- this is a high-paper-consumption command
- it exists mainly for explicit device verification or protocol troubleshooting
- `--dry-run` is only a CLI-path validation and warning preview; it does not query a hidden non-printing self-test state from the printer
- prefer `status`, `battery`, `discover`, and ordinary dry-run commands first

## `config show`

Show the resolved config path, whether a file exists there, the active settings, and the supported model list.

## `config path`

Show only the resolved config path.

## `config init`

Write the example config to the resolved default path or to an explicit destination.

Examples:

```powershell
paperang config init
paperang config init --force
paperang config init --path .\my-printer.json
```

## Python Library Note

The CLI and the Python facades intentionally share the same driver, render, and safety logic.

Use `paperang api list` to see which model-specific facades are implemented in the installed package. Use `paperang api p1` or `paperang api p2` when you want a quick read-only view of one model entry. Use [Paperang P1 Python API](p1-api.md) and [Paperang P2 Python API](p2-api.md) for the full library guides.

## Exit Behavior

- Success returns exit code `0`.
- Config failures return exit code `2`.
- Driver and connection failures return non-zero error codes.
- Safety failures, such as trying to print without `--allow-paper-use`, return a dedicated non-zero exit code.

## Transport Note

The standalone BLE transport now attempts one reconnect when a command is issued against a stale disconnected session object.

This is mainly useful for protocol reuse in a longer-lived Python process. Ordinary CLI invocations already start from a fresh process and connection.

For `paperang_p1`, the standalone project currently supports Bluetooth only. A cable/local transport is not exposed because it has not been validated as a usable data path.

For `paperang_p2`, the standalone project supports USB and BLE in software. USB is the default transport when the model resolves to P2, while BLE can be selected explicitly. P2 hardware validation is still pending in this repository.