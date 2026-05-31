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
  "discovery_names": ["MiaoMiaoJi", "Paperang", "Paperang_P2S"]
}
```

## Field Meaning

### `model`

Logical printer model identifier used by the driver registry.

In `v0.1.0`, the only valid value is `paperang_p1`.

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

## Working Defaults

The default Paperang P1 profile currently reflects the proven working behavior from the root project:

- width `384`
- density `75`
- post-print feed `5.0 mm`

## Recommended Workflow

1. Run `paperang config init`.
2. Open the reported config path.
3. Replace `macaddress` with your real printer address.
4. Keep `model` as `paperang_p1` for now.
5. Only change `post_print_feed_mm` if you want more or less paper exit after text.

## Why This Is Separate From The Root Config

The root project already has a known-good runtime configuration, but `paperang-cli` is supposed to be a standalone package.

Keeping an independent config means:

- cleaner packaging
- cleaner tests
- no accidental coupling to the legacy root scripts
- a better place to add future multi-model settings later
