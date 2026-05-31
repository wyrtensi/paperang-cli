# Architecture

## Design Goals

`paperang-cli` is intentionally not a thin symlink over the root scripts.

The new package needs:

- a stable CLI surface
- testable code boundaries
- explicit configuration loading
- a model registry for future printers
- a place for agent contracts and machine-readable outputs

## High-Level Layers

### Public Library API Layer

Files:

- `src/paperang_cli/api/__init__.py`
- `src/paperang_cli/api/p1.py`
- `src/paperang_cli/api/contract.py`

Responsibilities:

- expose the synchronous `PaperangP1` facade for library consumers
- present a P1-only surface that is easier to script from Python
- keep library-style ergonomics close to `paperang-p2-lib` where P1 features overlap
- reuse the existing driver, render, and safety paths instead of creating a second print implementation
- keep future model facades additive, so `p2.py` or `p3.py` can live beside `p1.py` instead of overloading a single global `api.py`

### CLI Layer

Files:

- `src/paperang_cli/cli.py`
- `src/paperang_cli/commands/`

Responsibilities:

- argument parsing
- global options
- JSON vs human output
- safe command semantics
- read-only inspection of the supported Python API contract

### Service and Utility Layer

Files:

- `src/paperang_cli/config.py`
- `src/paperang_cli/errors.py`
- `src/paperang_cli/output.py`
- `src/paperang_cli/render.py`
- `src/paperang_cli/models.py`

Responsibilities:

- configuration resolution
- typed project errors
- rendering and feed calculations
- output serialization

### Driver Layer

Files:

- `src/paperang_cli/drivers/base.py`
- `src/paperang_cli/drivers/registry.py`
- `src/paperang_cli/drivers/paperang_p1.py`

Responsibilities:

- per-model behavior
- transport selection per model
- protocol-specific parsing
- future extension point for non-P1 devices

### Protocol Layer

Files:

- `src/paperang_cli/protocol/const.py`
- `src/paperang_cli/protocol/hardware_bleak.py`
- `src/paperang_cli/protocol/image_data.py`

Responsibilities:

- BLE transport and packet framing
- low-level Paperang commands
- image and text conversion into printer data

## Why There Is A Driver Registry Already

Even though only P1 is supported today, a registry avoids turning the CLI into a permanent one-model implementation.

That matters because a future printer may differ in:

- packet framing
- BLE services or characteristics
- feed calibration
- density ranges
- render width
- whether it uses BLE at all

## Current P1 Behavioral Assumptions

The current standalone package intentionally carries over the already-proven behavior from the root working flow:

- connect over BLE with notify enabled
- brief settle delay before CRC handshake
- post-connect initialization sequence
- density `75`
- wrapped paragraph rendering
- calibrated post-print feed derived from the Android-like behavior

## Root Project Relationship

`paperang-cli` currently vendors the necessary protocol code into its own package tree.

This is deliberate for the first implementation stage because it gives the standalone package:

- explicit ownership of its behavior
- cleaner imports
- independence from the root runtime config file

If the repository later needs a shared library layer, the current package layout already points toward that refactor.