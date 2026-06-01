# Agent Contract

## Purpose

This file is the canonical human-readable contract for agents and automation that use `paperang-cli`.

The machine-readable counterpart is `cli-contract.json`. The two files describe the same public behavior. Implementation notes are intentionally excluded from the public contract unless an agent must know them to invoke the CLI safely.

## Contract Scope And Stability

This contract documents the current package release.

Stability labels mean:

- `stable`: supported agent-facing behavior in the documented package version
- `experimental`: implemented behavior that remains subject to manual output validation and may change in later releases
- `internal`: an implementation detail that agents must not rely on

Agents must not infer future compatibility guarantees from this file. Before relying on a newly introduced command or option, inspect the installed CLI version with `paperang --version` and consult the matching contract.

## Console Commands

The installed package exposes two equivalent console commands:

- `paperang`
- `paperang-cli`

Prefer `paperang`. Fall back to `paperang-cli` if the short command is unavailable or conflicts on the host.

## Automation Output

Prefer `--json` for machine-driven workflows.

Successful project responses use this envelope:

```json
{
  "status": "ok",
  "result": { ... }
}
```

Project-domain failures use this envelope when `--json` is active:

```json
{
  "status": "error",
  "code": "CONFIG_ERROR",
  "message": "...",
  "exit_code": 2
}
```

Result objects may gain additional fields in later compatible releases. Agents should ignore unknown fields.

Nullable fields are emitted as `null` when the printer does not report a value. Their presence does not mean that the printer returned usable data.

Click-level invocation failures, such as a missing argument, an invalid choice, or a missing image file, may exit with code `2` before the command handler runs. Those usage failures are not guaranteed to use the JSON error envelope even when `--json` is present. Human-readable output is not a stable parsing interface.

## Supported Model And Transport

The current release supports these models:

- `paperang_p1`
- `paperang_p2`

For `paperang_p1`:

- live printer communication uses Bluetooth Low Energy (BLE)
- local, cable, and USB data transports are not supported by this project
- agents must not attempt or document a cable, USB, or local fallback
- real BLE communication and physical printing have been tested only on Windows
- Linux and macOS CI checks do not prove live hardware compatibility

For `paperang_p2`:

- live printer communication supports USB and Bluetooth Low Energy (BLE)
- the public Python facade exposes explicit transport selection with `usb` or `ble`
- cable and generic `local` fallbacks are not separate supported transports in this project
- physical validation for P2 USB and BLE has not been completed in this repository yet
- real BLE communication and physical printing have been tested only on Windows for validated paths
- Linux and macOS CI checks do not prove live hardware compatibility

Do not assume that additional undocumented models or transports exist merely because the implementation has extension points.

## Config Resolution

Configuration is resolved in this order:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. the per-user default config path
4. built-in defaults

