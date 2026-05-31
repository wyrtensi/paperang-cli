# paperang-cli

[![CI](https://img.shields.io/github/actions/workflow/status/wyrtensi/paperang-cli/ci.yml?branch=main&label=CI)](https://github.com/wyrtensi/paperang-cli/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/paperang-cli)](https://pypi.org/project/paperang-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/paperang-cli)](https://pypi.org/project/paperang-cli/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Hardware tested on Windows](https://img.shields.io/badge/hardware_tested-Windows-0078D6?logo=windows11&logoColor=white)

`paperang-cli` is a standalone command-line tool for working with Paperang thermal printers from Python.

It provides a small, script-friendly interface for discovering a printer, checking its status, and printing text or images with explicit safety gates. JSON output is available for automation and agent-driven workflows.

## Current Support

Version `0.1.0` supports:

| Printer | Transport | Status |
| --- | --- | --- |
| Paperang P1 | Bluetooth Low Energy (BLE) | Supported |

Local, cable, and USB data transports are not supported for Paperang P1 in this package.

Real printer communication and physical printing have been tested only on Windows. CI runs compatibility checks on Linux and macOS, but those checks do not prove BLE or printer behavior on those platforms.

## Features

- Discover nearby Paperang printers over BLE
- Check battery level, Bluetooth MAC address, and live printer status
- Print short text or wrapped paragraphs
- Print local images with sticker and photo conversion presets
- Compose text and an image into one print job
- Preview every print path with `--dry-run`
- Emit machine-readable JSON with `--json`
- Use explicit allow flags before any paper-consuming operation

Image and composed printing are available, but remain experimental until you validate physical output on your printer.

## Installation

Python `3.10` or newer is required.

Install the published package from PyPI:

```powershell
python -m pip install paperang-cli
```

For local development, clone the repository and install it in editable mode:

```powershell
git clone https://github.com/wyrtensi/paperang-cli.git
Set-Location "paperang-cli"
python -m pip install -e ".[dev]"
python -m pytest
```

The package installs two equivalent commands:

- `paperang`
- `paperang-cli`

Use `paperang` by default. Use `paperang-cli` if the shorter command conflicts with another executable on your system.

An npm wrapper is also maintained under `npm/`. After its initial npm registry bootstrap, it can be installed globally with:

```powershell
npm install --global paperang-cli
```

The npm wrapper installs the matching Python package from PyPI and exposes the same two commands. Python `3.10` or newer is still required.

## Safe First Run

Start with commands that do not consume paper:

```powershell
paperang --json config show
paperang --json discover
paperang --json probe
paperang --json battery
```

Before a real print, run the matching command with `--dry-run`:

```powershell
paperang --json print text "Hello from Paperang" --dry-run
```

After checking the result, explicitly allow paper use:

```powershell
paperang --json print text "Hello from Paperang" --allow-paper-use
```

Keep the content, image, layout, conversion mode, font size, and feed options the same between dry-run and the real print.

## Printing

### Text

```powershell
paperang --json print text "Shipping label" --dry-run
paperang --json print text "Shipping label" --allow-paper-use
```

### Paragraph

```powershell
paperang --json print paragraph "A longer wrapped note for the printer." --dry-run
paperang --json print paragraph "A longer wrapped note for the printer." --allow-paper-use
```

### Image

Use `--mode sticker` for logos, icons, and line art:

```powershell
paperang --json print image ".\sample.png" --dry-run --mode sticker
paperang --json print image ".\sample.png" --allow-paper-use --mode sticker
```

Use `--mode photo` as a starting point for photographs and smoother grayscale content:

```powershell
paperang --json print image ".\photo.jpg" --dry-run --mode photo
```

Image quality depends on the source file and printer. A successful dry-run validates conversion and packaging, not the final paper output.

### Compose

`print compose` combines wrapped text and an image in one vertical layout:

```powershell
paperang --json print compose "Product label" ".\sample.png" --dry-run --mode sticker
paperang --json print compose "Product label" ".\sample.png" --allow-paper-use --mode sticker
```

Use `--layout image-above` when the image should be printed before the text:

```powershell
paperang --json print compose "Product label" ".\sample.png" --dry-run --layout image-above
```

Compose printing uses the same experimental image conversion pipeline as `print image`.

### Built-In Self-Test

The printer self-test consumes substantially more paper than an ordinary print. Use it only when you explicitly want the printer's built-in diagnostic page:

```powershell
paperang --json print self-test --dry-run
paperang --json print self-test --allow-large-paper-use
```

The self-test dry-run only validates the CLI path and warning payload. It does not query hidden hardware state.

## Commands

| Command | Purpose |
| --- | --- |
| `paperang discover` | Scan for nearby supported printers |
| `paperang battery` | Query the current battery percentage |
| `paperang mac` | Query the printer-reported Bluetooth MAC address |
| `paperang status` | Query live printer information |
| `paperang probe` | Return a combined readiness summary |
| `paperang print text` | Print a short text block |
| `paperang print paragraph` | Print wrapped text |
| `paperang print image` | Print a local image |
| `paperang print compose` | Print text and an image as one job |
| `paperang print self-test` | Print the built-in diagnostic page |
| `paperang config show` | Show the resolved config and active settings |
| `paperang config path` | Show the resolved config path |
| `paperang config init` | Write an example config file |

Run `paperang --help` or `paperang <command> --help` for the available options.

## Configuration

Inspect the active config:

```powershell
paperang --json config show
```

Create an example config:

```powershell
paperang config init
```

Configuration is resolved in this order:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. the per-user default config path
4. built-in defaults

Default paths:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Linux and macOS: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json`, or `~/.config/paperang-cli/paperang-cli.config.json`

See [Configuration](docs/usage/configuration.md) for the full schema.

## Documentation

- [Documentation index](docs/index.md)
- [Installation guide](docs/installation.md)
- [Command reference](docs/usage/commands.md)
- [Configuration](docs/usage/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Agent contract](docs/agents/cli-contract.md)
- [Publishing runbook for agents](docs/agents/publishing.md)

## Project History And Acknowledgements

This standalone CLI builds on earlier reverse engineering and Paperang P1 control work by:

- `ihc童鞋@提不起劲`
- `BroncoTc`

The current `paperang-cli` package is maintained by `wyrtensi`.

## License

This package is available under the [MIT License](LICENSE).
