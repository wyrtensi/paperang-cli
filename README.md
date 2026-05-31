# paperang-cli

[![CI](https://img.shields.io/github/actions/workflow/status/wyrtensi/paperang-cli/ci.yml?branch=main&label=CI)](https://github.com/wyrtensi/paperang-cli/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/paperang-cli?cacheSeconds=300)](https://pypi.org/project/paperang-cli/)
[![npm version](https://img.shields.io/npm/v/paperang-cli)](https://www.npmjs.com/package/paperang-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/paperang-cli?cacheSeconds=300)](https://pypi.org/project/paperang-cli/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Hardware tested on Windows](https://img.shields.io/badge/hardware_tested-Windows-0078D6?logo=windows11&logoColor=white)

`paperang-cli` is a standalone command-line tool and Python package for working with Paperang thermal printers.

It provides a small, script-friendly CLI for discovering a printer, checking its status, and printing text or images with explicit safety gates. JSON output is available for automation and agent-driven workflows.

The package also exposes a model-aware Python API surface. Today that means a supported `PaperangP1` facade plus a read-only API catalog that can mark future models such as `p2` as coming soon without pretending they already work.

## Current Support

The current release ships one supported model and one planned placeholder:

| Printer | Transport | Status |
| --- | --- | --- |
| Paperang P1 | Bluetooth Low Energy (BLE) | Supported |
| Paperang P2 | Local + Bluetooth Low Energy (BLE) | Coming soon, not available yet |

Local, cable, and USB data transports are not supported for Paperang P1 in this package.

The `Paperang P2` row is a roadmap placeholder only. No P2 driver, CLI command set, or public Python facade is available in this package version yet.

Real printer communication and physical printing have been tested only on Windows. CI runs compatibility checks on Linux and macOS, but those checks do not prove BLE or printer behavior on those platforms.

## Features

- Discover nearby Paperang printers over BLE
- Check battery level, Bluetooth MAC address, and live printer status
- Print short text or wrapped paragraphs
- Print local images with sticker and photo conversion presets
- Configure default print styling through JSON config, including font family and 90-degree text or image orientation
- Compose text and an image into one print job
- Preview every print path with `--dry-run`
- Emit machine-readable JSON with `--json`
- Use explicit allow flags before any paper-consuming operation
- Use the `PaperangP1` Python facade for library-style P1 automation
- Inspect model-specific API availability with `paperang api list`

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

An npm wrapper is also maintained under `npm/`. Install it globally with:

```powershell
npm install --global paperang-cli
```

The npm wrapper installs the matching Python package from PyPI and exposes the same two commands. Python `3.10` or newer is still required.

The npm wrapper uses a `postinstall` lifecycle script to run `pip install` for the matching Python package version. See the [security policy](SECURITY.md#npm-postinstall-behavior) for details and an `--ignore-scripts` audit path.

## Agent Skill

This repository includes a portable [Agent Skill](https://agentskills.io/) at `skills/paperang-cli/` and a synchronized repository-local copy at `.agents/skills/paperang-cli/`.

GitHub Copilot discovers it automatically when working from a repository checkout. The same skill can be installed as a personal skill for Codex, Claude Code, GitHub Copilot, and other Agent Skills-compatible clients.

With GitHub CLI `2.90.0` or newer, preview the skill before installation:

```powershell
gh skill preview wyrtensi/paperang-cli paperang-cli
gh skill install wyrtensi/paperang-cli paperang-cli --agent universal --scope user
```

GitHub CLI may note that one hidden skill was excluded. That is expected: `.agents/skills/paperang-cli/` is the synchronized checkout-local copy, while `skills/paperang-cli/` is the public installation source.

GitHub CLI supports host-specific installation for many editors and coding agents. Replace `universal` with a value such as `codex`, `claude-code`, `github-copilot`, `cursor`, `antigravity`, `gemini-cli`, `windsurf`, or another value listed by `gh skill install --help`.

Skills installed through GitHub CLI include source metadata, so they can be checked and updated later:

```powershell
gh skill update paperang-cli --dry-run
gh skill update --all
```

The repository also includes a small Python fallback installer for common personal locations. From a cloned repository:

```powershell
python scripts/install-agent-skill.py --target all
```

Install directly from GitHub on Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/wyrtensi/paperang-cli/main/scripts/install-agent-skill.py | py -3 - --source github --target all
```

Install directly from GitHub on Linux or macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/wyrtensi/paperang-cli/main/scripts/install-agent-skill.py | python3 - --source github --target all
```

Use `--target codex`, `--target claude`, `--target copilot`, `--target cursor`, `--target antigravity`, or `--target agents` to install only one personal copy. Existing copies are preserved unless `--force` is provided. Restart the agent client after installation.

You can also ask an agent:

```text
Install the paperang-cli Agent Skill from:
https://github.com/wyrtensi/paperang-cli/tree/main/skills/paperang-cli
```

The skill is available on all operating systems. Real BLE communication and physical printing remain tested only on Windows.

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

Keep the content, image, layout, conversion mode, font size, font family, orientation, autofit intent, and feed options the same between dry-run and the real print.

## Python API

`paperang-cli` also ships a model-aware Python API layer. Right now the only implemented public facade is `PaperangP1`, while `p2` is intentionally exposed only as a `coming-soon` placeholder in the read-only API catalog.

```python
from paperang_cli import PaperangP1

printer = PaperangP1(address="04:7F:0E:3A:4F:31")
printer.connect()
status = printer.get_status()
preview = printer.print_text("Hello from Paperang", dry_run=True)
```

See [Paperang P1 Python API](docs/usage/p1-api.md) for constructor options, supported methods, safety semantics, and parity notes versus `paperang-p2-lib`.

Use the installed CLI to inspect what is actually available in the current package version:

```powershell
paperang --json api list
paperang --json api p1
paperang --json api p2
```

## Printing

### Text

```powershell
paperang --json print text "Shipping label" --dry-run
paperang --json print text "Shipping label" --allow-paper-use
```

Use rotated label rendering when you want text to run along the paper path:

```powershell
paperang --json print text "Long shipping label" --dry-run --orientation rotate-90-cw --font-family mono --autofit
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

You can also rotate an image 90 degrees before it is fit to the P1 width:

```powershell
paperang --json print image ".\label.png" --dry-run --orientation rotate-90-ccw
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

Rotated compose printing is not implemented yet. `print compose` still uses the ordinary vertical layout path in the current release.

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
| `paperang api list` | List known model-specific Python API entries and their availability |
| `paperang api p1` | Show the supported `PaperangP1` Python API contract |
| `paperang api p2` | Show the `coming-soon` placeholder contract for a future P2 API |
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
- [Paperang P1 Python API](docs/usage/p1-api.md)
- [Configuration](docs/usage/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Agent contract](docs/agents/cli-contract.md)
- [Portable Agent Skill](skills/paperang-cli/SKILL.md)
- [Publishing runbook for agents](docs/agents/publishing.md)
- [Security policy](SECURITY.md)

## Project History And Acknowledgements

This standalone CLI builds on earlier reverse engineering and Paperang P1 control work by:

- `ihc童鞋@提不起劲`
- `BroncoTc`

The current `paperang-cli` package is maintained by `wyrtensi`.

## License

This package is available under the [MIT License](LICENSE).
