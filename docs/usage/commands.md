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
- current status such as `available` or `coming-soon`
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

Non-printing command that shows the placeholder contract for a future `PaperangP2`-style facade.

Examples:

```powershell
paperang api p2
paperang --json api p2
```

Typical data returned:

- `coming-soon` availability status
- explicit note that no public P2 facade is implemented yet
- planned facade name
- empty constructor and method lists
- parity gaps that explain what is still unavailable

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

Non-printing command that runs the usual live BLE status query plus the printer-reported Bluetooth MAC query and returns them in one summary payload.

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
- explicit note that local/cable mode is not supported for `paperang_p1` in this project

## `discover`

Non-printing command that scans for nearby supported devices.

Example:

```powershell
paperang discover
paperang --json discover
```

## `print text`

Print a shorter text block using the default text rendering path.

Safe validation:

```powershell
paperang print text "test print" --dry-run
```

Useful styling overrides:

- `--font-family sans|mono|serif`
- `--min-font-size INT`
- `--autofit` or `--no-autofit`
- `--orientation normal|rotate-90-cw|rotate-90-ccw`

Real printing:

```powershell
paperang print text "test print" --allow-paper-use
paperang print text "test print" --allow-paper-use --feed-mm 6
paperang print text "test print" --allow-paper-use --font-size 40
paperang print text "long shipping label" --dry-run --orientation rotate-90-cw --font-family mono --autofit
```

## `print paragraph`

Print a wrapped paragraph with a smaller default font.

Safe validation:

```powershell
paperang print paragraph "This is a test print paragraph." --dry-run
```

The same styling overrides as `print text` are available here, including rotated label rendering and rotated-label autofit.

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
```

Mode behavior:

- `--mode sticker` is the default and uses a hard threshold intended for logos, line art, stickers, and other already-high-contrast images
- `--mode photo` uses dithering and is the better starting point for photographs and smooth gradients
- `--conversion` remains available as a lower-level override for manual experimentation and debugging
- `--orientation rotate-90-cw|rotate-90-ccw` rotates the source image before it is fit to the fixed P1 print width

Current note:

- image printing is available but still experimental
- the original project had multiple image-conversion paths
- `--mode photo` is still experimental because physical quality depends on the source image and printer behavior
- you should validate physical output on real hardware before treating it as stable
- `--dry-run` validates conversion and packaging, not the final printed visual quality

## `print compose`

`print compose` still uses the ordinary vertical layout path in the current release.

- layout and image defaults can now come from `print_defaults.compose`
- rotated compose printing is not implemented yet

Print one combined layout made from wrapped text plus a local image.

Safe validation:

```powershell
paperang print compose "test print label" .\sample.png --dry-run
paperang --json print compose "test print label" .\sample.png --dry-run --layout image-above --mode photo
```

Real printing:

```powershell
paperang print compose "test print label" .\sample.png --allow-paper-use
paperang print compose "test print label" .\sample.png --allow-paper-use --layout image-above
paperang print compose "test print label" .\sample.png --allow-paper-use --mode photo
```

Compose behavior:

- `TEXT` is rendered as wrapped text
- `IMAGE_PATH` is converted with the same image pipeline used by `print image`
- `--layout text-above` is the default
- `--layout image-above` swaps the vertical order
- `--mode` and `--conversion` affect only the image part of the composed print

Current note:

- this path should be treated with the same caution as `print image`
- `--dry-run` validates rendering and packaging, not the final physical result
- for `paperang_p1`, real hardware communication still goes through Bluetooth only

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

The CLI and the Python `PaperangP1` facade intentionally share the same driver, render, and safety logic.

Use `paperang api list` to see which model-specific facades are implemented in the installed package. Use `paperang api p1` or `paperang api p2` when you want a quick read-only view of one model entry. Use [Paperang P1 Python API](p1-api.md) for the full library guide.

## Exit Behavior

- Success returns exit code `0`.
- Config failures return exit code `2`.
- Driver and connection failures return non-zero error codes.
- Safety failures, such as trying to print without `--allow-paper-use`, return a dedicated non-zero exit code.

## Transport Note

The standalone BLE transport now attempts one reconnect when a command is issued against a stale disconnected session object.

This is mainly useful for protocol reuse in a longer-lived Python process. Ordinary CLI invocations already start from a fresh process and connection.

For `paperang_p1`, the standalone project currently supports Bluetooth only. A cable/local transport is not exposed because it has not been validated as a usable data path.