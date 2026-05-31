# Installation

## Supported Runtime

`paperang-cli` is currently intended to run on Python `3.10+`.

The existing repository has already been exercised on Windows with Python `3.14.2`, so that is the current practical reference environment.

## Core Dependencies

The standalone package depends on:

- `bleak` for Bluetooth LE communication
- `click` for the CLI surface
- `numpy`, `Pillow`, `scikit-image`, `scipy`, `numba`, and `pilkit` for rendering

## Install From PyPI

```powershell
python -m pip install paperang-cli
```

That gives you:

- `python -m paperang_cli`
- `paperang`
- `paperang-cli`

## Local Editable Install

From a cloned repository:

```powershell
C:/Users/wyrtensi/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -e ".[dev]"
```

This also installs `pytest`.

## No-Install Development Mode

If you want to validate the package structure before installing, use the `src` directory on `PYTHONPATH`.

```powershell
Set-Location "paperang-cli"
$env:PYTHONPATH = "src"
C:/Users/wyrtensi/AppData/Local/Python/pythoncore-3.14-64/python.exe -m paperang_cli --help
```

## Windows Notes

- Keep Bluetooth enabled.
- Ensure the printer is powered on before `status` or `discover`.
- If Windows has Bluetooth pairing problems, the root repository docs may still be useful because the BLE stack is the same family of behavior.
- `paperang-cli` does not automate pairing in `v0.1.0`.

## First Safe Commands

After installation, start with non-printing commands:

```powershell
paperang discover
paperang status
paperang --json status
```

Then validate rendering without touching paper:

```powershell
paperang print text "test print" --dry-run
paperang --json print paragraph "A longer message for wrapped rendering." --dry-run
paperang --json print image .\sample.png --dry-run
paperang --json print self-test --dry-run
```

If `paperang` conflicts with another executable on the machine, use `paperang-cli` instead. Both commands point to the same Python entry point.

## Current Caveat About Images

Image printing is available in `v0.1.0`, but it should still be treated as experimental until you confirm real output quality on hardware. The original project had more than one image-conversion path, which suggests that different classes of images may need different tuning.
