# paperang-cli Agent Notes

This subproject is intended to be usable by people and by automation.

## Canonical Agent Contract

Read these files before driving the CLI:

- `docs/agents/cli-contract.md`
- `docs/agents/cli-contract.json`

## Safe Invocation Rules

Both `paperang` and `paperang-cli` are valid console commands.

Prefer `paperang` unless the host already has a conflicting executable with that name.

- Prefer `--json` for machine-readable output.
- Prefer `battery`, `mac`, `probe`, `status`, and `discover` before any printing command.
- Require a successful matching `print ... --dry-run` before a real print. Keep the same content, image, layout, conversion mode, font size, and feed options.
- Real `print text`, `print paragraph`, `print image`, and `print compose` commands require `--allow-paper-use`.
- `print self-test` requires `--allow-large-paper-use` and should be treated as a high-paper-consumption action.
- Do not assume additional models exist yet. `paperang_p1` is the only supported model in v0.1.0.

Image printing should currently be treated as experimental. Agents should assume that physical output quality may still need manual validation and user confirmation.

`print compose` should be treated with the same caution as `print image`, because its image section goes through the same conversion pipeline.

For `print image`, prefer:

- `--mode sticker` for logos, stickers, icons, and other high-contrast graphics
- `--mode photo` for photographs and smoother grayscale content
- `--conversion` only when deliberately tuning a low-level conversion path

## Config Resolution

Configuration is resolved in this order:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. the per-user default config path
4. built-in defaults

Default config paths:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Linux and macOS: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json`, or `~/.config/paperang-cli/paperang-cli.config.json`

## Publishing

Before preparing a release or changing GitHub Actions publishing automation, read:

- `docs/agents/publishing.md`

## Hardware Caution

`print text`, `print paragraph`, `print image`, `print compose`, and `print self-test` consume paper.

The built-in self-test consumes substantially more paper than ordinary print commands.

If an agent is operating without explicit user approval for paper use, it should stay in `battery`, `mac`, `status`, `discover`, and `--dry-run` flows.

`print self-test --dry-run` is not a hidden hardware self-check. It only validates the CLI path and returns the high-paper-use warning without sending the printer self-test command.

If a longer-lived Python process reuses the transport object after disconnect, the transport now attempts one reconnect before failing the next query.

For `paperang_p1`, local/cable mode is not available in this project. Live communication currently uses Bluetooth only.
