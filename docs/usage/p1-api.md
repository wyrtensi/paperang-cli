# Paperang P1 Python API

## Purpose

`paperang-cli` exposes a high-level `PaperangP1` class for scripts that want a library-style API closer to `paperang-p2-lib` without changing the proven P1 print logic in this repository.

The public facade is intentionally thin:

- it delegates to the existing `paperang_cli` driver layer
- it keeps the same safety gates as the CLI
- it does not create a second rendering, BLE, or printing path

Internally, the facade now lives under the model-specific module `paperang_cli.api.p1`. That keeps the package layout ready for future model-specific facades such as `paperang_cli.api.p2` instead of treating one flat `api.py` file as the permanent global API.

At the moment, `paperang_cli.api.p2` is intentionally not implemented. The installed CLI exposes it only as a `coming-soon` placeholder through `paperang api p2` so the package can be explicit about what is and is not available.

Import it with:

```python
from paperang_cli import PaperangP1
```

## Scope And Limits

Current scope:

- Paperang P1 only
- Bluetooth Low Energy only
- high-level status, battery, MAC, text, paragraph, image, compose, and self-test operations
- config-driven styling defaults for text, paragraph, image, and ordinary compose jobs

Out of scope:

- USB, cable, and local data transports
- low-level packet or transport classes as public stable API
- P2-specific features such as QR printing, pickup-code printing, profiles, or USB helpers
- rotated compose rendering

## Quick Start

```python
from paperang_cli import PaperangP1

printer = PaperangP1(address="04:7F:0E:3A:4F:31")
printer.connect()

status = printer.get_status()
print(status.battery_percent)

preview = printer.print_text("Hello from Paperang", dry_run=True)
print(preview.bytes_sent)
```

## Constructor

```python
PaperangP1(
    *,
    address: str | None = None,
    config_path: str | os.PathLike[str] | None = None,
    printer_width: int | None = None,
    print_density: int | None = None,
    post_print_feed_mm: float | None = None,
    discovery_names: list[str] | None = None,
)
```

Constructor behavior:

- if `config_path` is omitted, the class starts from built-in defaults instead of reading the per-user CLI config automatically
- if `config_path` is provided, the file is loaded with the same schema validation used by the CLI
- explicit constructor arguments override values loaded from `config_path`

Important defaults inherited from the existing P1 implementation:

- `print_density=75`
- `post_print_feed_mm=5.0`
- BLE discovery names default to the current CLI list

## Lifecycle

`connect()` and `disconnect()` are library ergonomics, not a second transport implementation.

- `connect()` performs a non-printing readiness check and caches the resolved address for follow-up calls
- `disconnect()` clears that cached address from the facade
- individual operations still flow through the existing driver path, so BLE connect and disconnect behavior remains unchanged from the CLI and driver implementation

## Convenience Properties

`PaperangP1` also exposes two small state helpers for library consumers:

- `address`: the cached ready address if one has been learned, otherwise the configured address if present
- `connected`: `True` when the facade currently has a cached ready address, otherwise `False`

These properties reflect facade state only. They do not expose a long-lived BLE session object.

## Address Override Rules

The facade supports per-call address overrides in addition to the constructor default.

- `connect()` accepts `address=` to run the readiness check against a specific printer
- query methods such as `get_status()` and `get_battery()` also accept `address=`
- print methods also accept `address=` when you want one call to target a different printer than the cached or configured address

Resolution order for one call is:

1. explicit `address=` argument
2. cached address learned by an earlier successful call
3. constructor or config-provided address

If an operation returns a concrete printer address, the facade caches it for later calls.

## Methods

| Method | Returns | Notes |
| --- | --- | --- |
| `discover()` | `list[PrinterDevice]` | BLE scan for supported device names |
| `connect()` | `PaperangP1` | Non-printing readiness check that caches the resolved address; accepts optional `address=` |
| `disconnect()` | `None` | Clears the facade cache only |
| `get_status()` | `PrinterStatus` | Non-printing live status query; accepts optional `address=` |
| `get_battery()` | `BatteryStatus` | Non-printing battery-only query; accepts optional `address=` |
| `get_bluetooth_mac()` | `BluetoothMacStatus` | Non-printing printer-reported Bluetooth MAC query; accepts optional `address=` |
| `get_bt_mac()` | `BluetoothMacStatus` | Compatibility alias for `get_bluetooth_mac()`; accepts optional `address=` |
| `print_text()` | `PrintResult` | Short text print path; accepts optional `address=`, `font_family=`, `min_font_size=`, `autofit=`, and `orientation=` |
| `print_paragraph()` | `PrintResult` | Wrapped paragraph print path; accepts optional `address=`, `font_family=`, `min_font_size=`, `autofit=`, and `orientation=` |
| `print_image()` | `PrintResult` | Image print path with `mode` or `conversion` normalization plus optional `orientation=`; accepts optional `address=` |
| `print_compose()` | `PrintResult` | Combined text-plus-image print path; accepts optional `address=` |
| `print_self_test()` | `PrintResult` | Built-in self-test with the existing large-paper warning; accepts optional `address=` |

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

## Styling Defaults And Result Metadata

When a `config_path` file contains `print_defaults`, the library API uses those values as the baseline for matching print methods.

Resolution order for one styling field is:

1. explicit method argument such as `font_family=` or `orientation=`
2. matching `print_defaults` entry from the loaded config
3. built-in default behavior

Dry-run and real-print `PrintResult` values now include a `styling` object when the driver resolved styling information for that job. For example, rotated text dry-runs report the resolved orientation, generic font family, final font size, and whether autofit actually changed the chosen font size.

Ordinary compose jobs can inherit config defaults such as `layout`, `font_size`, `image_mode`, and `image_conversion`, but rotated compose rendering is still unavailable.

## Configuration Example

```python
from paperang_cli import PaperangP1

printer = PaperangP1(
    config_path="./paperang-cli.config.json",
    print_density=80,
)

preview = printer.print_text(
    "Long shipping label",
    dry_run=True,
    orientation="rotate-90-cw",
    font_family="mono",
    autofit=True,
)

print(preview.styling)
```

## Parity Notes Versus `paperang-p2-lib`

Conceptual overlap:

- high-level class instance
- `connect()` and `disconnect()` entry points
- status and battery queries
- text and image printing methods

Intentional differences in this project:

- the public class is `PaperangP1`, not `PaperangP2`
- the supported model is P1 only
- transport is BLE only
- `print_paragraph()` and `print_compose()` are P1-specific convenience methods in this package
- rotated text, paragraph, and image printing are P1-specific render conveniences in this package
- there is no public QR, pickup-code, USB, or profile API
- rotated compose printing is not implemented yet
- the public facade does not promise stable low-level command coverage

## CLI Inspection

Use this command when you want to inspect the supported Python API from an installed package instead of a repository checkout:

```powershell
paperang --json api list
paperang --json api p1
```

That output is the supported read-only contract for the public `PaperangP1` facade. If you also inspect `paperang --json api p2`, the current package will explicitly report that P2 is still `coming-soon` and unavailable.

Use this page as the fuller library guide for convenience properties, address resolution, and usage notes that do not need to appear in the compact CLI contract output.