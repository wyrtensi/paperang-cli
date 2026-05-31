# paperang-cli npm wrapper

This npm package installs the matching Python `paperang-cli` release from PyPI and exposes the same two commands:

- `paperang`
- `paperang-cli`

## Requirements

- Node.js `22.14.0` or newer
- npm `11.5.1` or newer
- Python `3.10` or newer

## Install

```powershell
npm install --global paperang-cli
paperang --help
```

The wrapper runs a `postinstall` lifecycle script that installs the matching `paperang-cli` version from PyPI during npm installation. It retries with `--user` if the first pip installation fails.

To inspect the wrapper before allowing lifecycle scripts to run:

```powershell
npm install --global paperang-cli --ignore-scripts
python -m pip install --upgrade paperang-cli
```

Real Bluetooth Low Energy communication and physical printing have been tested only on Windows. CI compatibility checks on Linux and macOS do not prove hardware behavior on those platforms.

See the [main repository](https://github.com/wyrtensi/paperang-cli) and its [security policy](https://github.com/wyrtensi/paperang-cli/blob/main/SECURITY.md) for usage, safety notes, and documentation.
