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

The wrapper installs `paperang-cli==0.1.0` through Python's package installer during npm installation.

Real Bluetooth Low Energy communication and physical printing have been tested only on Windows. CI compatibility checks on Linux and macOS do not prove hardware behavior on those platforms.

See the [main repository](https://github.com/wyrtensi/paperang-cli) for usage, safety notes, and documentation.
