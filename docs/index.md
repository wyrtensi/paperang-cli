# paperang-cli Documentation

## What This Project Is

`paperang-cli` is a standalone Python package that lives inside the current repository but is not tied to the root runtime scripts.

It exists to provide:

- a stable command-line interface
- a safe automation surface for humans and agents
- a clean place for tests and documentation
- a driver boundary for future printer models

## Current Scope

Version `0.1.0` supports one model:

- `paperang_p1`

The CLI currently includes:

- `status`
- `discover`
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
2. Read `usage/configuration.md`.
3. Run `paperang status` or `paperang discover` before printing.
4. Use `--dry-run` before any real print.
5. Treat `print image` as experimental until you verify real hardware output.

If you are using the project as an automation or agent surface:

1. Read `agents/cli-contract.md`.
2. Prefer `--json`.
3. Treat printing as destructive.
4. Require explicit approval before `--allow-paper-use`.
5. Require explicit approval before `--allow-large-paper-use` for self-test.

## Documentation Map

- `installation.md`: install and local setup
- `../skills/paperang-cli/SKILL.md`: portable distributable Agent Skill for safe automation
- `usage/commands.md`: command reference and examples
- `usage/configuration.md`: config format, resolution order, and recommended defaults
- `development/architecture.md`: package structure and design rationale
- `development/extending-printers.md`: how to add another printer model later
- `development/testing.md`: test strategy and local verification
- `troubleshooting.md`: common Windows and Bluetooth issues
- `agents/cli-contract.md`: human-readable automation contract
- `agents/cli-contract.json`: machine-readable automation contract
- `agents/publishing.md`: repository bootstrap and release automation runbook
