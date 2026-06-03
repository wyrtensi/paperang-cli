# Platform Support Matrix

This document is the single source of truth for cross-platform support claims.
Update it whenever validation status changes.

## Per-printer support

| Printer | Transport | Windows | macOS | Linux |
| --- | --- | --- | --- | --- |
| Paperang P1 | BLE | ✅ Tested (Python 3.14) | ⚠️ Untested (software only) | ⚠️ Untested (software only) |
| Paperang P2 | USB | ✅ Software (libusb/WinUSB) | ⚠️ Untested | ⚠️ Untested |
| Paperang P2 | BLE | ⚠️ Requires paperang-p2-lib 0.4.0rc3+ | ⚠️ Untested | ⚠️ Untested |

## Per-OS validation status

| OS | CI runs | Hardware tested | Last validation date |
| --- | --- | --- | --- |
| Windows | ✅ | ✅ Python 3.14 + P1 BLE | 2026-06-01 |
| macOS | ✅ | ❌ (no hardware in CI) | — |
| Linux | ✅ | ❌ (no hardware in CI) | — |

## Capability detection

Run `paperang --json capabilities` to check what's available on your platform.

The command reports:
- Whether `bleak` (BLE library) is installed and which backend it uses
- Which `paperang-p2-lib` version is installed (0.3.x = USB only, 0.4.0rc3+ = USB + BLE)
- Whether `pyusb` + `libusb` is available for P2 USB
- Platform-specific notes (e.g., bluez on Linux, CoreBluetooth permissions on macOS)

## Platform-specific notes

### Windows

- BLE: bleak uses WinRT backend — works out of the box.
- USB (P2): requires Zadig or WinUSB driver for the printer's USB interface.
- Config: `%APPDATA%\paperang-cli\paperang-cli.config.json`

### macOS

- BLE: bleak uses CoreBluetooth — may require first-run permission prompt.
- USB (P2): requires `brew install libusb`.
- Config: `~/Library/Application Support/paperang-cli/paperang-cli.config.json`
- Note: USB printing on macOS Sonoma+ may require additional code signing.

### Linux

- BLE: bleak uses BlueZ DBus — requires `bluez` service running and user in `bluetooth` group.
- USB (P2): may require udev rules for non-root access (see installation docs).
- Config: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json` or `~/.config/paperang-cli/...`

## Versioned history

- 0.1.9: Initial cross-platform support surface. CI runs on 3 OS × 5 Python.
  macOS config path added. Capability detection command added.
  Real hardware tested only on Windows.
- 0.1.8: Initial macOS/Linux CI matrix without hardware validation.

## Online resources

- **GitHub Pages:** https://wyrtensi.github.io/paperang-cli/ — cross-platform documentation and status
- **PyPI:** https://pypi.org/project/paperang-cli/ — Python package
- **npm:** https://www.npmjs.com/package/paperang-cli — npm wrapper

## Verify your installation

Run the cross-platform check script:

```bash
python scripts/check-cross-platform.py
```

This verifies:
- Python version >= 3.10
- paperang_cli importable
- CLI entrypoint working
- Config path correct for your OS
- Capability detection (bleak, paperang-p2-lib, USB)
