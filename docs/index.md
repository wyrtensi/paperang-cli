# paperang-cli Documentation

## What This Project Is

`paperang-cli` is a standalone Python package that lives inside the current repository but is not tied to the root runtime scripts.

It exists to provide:

- a stable command-line interface
- documented Python APIs for Paperang P1 and P2 scripts
- a safe automation surface for humans and agents
- a clean place for tests and documentation
- a driver boundary for future printer models

## Current Scope

The current release supports two live models:

- `paperang_p1`
- `paperang_p2`

Paperang P2 is supported in software over USB and BLE, but it has not been hardware-validated in this repository yet.

The CLI currently includes:

- `status`
- `discover`
- `api list`
- `api p1`
- `api p2`
- `battery`
- `mac`
- `probe`
- `print text`
- `print paragraph`
- `print image`
- `print compose`
- `print self-test`
- `config show`
- `config path`
- `config init`

## Read This First

If you are using the project as a person:

1. Read `installation.md`.
2. Read `usage/p1-api.md` or `usage/p2-api.md` if you want the Python library surface.
3. Read `usage/configuration.md`.
4. Read `usage/commands.md` if you want ready-made `--style-json` examples for labels, long image strips, and composed badges.
5. Run `paperang status` or `paperang discover` before printing.
6. Use `--dry-run` before any real print.
7. Treat `print image` as experimental until you verify real hardware output.

If you are using the project as an automation or agent surface:

1. Read `agents/cli-contract.md`.
2. Prefer `--json`.
3. Treat printing as destructive.
4. Require explicit approval before `--allow-paper-use`.
5. Require explicit approval before `--allow-large-paper-use` for self-test.

## Documentation Map

- `installation.md`: install and local setup
- `../skills/paperang-cli/SKILL.md`: portable distributable Agent Skill for safe automation
- `usage/commands.md`: command reference, smart-layout examples, and ready-to-copy `--style-json` payloads
- `usage/p1-api.md`: high-level Python API for `PaperangP1`
- `usage/p2-api.md`: high-level Python API for `PaperangP2`
- `usage/configuration.md`: config format, resolution order, and recommended defaults
- `development/architecture.md`: package structure and design rationale
- `development/extending-printers.md`: how to add another printer model later
- `development/testing.md`: test strategy and local verification
- `troubleshooting.md`: common Windows and Bluetooth issues
- `agents/cli-contract.md`: human-readable automation contract
- `agents/cli-contract.json`: machine-readable automation contract
- `agents/publishing.md`: repository bootstrap and release automation runbook
- `../SECURITY.md`: supported versions, vulnerability reporting, and npm postinstall behavior
