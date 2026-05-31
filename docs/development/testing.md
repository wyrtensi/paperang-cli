# Testing Strategy

## Goals

The test suite should validate most logic without requiring a live printer.

That means the default tests focus on:

- config resolution
- Python API delegation
- driver registry behavior
- render-only logic
- CLI parsing and output shape
- safety gates for destructive commands

## What Is In Automated Tests

- config loading with defaults
- config error paths
- writing example config
- `PaperangP1` facade construction and driver delegation
- model registry resolution
- feed calibration
- render-only bitstream generation
- CLI `discover`, `status`, `api p1`, and `print` via mocked drivers

## What Is Not In Automated Tests

These checks remain manual hardware smoke tests:

- actual BLE discovery on the host machine
- actual battery query against a printer
- actual print job delivery
- physical paper exit verification

## Running Tests

From `paperang-cli/`:

```powershell
python -m pip install -e ".[dev,release]"
python -m pytest
```

Focused library/API checks:

```powershell
python -m pytest tests/test_api.py tests/test_cli.py tests/test_config.py
```

Validate the distributable Agent Skill and its synchronized repository-local copy:

```powershell
python scripts/check-agent-skill.py
gh skill publish skills --dry-run
```

Validate the npm wrapper and release artifacts when changing versioning, packaging, or public distribution behavior:

```powershell
Set-Location npm
npm test
Set-Location ..
python -m build
python -m twine check dist/*
```

## Recommended Manual Smoke Sequence

After changing BLE, driver behavior, or live print rendering, prefer this sequence:

1. `paperang --json discover`
2. `paperang --json probe --address "04:7F:0E:3A:4F:31"`
3. `paperang --json battery --address "04:7F:0E:3A:4F:31"`
4. `paperang --json print text "rotated smoke" --dry-run --address "04:7F:0E:3A:4F:31" --orientation rotate-90-cw --font-family mono --autofit`
5. `paperang --json print image "docs\\assets\\compose-sample.pbm" --dry-run --address "04:7F:0E:3A:4F:31" --orientation rotate-90-cw --mode sticker`
6. `paperang --json print compose "compose smoke" "docs\\assets\\compose-sample.pbm" --dry-run --address "04:7F:0E:3A:4F:31" --mode sticker`
7. only then a real print with `--allow-paper-use`

If discovery is flaky on Windows, a known saved MAC address is still a valid smoke-test path for direct BLE connect.

## Why Dry-Run Matters

Every print consumes paper.

For agent-friendly workflows, `--dry-run` lets you validate:

- config resolution
- parameter parsing
- font sizing
- generic font-family selection
- rotated orientation handling
- rotated-label autofit behavior
- wrapping behavior
- feed calculations
- JSON result structure

without touching hardware.

## Extra Caveat For Images

Image printing should not be treated as solved just because the CLI can produce a bitstream in dry-run mode.

The original repository already hinted at image-specific complexity by carrying more than one conversion approach. That means physical validation still matters for:

- contrast handling
- logos vs photos
- thresholding strategy
- whether `threshold` or `edge` looks better for a given input
