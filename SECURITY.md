# Security Policy

## Supported Versions

Security fixes are provided for the latest published `paperang-cli` release.

| Version | Supported |
| --- | --- |
| Latest published release | Yes |
| Older releases | No |

## Reporting A Vulnerability

Report security issues through the public [GitHub issue tracker](https://github.com/wyrtensi/paperang-cli/issues).

Do not include secrets, personal information, unredacted Bluetooth MAC addresses, or complete debug logs that contain device identifiers or local filesystem paths. Redact sensitive values before posting. If a report cannot be safely described in public, open an issue with only a short request for a private contact channel.

Please include:

- the affected `paperang-cli` version
- the installation method: PyPI, npm wrapper, or source checkout
- the operating system and Python version
- a minimal reproduction
- the expected and observed behavior

## Security-Relevant Behavior

This project controls a physical printer over Bluetooth Low Energy (BLE). Treat the following as security issues:

- bypassing `--allow-paper-use` or `--allow-large-paper-use`
- consuming paper during `--dry-run`
- connecting to or operating an unintended printer without an explicit address or discovery result
- command execution, dependency confusion, or unsafe package-install behavior
- exposing device identifiers or local data unexpectedly

Ordinary Bluetooth connectivity failures and print-quality problems are bugs, but are not normally security issues.

## npm Postinstall Behavior

The npm package is a wrapper around the Python package. Installing it normally runs [`npm/scripts/postinstall.js`](npm/scripts/postinstall.js).

The postinstall script:

1. finds a compatible Python installation
2. runs `python -m pip install --upgrade paperang-cli==<matching-version>`
3. runs `python -m pip install --force-reinstall --no-deps paperang-cli==<matching-version>`
4. retries the complete sequence with `--user` if the first install scope fails

This means that `npm install --global paperang-cli` also downloads and installs the matching Python package and its runtime dependencies from PyPI.
The second pip command replaces same-version editable installations with the
published wheel without reinstalling heavy runtime dependencies.

To inspect the npm wrapper before allowing lifecycle scripts to run:

```powershell
npm install --global paperang-cli --ignore-scripts
```

After inspection, install the matching Python package explicitly:

```powershell
python -m pip install --upgrade paperang-cli
```

Installing directly from PyPI avoids the npm lifecycle script:

```powershell
python -m pip install paperang-cli
```

## Hardware Support Boundary

Real BLE communication and physical printing have been tested only on Windows. Linux and macOS CI jobs validate software compatibility, not live printer behavior.
