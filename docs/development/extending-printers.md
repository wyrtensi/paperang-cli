# Extending To More Printers Later

## Current State

Only `paperang_p1` is implemented.

That is a deliberate constraint, not an accidental omission.

## Extension Strategy

When a second printer arrives, do not spread conditional logic through the CLI command files.

Instead:

1. Add a new driver module under `src/paperang_cli/drivers/`.
2. Register it in `registry.py`.
3. Add or adapt protocol modules only if the transport really differs.
4. Extend the config schema and agent contract.
5. Add targeted tests for the new driver.

## What Can Vary By Model

- printer width
- density defaults
- feed calibration
- discovery names
- BLE UUIDs
- packet format
- connection lifecycle
- supported command surface

## Suggested Driver Checklist

For a new model, answer these questions first:

1. Does it use the same transport as P1?
2. Does it use the same packet framing and CRC behavior?
3. Is text rendering width still `384`, or different?
4. Does the model need a different post-connect initialization sequence?
5. Does paragraph wrapping need special handling?
6. Can the same `status` data be queried safely?

## Keep The CLI Stable

Prefer keeping the public CLI stable and model selection internal or configuration-driven.

Examples:

- good: `paperang-cli print text "test print"`
- acceptable: `paperang-cli --config p2.json print text "test print"`
- avoid for now: one top-level command tree per model

That keeps the user and agent contract smaller and easier to automate.