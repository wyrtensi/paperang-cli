# Paperang P2 Python API

## Purpose

`paperang-cli` exposes a high-level `PaperangP2` class for scripts that want the repository's CLI-aligned render, dry-run, and safety behavior on top of a live P2 transport backend.

The physically validated P2 path in this repository is BLE FF00/A5 on Windows. Some P2 units advertise as `Paperang_P2` and expose that `ff00` BLE profile with `A5...5A` protocol frames; this repository can discover, connect, query diagnostics, and print through RawBT-style raster packets over that profile.

The USB path remains an experimental software path that uses `mdj2812/paperang-p2-lib` and references `mdj2812/paperang-p2-usb`; it is not the validated P2 path in this repository yet.

Import it with:

```python
from paperang_cli import PaperangP2
```

## Scope And Limits

Current scope:

- Paperang P2 only
- BLE transport for the validated FF00/A5 path, with an experimental USB transport still available in software
- high-level status, battery, MAC, text, paragraph, image, compose, and self-test operations
- config-driven styling defaults for text, paragraph, image, and ordinary compose jobs

Out of scope:

- low-level transport or packet classes as public stable API
- upstream extras such as QR printing, pickup-code printing, and profile-specific commands
- rotated compose rendering
- hardware-validation claims for P2 USB in this repository

## Quick Start

```python
from paperang_cli import PaperangP2

printer = PaperangP2(transport="ble", address="04:7F:0E:3A:4F:31")
status = printer.get_status()
preview = printer.print_text("Hello from Paperang P2", dry_run=True)

print(status.battery_percent)
print(preview.bytes_sent)
```

The experimental USB path is still exposed for research and backward compatibility:

```python
printer = PaperangP2(transport="usb")
```

## Constructor

```python
PaperangP2(
    *,
    address: str | None = None,
    transport: str | None = None,
    config_path: str | os.PathLike[str] | None = None,
    printer_name: str | None = None,
    printer_width: int | None = None,
    print_density: int | None = None,
    post_print_feed_mm: float | None = None,
    discovery_names: list[str] | None = None,
)
```

Constructor behavior:

- if `config_path` is omitted, the class starts from built-in defaults instead of reading the per-user CLI config automatically
- if `config_path` is provided, the file is loaded with the same schema validation used by the CLI
- if the config defines `printers`, pass `printer_name="..."` to select one named profile
- explicit constructor arguments override values loaded from `config_path`
- the constructor always forces `model="paperang_p2"`
- if `transport` is omitted, the facade currently defaults to USB for backward compatibility; use `transport="ble"` for the validated P2 path

Important defaults inherited from the current P2 implementation:

- `printer_width=576` when omitted
- `print_density=95`
- `calibration.advance_mm_per_px=0.08472`, based on an approximately `61 mm` printed distance over `720 px`
- built-in text defaults are scaled from the P1 `384 px` head to the P2 `576 px` head, so ordinary P2 text starts at `54 px` instead of the shared renderer's `36 px`; explicit `font_size=` values are still used as exact pixel sizes
- `post_print_feed_mm=5.0`
- BLE discovery names default to the current CLI list when BLE transport is selected

## Transport Selection

`PaperangP2` has one validated live transport and one experimental software transport:

- `transport="ble"`: validated on Windows for FF00/A5 devices advertising as `Paperang_P2`. It uses the provided `address`, configured `macaddress`, or the BLE discovery path. The driver first tries the upstream Nordic UART profile and then falls back to the `ff00` profile; `probe` reports `protocol=a5` when the FF00 device answers the `A5...5A` probe.
- `transport="usb"`: experimental software path. `address` is ignored and `discover()` reports the connected USB printer when the upstream backend can open it.

Config files can select the same behavior with `"model": "paperang_p2"` and optional `"transport": "usb"` or `"transport": "ble"`.

## Lifecycle

`connect()` and `disconnect()` are library ergonomics, not a second transport implementation.

- `connect()` performs a non-printing readiness check and caches the resolved address for follow-up calls
- `disconnect()` clears that cached address from the facade
- individual operations still flow through the existing driver path, so transport setup, dry-run behavior, and safety checks stay aligned with the CLI

## Convenience Properties

`PaperangP2` also exposes two small state helpers for library consumers:

- `address`: the cached ready address if one has been learned, otherwise the configured address if present
- `connected`: `True` when the facade currently has a cached ready address, otherwise `False`

These properties reflect facade state only. They do not expose a long-lived USB or BLE session object.

## Methods

