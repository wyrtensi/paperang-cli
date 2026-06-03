# Troubleshooting

## Common Issues

### `discover` Finds Nothing

Check:

- printer is powered on
- Bluetooth is enabled on your platform
- the printer is advertising under one of the configured discovery names
- the device is physically nearby

If you already know the MAC address, prefer setting `macaddress` in the config and using `status` or `print` with direct connect.

### `status` Cannot Connect

Check:

- the saved `macaddress`
- Bluetooth state on your platform
- battery level on the printer
- that another app is not holding the printer connection

### Print Happens But Paper Exit Is Wrong

Current P1 behavior uses calibrated feed command units derived from the known-good Android behavior.

If the result is still too short or too long for your paper:

1. adjust `post_print_feed_mm` in the CLI config
2. validate with a minimal text print
3. keep notes per paper type

### Image Print Looks Bad Or Unexpected

This is currently plausible.

The standalone CLI can now convert and send images, but the original project already showed signs that image conversion was a harder problem than plain text.

Try these steps:

1. run `paperang print image ./sample.png --dry-run` first
2. start with `--mode sticker` for logos or `--mode photo` for photographs
3. if that is still not good enough, compare low-level overrides such as `--conversion edge`
4. prefer simple black-and-white source images first when isolating sticker-style issues
5. validate on real paper before assuming the mode is stable for production use

### `print` Refuses To Run

This is expected if you forgot `--allow-paper-use`.

Use:

```bash
paperang print text "test print" --allow-paper-use
```

Or stay safe with:

```bash
paperang print text "test print" --dry-run
```

For self-test, the dedicated flag is different because the built-in page uses substantially more paper:

```bash
paperang print self-test --allow-large-paper-use
```

### JSON Output Missing

`--json` is a global option and must come before the subcommand.

Correct:

```bash
paperang --json status
paperang --json print text "test print" --dry-run
```

Not correct:

```bash
paperang status --json
```

If the short command name conflicts with another tool on the host, switch to `paperang-cli` and keep the same argument order.

## Windows

- Keep Bluetooth enabled in Windows settings.
- Ensure the printer is powered on before `status` or `discover`.
- If Windows has Bluetooth pairing problems, the root repository docs may still be useful because the BLE stack is the same family of behavior.
- `paperang-cli` does not automate pairing in the current release.

## macOS

### Bluetooth permission not granted

Open System Settings → Privacy & Security → Bluetooth, then allow Terminal or your terminal emulator.

### libusb not found

Install via Homebrew:

```bash
brew install libusb
```

### CoreBluetooth scan returns empty

Verify Bluetooth is enabled in System Settings → Bluetooth.

## Linux

### bluez not running

Check the service status and start it:

```bash
systemctl status bluetooth
sudo systemctl start bluetooth
```

### User not in 'bluetooth' group

Add your user to the `bluetooth` group and relogin:

```bash
sudo usermod -aG bluetooth $USER
```

Log out and back in for the group change to take effect.

### udev rules missing

Create `/etc/udev/rules.d/99-paperang.rules` with:

```
SUBSYSTEM=="usb", ATTR{idVendor}=="xxxx", MODE="0666"
```

Replace `xxxx` with the printer's USB vendor ID. Then reload:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Permission denied on USB

Either set udev rules (above) or temporarily allow access:

```bash
sudo chmod 666 /dev/bus/usb/...
```

## When To Fall Back To The Root Scripts

If you are investigating protocol regressions or a behavior not yet represented in `paperang-cli`, the root repository still contains the original working scripts.

That is especially useful while the standalone package is still early in development.
