# Testing Strategy

## Goals

The test suite should validate most logic without requiring a live printer.

That means the default tests focus on:

- config resolution
- driver registry behavior
- render-only logic
- CLI parsing and output shape
- safety gates for destructive commands

## What Is In Automated Tests

- config loading with defaults
- config error paths
- writing example config
- model registry resolution
- feed calibration
- render-only bitstream generation
- CLI `discover`, `status`, and `print` via mocked drivers

## What Is Not In Automated Tests

These checks remain manual hardware smoke tests:

- actual BLE discovery on the host machine
- actual battery query against a printer
- actual print job delivery
- physical paper exit verification

## Running Tests

From `paperang-cli/`:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Validate the distributable Agent Skill and its synchronized repository-local copy:

```powershell
python scripts/check-agent-skill.py
gh skill publish skills --dry-run
```

## Recommended Manual Smoke Sequence

After changing BLE or driver behavior:

1. `paperang-cli --json status`
2. `paperang-cli --json discover`
3. `paperang-cli print text "test print" --dry-run --json`
4. `paperang-cli --json print image ".\\sample.png" --dry-run`
5. only then a real print with `--allow-paper-use`

## Why Dry-Run Matters

Every print consumes paper.

For agent-friendly workflows, `--dry-run` lets you validate:

- config resolution
- parameter parsing
- font sizing
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
