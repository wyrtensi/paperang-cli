# Agent Contract

## Purpose

This file is the canonical human-readable contract for agents and automation that use `paperang-cli`.

The machine-readable counterpart is `cli-contract.json`. The two files describe the same public behavior. Implementation notes are intentionally excluded from the public contract unless an agent must know them to invoke the CLI safely.

## Contract Scope And Stability

This contract documents package version `0.1.0`.

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

The only supported model in package version `0.1.0` is:

- `paperang_p1`

For `paperang_p1`:

- live printer communication uses Bluetooth Low Energy (BLE)
- local, cable, and USB data transports are not supported by this project
- agents must not attempt or document a cable, USB, or local fallback
- real BLE communication and physical printing have been tested only on Windows
- Linux and macOS CI checks do not prove live hardware compatibility

Do not assume that additional models or transports exist merely because the implementation has extension points.

## Config Resolution

Configuration is resolved in this order:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. the per-user default config path
4. built-in defaults

Default paths:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Linux and macOS: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json`, or `~/.config/paperang-cli/paperang-cli.config.json`

Use `paperang --json config show` to inspect the active settings and resolved path.

## Safety Model

### Hardware-safe queries

These commands never consume paper:

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

Agents must run a successful matching dry-run before any real print. A matching dry-run uses the same print subcommand, content, image, layout, conversion mode, font size, and feed options as the intended real print.

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
3. report the dry-run result and ask for explicit approval for the real print
4. add the correct allow flag only after that approval

A missing allow flag is a hard stop. If the CLI returns `SAFETY_ERROR`, do not automatically retry with an allow flag.

Optional flags such as `--font-size`, `--feed-mm`, `--layout`, `--mode`, and `--conversion` do not bypass or weaken the safety gate.

The current implementation permits an allow flag to appear together with `--dry-run`. Dry-run still wins: no printer connection or paper use occurs. Agents should omit allow flags from dry-runs to keep intent clear.

### Experimental image paths

`print image` and `print compose` are experimental because physical output quality still needs manual validation.

For these commands:

- a successful dry-run proves rendering and packaging only
- a successful dry-run does not prove printer readiness or final paper quality
- use `--mode sticker` for logos, stickers, icons, and other high-contrast graphics
- use `--mode photo` for photographs and smoother grayscale content
- use `--conversion` only when deliberately tuning the low-level conversion path
- manually inspect physical output before relying on repeated or automated printing

`print compose` uses the same image pipeline as `print image`. Its own matching compose dry-run is mandatory. A separate `print image ... --dry-run` is useful when isolating image-conversion tuning, but it does not replace the compose dry-run.

### High-paper self-test

`print self-test` consumes substantially more paper than ordinary prints.

Its dry-run is only a CLI-path validation and warning preview. It does not connect to the printer and is not a hidden hardware diagnostic query.

## Dry-run Semantics

| Command | Dry-run validates | Dry-run does not validate |
| --- | --- | --- |
| `print text` | text rendering, bitstream preparation, font size, feed calculation | printer connectivity, printer readiness, physical output |
| `print paragraph` | wrapped rendering, bitstream preparation, font size, feed calculation | printer connectivity, printer readiness, physical output |
| `print image` | local image loading, selected conversion, bitstream preparation, feed calculation | printer connectivity, printer readiness, physical image quality |
| `print compose` | wrapped text, local image loading, selected layout and conversion, combined bitstream preparation, feed calculation | printer connectivity, printer readiness, physical layout quality |
| `print self-test` | command path and high-paper warning payload | printer connectivity, printer readiness, any hardware self-test state |

## Recommended Agent Workflows

### Readiness

For first contact with an unknown device:

1. `paperang --json config show`
2. `paperang --json discover`, or use an explicit `--address` supplied by the user
3. `paperang --json probe`, or use `paperang --json status`
4. `paperang --json battery` when battery state matters

Stop and report any failure before printing.

### Text or paragraph

1. Run the selected `print text ... --dry-run` or `print paragraph ... --dry-run`.
2. Report the dry-run result and ask for explicit approval to consume paper.
3. Repeat the matching command with `--allow-paper-use`.

### Image

1. Run `paperang --json print image ".\sample.png" --dry-run --mode sticker`, or select `--mode photo`.
2. Report that physical quality remains experimental and ask for explicit approval.
3. Repeat the matching command with `--allow-paper-use`.
4. Ask the user to validate physical quality before repeated automation.

### Compose

1. Run the matching `paperang --json print compose "label" ".\sample.png" --dry-run --mode sticker`.
2. Report that the image portion remains experimental and ask for explicit approval.
3. Repeat the matching command with `--allow-paper-use`.
4. Ask the user to validate physical layout quality before repeated automation.

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
| `print text` | `TEXT` | `--address`, `--font-size`, `--feed-mm`, `--dry-run`, `--allow-paper-use` |
| `print paragraph` | `TEXT` | `--address`, `--font-size`, `--feed-mm`, `--dry-run`, `--allow-paper-use` |
| `print image` | `IMAGE_PATH` | `--address`, `--feed-mm`, `--mode sticker\|photo`, `--conversion threshold\|edge\|dither`, `--dry-run`, `--allow-paper-use` |
| `print compose` | `TEXT IMAGE_PATH` | `--address`, `--font-size`, `--feed-mm`, `--layout text-above\|image-above`, `--mode sticker\|photo`, `--conversion threshold\|edge\|dither`, `--dry-run`, `--allow-paper-use` |
| `print self-test` | none | `--address`, `--dry-run`, `--allow-large-paper-use` |

For image and compose rendering, `--conversion` takes precedence over `--mode`.

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
