# Installation

## Supported Runtime

`paperang-cli` is currently intended to run on Python `3.10+`.

Real BLE communication and physical printing have been tested only on Windows. Linux and macOS CI checks validate package compatibility and unit tests, not live printer behavior.

## Core Dependencies

The standalone package depends on:

- `bleak` for Bluetooth LE communication
- `click` for the CLI surface
- `numpy`, `Pillow`, `scikit-image`, `scipy`, `numba`, and `pilkit` for rendering

## Windows

### Install From PyPI

```powershell
python -m pip install paperang-cli
```

That gives you:

- `python -m paperang_cli`
- `paperang`
- `paperang-cli`

### Local Editable Install

From a cloned repository:

```powershell
python -m pip install -e ".[dev]"
```

This also installs `pytest`.

### No-Install Development Mode

If you want to validate the package structure before installing, use the `src` directory on `PYTHONPATH`.

```powershell
Set-Location "paperang-cli"
$env:PYTHONPATH = "src"
python -m paperang_cli --help
```

### Windows Notes

- Keep Bluetooth enabled.
- Ensure the printer is powered on before `status` or `discover`.
- For P2 BLE, devices advertising as `Paperang_P2` may expose the `ff00` profile with `A5...5A` protocol frames. The CLI can discover, probe, query diagnostics, and print through that supported path; real P2 BLE output has been physically validated on Windows.
- For P2 USB, `paperang --json capabilities` must report `p2.usb` as available. USB is still an experimental software path. If the capability report says PyUSB is installed but no `libusb-1.0` backend is available, install a loadable libusb backend before retrying USB commands.
- If Windows has Bluetooth pairing problems, the root repository docs may still be useful because the BLE stack is the same family of behavior.
- `paperang-cli` does not automate pairing in the current release.

## macOS

### Install From PyPI

```bash
pip install paperang-cli
```

### Local Editable Install

```bash
pip install --pre -e ".[dev]"
```

### System Dependencies

For P2 USB support, install `libusb` via Homebrew:

```bash
brew install libusb
```

### Bluetooth (BLE)

macOS uses CoreBluetooth. The first time you run a BLE command, macOS may prompt for Bluetooth permission.

### Config Location

```
~/Library/Application Support/paperang-cli/paperang-cli.config.json
```

### macOS Troubleshooting

- **Bluetooth permission not granted:** Open System Settings → Privacy & Security → Bluetooth, then allow Terminal or your terminal emulator.
- **libusb not found:** Run `brew install libusb`.
- **CoreBluetooth scan returns empty:** Verify Bluetooth is enabled in System Settings → Bluetooth.

## Linux

### Install From PyPI

```bash
pip install paperang-cli
```

### Local Editable Install

```bash
pip install --pre -e ".[dev]"
```

### System Dependencies

Debian/Ubuntu:

```bash
sudo apt-get install libusb-1.0-0-dev bluez
```

Fedora:

```bash
sudo dnf install libusb1-devel bluez
```

### Bluetooth (BLE)

BLE requires `bluez` running and your user in the `bluetooth` group:

```bash
sudo usermod -aG bluetooth $USER
```

Log out and back in for the group change to take effect.

### USB (P2)

Non-root USB access may require udev rules. See the Linux troubleshooting section below.

### Config Location

```
$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json
```

or by default:

```
~/.config/paperang-cli/paperang-cli.config.json
```

### Linux Troubleshooting

- **bluez not running:** Check with `systemctl status bluetooth` and start with `sudo systemctl start bluetooth`.
- **User not in 'bluetooth' group:** Run `sudo usermod -aG bluetooth $USER` then log out and back in.
- **udev rules missing:** Create `/etc/udev/rules.d/99-paperang.rules` with:
  ```
  SUBSYSTEM=="usb", ATTR{idVendor}=="xxxx", MODE="0666"
  ```
  Replace `xxxx` with the printer's USB vendor ID. Then reload rules with `sudo udevadm control --reload-rules && sudo udevadm trigger`.
- **Permission denied on USB:** Either set udev rules (above) or temporarily run `sudo chmod 666 /dev/bus/usb/...`.

## First Safe Commands

After installation, start with non-printing commands:

```bash
paperang discover
paperang status
paperang --json status
```

Then validate rendering without touching paper:

```bash
paperang print text "test print" --dry-run
paperang --json print paragraph "A longer message for wrapped rendering." --dry-run
paperang --json print image ./sample.png --dry-run
paperang --json print self-test --dry-run
```

If `paperang` conflicts with another executable on the machine, use `paperang-cli` instead. Both commands point to the same Python entry point.

## Current Caveat About Images

Image printing is available in the current release, but it should still be treated as experimental until you confirm real output quality on hardware. The original project had more than one image-conversion path, which suggests that different classes of images may need different tuning.