| Method | Returns | Notes |
| --- | --- | --- |
| `discover()` | `list[PrinterDevice]` | BLE discovery, or USB presence check when the experimental USB transport is selected |
| `connect()` | `PaperangP2` | Non-printing readiness check that caches the resolved address |
| `disconnect()` | `None` | Clears the facade cache only |
| `get_status()` | `PrinterStatus` | Non-printing live status query; accepts optional `address=` |
| `get_battery()` | `BatteryStatus` | Non-printing battery-only query; accepts optional `address=` |
| `get_bluetooth_mac()` | `BluetoothMacStatus` | Non-printing printer-reported Bluetooth MAC query; accepts optional `address=` |
| `get_bt_mac()` | `BluetoothMacStatus` | Compatibility alias for `get_bluetooth_mac()` |
| `print_text()` | `PrintResult` | Short text print path with optional `font_family=`, `font_size=`, `min_font_size=`, `font_fit=`, `autofit=`, `orientation=`, and `feed_mm=` |
| `print_paragraph()` | `PrintResult` | Wrapped paragraph print path with the same styling controls as `print_text()` |
| `print_image()` | `PrintResult` | Image print path with `mode` or `conversion` normalization plus optional `orientation=` |
| `print_compose()` | `PrintResult` | Combined text-plus-image print path with `layout=`, `font_size=`, `min_font_size=`, `font_fit=`, `mode=`, `conversion=`, and `feed_mm=` |
| `print_self_test()` | `PrintResult` | Built-in self-test with the existing large-paper warning |

The return types are the same dataclasses used by the CLI and driver layers.

## Safety Model

Real printing is intentionally not implicit.

- `print_text()`, `print_paragraph()`, `print_image()`, and `print_compose()` require `allow_paper_use=True` unless `dry_run=True`
- `print_self_test()` requires `allow_large_paper_use=True` unless `dry_run=True`
- `dry_run=True` stays non-printing and does not connect to the printer

Image-related cautions still apply in the library API:

- `mode="sticker"` is the better starting point for logos, icons, and line art
- `mode="photo"` maps to dithering and is the better starting point for photos or smooth gradients
- `orientation="rotate-90-cw"` or `orientation="rotate-90-ccw"` is supported for `print_text()`, `print_paragraph()`, and `print_image()`
- `autofit=True` is mainly useful for rotated text and rotated paragraph jobs
- `print_image()` and `print_compose()` remain experimental until you validate physical output on your hardware

P2 BLE FF00/A5 printing is physically validated on Windows. P2 USB remains experimental and is not the supported P2 path.

## Hardware Smoke Checklist

Use this checklist only when you have a real P2 printer on hand. A successful BLE FF00/A5 pass validates one device on one Windows host path; it does not validate USB, macOS, or Linux behavior.

1. Set `"model": "paperang_p2"`, `"transport": "ble"`, and the target BLE address in config, or create the facade as `PaperangP2(transport="ble", address="04:7F:0E:3A:4F:31")`.
2. Run `paperang --json discover` if you still need to confirm the BLE address.
3. Run `paperang --json probe`.
4. Run `paperang --json battery`.
5. Run `paperang --json print text "P2 BLE smoke" --dry-run`.
6. Only if that dry-run looks correct, repeat the same job once with `--allow-paper-use`.

If `probe` reports `hardware_info` containing `BLE profile ff00` and `protocol=a5`, the device has been found and connected through the validated A5 packet family. Real printing through that BLE profile uses RawBT-style `05 1B` raster chunks.

If you are validating the Python facade instead of the CLI, keep the same order: start with `PaperangP2(transport="ble", address="...")`, call a non-printing method such as `get_status()` or `get_battery()` first, then run one matching `dry_run=True` preview before any real print.

For USB research, use `transport="usb"` explicitly and treat any result as experimental until you validate the backend and hardware behavior on that host.

## Styling Defaults And Result Metadata

When a `config_path` file contains `print_defaults`, the library API uses those values as the baseline for matching print methods.

Resolution order for one styling field is:

1. explicit method argument such as `font_fit=` or `orientation=`
2. matching `print_defaults` entry from the loaded config
3. built-in default behavior

Dry-run and real-print `PrintResult` values include a `styling` object when the driver resolved styling information for that job.

When a dry-run returns `estimated_length_mm`, `max_length_mm`, or `fits_length_limit`, surface those values directly so the caller can describe the expected paper result in human terms instead of inventing a separate estimate.

## Parity Notes Versus `paperang-p2-lib`

Conceptual overlap:

- the same P2 model
- supported BLE transport plus an experimental USB software path
- status, battery, and Bluetooth MAC queries
- text and image printing routed to a live P2 backend

Intentional differences in this project:

- `PaperangP2` routes through this repository's driver, render, dry-run, and safety layers instead of exposing the upstream transport API directly
- upstream extras such as QR printing, pickup-code printing, and profile-specific commands are not part of this public facade yet
- `print_paragraph()` and `print_compose()` are convenience methods specific to this package
- rotated compose printing is not implemented yet
- P2 BLE FF00/A5 is physically validated on Windows; P2 USB remains experimental and is not the supported P2 path

## CLI Inspection

Use this command when you want to inspect the supported Python API from an installed package instead of a repository checkout:

```powershell
paperang --json api list
paperang --json api p2
```

That output is the supported read-only contract for the public `PaperangP2` facade. Use [Paperang P1 Python API](p1-api.md) when you need the P1-only BLE surface.