Default paths:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Linux and macOS: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json`, or `~/.config/paperang-cli/paperang-cli.config.json`

Use `paperang --json config show` to inspect the active settings, nested `print_defaults`, and resolved path.

The active config may now contain a nested `print_defaults` object for supported-model styling defaults. CLI flags override those defaults for one invocation.

For agent-driven styling, built-in scenarios and shipped examples should be treated as reusable starting points, not as a whitelist and not as a hidden alternate render mode.

Recommended default policy for agents:

- prefer the nearest scenario or example as a base
- if that base is close but not exact, add temporary per-invocation `--style-json` overrides
- if no scenario fits, build a temporary `--style-json` payload from the existing public controls
- leave persistent `print_defaults` unchanged unless the user explicitly asks to make the behavior the default for future jobs
- keep `break_long_words` at `false` unless the user explicitly asks for character-level splitting
- when a long token must fit and the user did not request splitting, prefer whole words and `font_fit=largest-fitting` before enabling character-chunk splitting
- describe expected paper output in human terms and use `estimated_length_mm`, `max_length_mm`, and `fits_length_limit` when present
- answer in the user's language when it is clear, otherwise follow higher-priority environment instructions

## Safety Model

### Hardware-safe queries

These commands never consume paper:

- `api list`
- `api p1`
- `api p2`
- `discover`
- `battery`
- `mac`
- `probe`
- `status`
- `config show`
- `config path`

`config init` also does not communicate with the printer, but it writes a local config file. It refuses to overwrite an existing destination unless `--force` is provided.

### Dry-run commands

Every `print ... --dry-run` flow is non-printing and does not connect to the printer.

Agents must run a successful matching dry-run before any real print. A matching dry-run uses the same print subcommand, content, image, layout, conversion mode, font size, min-font-size, font-fit mode, font family, orientation, autofit intent, and feed options as the intended real print. If the CLI invocation relies on config-driven styling defaults, the dry-run must be executed with the same active config.

### Paper-consuming commands

These commands consume paper:

| Command | Required real-print flag |
| --- | --- |
| `print text` | `--allow-paper-use` |
| `print paragraph` | `--allow-paper-use` |
| `print image` | `--allow-paper-use` |
| `print compose` | `--allow-paper-use` |
| `print self-test` | `--allow-large-paper-use` |

Agents must:

1. obtain an explicit user request before consuming paper
2. run the matching `--dry-run`
3. treat an imperative request such as "print this" as approval for exactly one matching non-self-test real print after a successful dry-run
4. report the dry-run result, but do not ask the same question again when the current request already authorized that print
5. ask for explicit approval when the request is exploratory or ambiguous, when parameters change after the dry-run, or before copies, retries, and repeated prints
6. add the correct allow flag only after approval from the current request or a follow-up

`print self-test` always requires specific follow-up approval after its dry-run because it consumes substantially more paper.

A missing allow flag is a hard stop. If the CLI returns `SAFETY_ERROR`, do not automatically retry with an allow flag.

Optional flags such as `--font-size`, `--min-font-size`, `--font-fit`, `--font-family`, `--autofit`, `--orientation`, `--feed-mm`, `--layout`, `--mode`, and `--conversion` do not bypass or weaken the safety gate.

The current implementation permits an allow flag to appear together with `--dry-run`. Dry-run still wins: no printer connection or paper use occurs. Agents should omit allow flags from dry-runs to keep intent clear.

### Experimental image paths

`print image` and `print compose` are experimental because physical output quality still needs manual validation.

For these commands:

- a successful dry-run proves rendering and packaging only
- a successful dry-run does not prove printer readiness or final paper quality
- use `--mode sticker` for logos, stickers, icons, and other high-contrast graphics
- use `--mode photo` for photographs and smoother grayscale content
- use `--conversion` only when deliberately tuning the low-level conversion path
- use `--orientation rotate-90-cw|rotate-90-ccw` when the image should run along the paper path
- manually inspect physical output before relying on repeated or automated printing

`print compose` uses the same image pipeline as `print image`. Its own matching compose dry-run is mandatory. A separate `print image ... --dry-run` is useful when isolating image-conversion tuning, but it does not replace the compose dry-run.

Rotated text and paragraph printing are supported in the current release. Rotated compose printing is not implemented yet.

### High-paper self-test

`print self-test` consumes substantially more paper than ordinary prints.

Its dry-run is only a CLI-path validation and warning preview. It does not connect to the printer and is not a hidden hardware diagnostic query.

## Dry-run Semantics

| Command | Dry-run validates | Dry-run does not validate |
| --- | --- | --- |
| `print text` | text rendering, selected font family, selected orientation, bitstream preparation, font size, feed calculation, estimated length reporting when the active style carries a length budget | printer connectivity, printer readiness, physical output |
| `print paragraph` | wrapped rendering, selected font family, selected orientation, bitstream preparation, font size, feed calculation, estimated length reporting when the active style carries a length budget | printer connectivity, printer readiness, physical output |
| `print image` | local image loading, selected conversion, selected orientation, bitstream preparation, feed calculation, estimated length reporting and length-fit validation when configured | printer connectivity, printer readiness, physical image quality |
| `print compose` | wrapped text, local image loading, selected layout and conversion, combined bitstream preparation, feed calculation, estimated length reporting and length-limit evaluation when configured | printer connectivity, printer readiness, physical layout quality |
| `print self-test` | command path and high-paper warning payload | printer connectivity, printer readiness, any hardware self-test state |

When a print result includes `estimated_length_mm`, `max_length_mm`, or `fits_length_limit`, agents should surface those fields directly instead of re-estimating paper usage from pixels.

For rotated `rotate-90-cw` and `rotate-90-ccw` text and image jobs, those length fields now use the head-width calibration value `printable_width_mm` when it is available. Ordinary orientation jobs and ordinary compose length planning continue to use `advance_mm_per_px`.

## Recommended Agent Workflows

### Readiness

For first contact with an unknown device:

1. `paperang --json config show`
2. `paperang --json discover`, or use an explicit `--address` supplied by the user
3. `paperang --json probe`, or use `paperang --json status`
4. `paperang --json battery` when battery state matters

Stop and report any failure before printing.

### Library API inspection

When an automation or agent needs to know what Python API surface is actually supported by the installed package:

1. Run `paperang --json api list`.
2. Choose the relevant model entry, such as `paperang --json api p1` or `paperang --json api p2`.
3. Read the supported constructor options, methods, styling support, and safety requirements for the selected model.
4. Do not assume parity with `paperang-p2-lib` features that are not listed in the matching model contract.

### Text or paragraph

1. Prefer the nearest scenario or example as a base when it fits, otherwise build a temporary `--style-json` payload from the existing public controls.
2. Keep `break_long_words` at `false` unless the user explicitly asks for character-level splitting.
3. Run the selected `print text ... --dry-run` or `print paragraph ... --dry-run`.
4. When using rotated text or JSON-driven styling, keep `--orientation`, `--font-family`, `--min-font-size`, `--font-fit`, `--autofit`, and any `--style-json` payload identical between dry-run and real print.
5. Report the dry-run result in human terms, including expected paper length when the result exposes it.
6. If the current request was exploratory or ambiguous, ask for explicit approval to consume paper.
7. Repeat the matching command with `--allow-paper-use` after approval from the current request or a follow-up.

### Image

1. Run `paperang --json print image ".\sample.png" --dry-run --mode sticker`, or use the matching `--style-json` payload when a preset or structured override controls orientation or length fitting.
2. Include `--orientation` when you want the image rotated along the paper path, and keep the same `--style-json` payload for the real print.
3. Report that physical quality remains experimental.
4. If the current request was exploratory or ambiguous, ask for explicit approval.
5. Repeat the matching command with `--allow-paper-use` after approval from the current request or a follow-up.
6. Ask the user to validate physical quality before repeated automation.

### Compose

1. Prefer the nearest scenario or example as a base when it fits, otherwise build a temporary `--style-json` payload from the existing public controls.
2. Keep `break_long_words` at `false` unless the user explicitly asks for character-level splitting in the text section.
3. Run the matching `paperang --json print compose "label" ".\sample.png" --dry-run --mode sticker`, or the matching `--style-json` payload when layout or length handling is JSON-driven.
4. Report that the image portion remains experimental and describe the expected paper result in human terms.
5. If the current request was exploratory or ambiguous, ask for explicit approval.
6. Repeat the matching command with `--allow-paper-use` after approval from the current request or a follow-up.
7. Ask the user to validate physical layout quality before repeated automation.

### Self-test

1. Prefer `status`, `battery`, `probe`, and ordinary print dry-runs first.
2. Run `paperang --json print self-test --dry-run`.
3. Warn that the built-in self-test consumes substantially more paper and ask for explicit approval specifically for self-test.
4. Run `paperang --json print self-test --allow-large-paper-use`.

## Global Options

| Option | Purpose |
| --- | --- |
| `--json` | Emit machine-readable JSON output. Preferred for agents. |
| `--config PATH` | Use a specific JSON config file. |
| `--debug` | Enable verbose diagnostic logging. Use when BLE investigation requires it. |
| `--version` | Show the installed CLI version. |

## Command Reference

### API inspection command

| Command | Purpose | Options | Result |
| --- | --- | --- | --- |
| `api list` | List known model-specific API entries and whether they are implemented in the current package version. | none | array of entries with `api`, `model`, `available`, `status`, nullable `class_name`, and nullable `planned_class_name` |
| `api p1` | Show the supported `PaperangP1` Python API surface, constructor options, method list, styling support, safety requirements, and parity gaps. | none | `api`, `availability`, nullable `class_name`, nullable `planned_class_name`, nullable `import_path`, nullable `implementation_module`, `model`, nullable `transport`, `config_loading`, `constructor_options`, `methods`, `styling_support`, `safety`, `unsupported_parity_gaps` |
| `api p2` | Show the supported `PaperangP2` Python API surface, including explicit USB or BLE transport selection and current parity gaps. | none | same fields as `api p1`, populated for the live `PaperangP2` facade |

### Query commands

| Command | Purpose | Options | Result |
| --- | --- | --- | --- |
| `discover` | Scan BLE for supported device names. | none | list of devices with `name`, `address`, nullable `rssi`, and nullable `details` |
| `battery` | Query battery percentage without printing. | optional `--address` | `model`, `address`, `transport`, `connected`, nullable `battery_percent` |
| `mac` | Query printer-reported Bluetooth MAC without printing. | optional `--address` | `model`, `address`, `transport`, `connected`, nullable `bluetooth_mac` |
| `status` | Query live printer status without printing. | optional `--address` | `model`, `address`, `transport`, `connected`, nullable live status fields, and `raw` |
| `probe` | Combine `status` with printer-reported Bluetooth MAC and explicit local-transport status. | optional `--address` | status fields plus nullable `bluetooth_mac`, `local_transport_supported`, `local_transport_note`, and `raw` |

Live status fields are:

- `battery_percent`
- `serial_number`
- `firmware_version`
- `hardware_info`
- `density`
- `power_off_time`

Agents must read runtime values rather than assume fixed device values.

### Print commands

| Command | Arguments | Options |
| --- | --- | --- |
| `print text` | `TEXT` | `--address`, `--font-size`, `--font-family sans\|mono\|serif`, `--min-font-size`, `--font-fit manual\|largest-fitting`, `--autofit`, `--no-autofit`, `--orientation normal\|rotate-90-cw\|rotate-90-ccw`, `--style-json PATH\|-`, `--feed-mm`, `--dry-run`, `--allow-paper-use` |
| `print paragraph` | `TEXT` | `--address`, `--font-size`, `--font-family sans\|mono\|serif`, `--min-font-size`, `--font-fit manual\|largest-fitting`, `--autofit`, `--no-autofit`, `--orientation normal\|rotate-90-cw\|rotate-90-ccw`, `--style-json PATH\|-`, `--feed-mm`, `--dry-run`, `--allow-paper-use` |
| `print image` | `IMAGE_PATH` | `--address`, `--orientation normal\|rotate-90-cw\|rotate-90-ccw`, `--style-json PATH\|-`, `--feed-mm`, `--mode sticker\|photo`, `--conversion threshold\|edge\|dither`, `--dry-run`, `--allow-paper-use` |
| `print compose` | `TEXT IMAGE_PATH` | `--address`, `--font-size`, `--min-font-size`, `--font-fit manual\|largest-fitting`, `--style-json PATH\|-`, `--feed-mm`, `--layout text-above\|image-above`, `--mode sticker\|photo`, `--conversion threshold\|edge\|dither`, `--dry-run`, `--allow-paper-use` |
| `print self-test` | none | `--address`, `--dry-run`, `--allow-large-paper-use` |

For `print text`, `print paragraph`, `print image`, and `print compose`, `--style-json` accepts a JSON file path or `-` for stdin. The payload can select a preset and carry an operation-specific override block. Explicit CLI flags still take precedence over the JSON payload.

For `print text`, `print paragraph`, and `print compose`, `font_fit=largest-fitting` means the renderer searches downward for the biggest fitting font size. If `font_size` is omitted or null, the search starts from a large automatic ceiling.

For image and compose rendering, `--conversion` takes precedence over `--mode`. When `--mode`, `--layout`, or other styling values are omitted, the current release may inherit those values from config-driven print defaults or from the selected JSON preset.

### Config commands

| Command | Purpose | Options | Result |
| --- | --- | --- | --- |
| `config show` | Show resolved path, file presence, active config, and supported model list. | none | `config_path`, `config_exists`, `config`, `supported_models` |
| `config path` | Show the resolved config path. | none | `config_path` |
| `config init` | Write an example config. | optional `--path`, optional `--force` | `config_path` |

## Exit Codes

Project-domain exit codes:

| Code | Meaning | Agent behavior |
| --- | --- | --- |
| `0` | success | continue |
| `2` | config error | stop and report the configuration problem |
| `3` | driver error | stop and report the driver problem |
| `4` | printer not found | stop and report that the configured or requested printer was not reachable |
| `5` | safety error | stop; do not add an allow flag or retry without explicit user approval |

As noted above, Click-level usage validation can also return exit code `2`.

## Internal Details Outside The Contract

Agents must not depend on internal protocol and rendering choices such as:

- BLE library selection
- post-connect warm-up sequencing
- reconnect behavior for reused transport objects
- calibrated feed-unit conversion
- default printer width and density values
- internal driver boundaries

Use public commands and runtime query results instead.
