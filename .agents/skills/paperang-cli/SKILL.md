---
name: paperang-cli
description: "Use when operating, automating, debugging, reviewing, or extending paperang-cli for Paperang P1 or P2 printers: BLE or USB discovery/readiness, JSON output, configuration, dry-run validation, paper-use approval, image or compose printing, self-test caution, CLI contracts, rendering, drivers, protocol changes, tests, or release automation."
license: MIT
---

# paperang-cli

Use `paperang-cli` as a safety-first command-line interface for Paperang thermal printers. Prefer `paperang`; use `paperang-cli` only when the shorter executable conflicts on the host.

This skill is portable across agent clients and operating systems. Real BLE communication and physical printing have been tested only on Windows. Treat Linux and macOS support as compatibility-tested, not hardware-validated.

## Read The Contract

Read the bundled references before driving hardware or changing public CLI behavior:

- [Human-readable CLI contract](references/cli-contract.md)
- [Machine-readable CLI contract](references/cli-contract.json)

If working inside the `wyrtensi/paperang-cli` repository, the canonical editable contract lives under `docs/agents/`. Update the bundled reference copies whenever the canonical files change.

## Safety Rules

Treat these rules as hard requirements:

1. Prefer `--json` for agent-driven commands.
2. For an ordinary one-off print request, use the fast path: run the matching `print ... --dry-run`, then run the matching real print. The real print command performs its own required transport initialization.
3. Use `config show`, `discover`, `probe`, `status`, `battery`, and `mac` for first contact with an unknown device, explicit diagnostics, or recovery after a failed real print. Do not run live BLE readiness commands in parallel.
4. Run a successful matching `print ... --dry-run` before every real print.
5. Keep content, image, layout, mode, conversion, font size, min-font-size, font-fit mode, font family, orientation, autofit intent, and feed options unchanged between dry-run and real print.
6. Treat an imperative user request such as "print this" as approval for exactly one matching non-self-test real print after a successful dry-run. Report the dry-run result, but do not ask the same question again.
7. Ask for explicit approval before consuming paper when the request is exploratory or ambiguous, when parameters change after the dry-run, or before copies, retries, and repeated prints.
8. Add `--allow-paper-use` only after approval from the current request or a follow-up for `print text`, `print paragraph`, `print image`, or `print compose`.
9. Add `--allow-large-paper-use` only after specific follow-up approval for `print self-test`.
10. If the CLI returns `SAFETY_ERROR`, stop. Never automatically append an allow flag or retry.

`print image` and `print compose` are experimental physical-output paths. A successful dry-run validates rendering and packaging, not printer readiness or final paper quality.

## Approval Interpretation

- "Print this text", "print this image", and "print this label" authorize one matching real print after a successful dry-run.
- "Can this be printed?", "preview this", and "show me how this would look" do not authorize paper use.
- A first print does not authorize another copy, a retry, or a print with changed parameters.
- Always ask again before `print self-test` because it consumes substantially more paper.

## Supported Hardware

The current release supports `paperang_p1` over BLE and `paperang_p2` over USB or BLE.

`paperang_p2` support is implemented in software via `paperang-p2-lib`, but physical USB and BLE validation for P2 has not been completed in this repository yet.

- Do not invent or document local or cable fallbacks beyond the supported model transports.
- For `paperang_p1`, do not invent a USB or local fallback.
- Do not assume other undocumented models are available because extension points exist.
- Ask for manual physical validation before repeated image or compose printing.

## Fast Print Path

For an ordinary one-off print request, avoid separate live readiness queries. The real print command performs discovery, connection, and required transport initialization itself:

```powershell
paperang --json print text "Hello from Paperang" --dry-run
paperang --json print text "Hello from Paperang" --allow-paper-use
```

Keep the dry-run and real print parameters identical. If the real print fails, stop and report the error before using diagnostic commands or retrying.

## Diagnostic Readiness Sequence

Use this sequence for first contact with an unknown device, explicit diagnostics, or recovery after a failed real print. Run live BLE readiness commands sequentially, never in parallel:

```powershell
paperang --json config show
paperang --json discover
paperang --json probe
paperang --json battery
```

Stop and report failures before printing or retrying.

For an ordinary text print:

```powershell
paperang --json print text "Hello from Paperang" --dry-run
```

For a rotated label-style text preview:

```powershell
paperang --json print text "Long shipping label" --dry-run --orientation rotate-90-cw --font-family mono --autofit
```

For a rotated image preview:

```powershell
paperang --json print image ".\sample.png" --dry-run --orientation rotate-90-cw
```

After a successful matching dry-run, when the user already asked to print:

```powershell
paperang --json print text "Hello from Paperang" --allow-paper-use
```

Rotated compose printing is not implemented yet in the current release. Keep `print compose` in the ordinary vertical layout path.

## Scenario Playbook

This skill bundle ships ready `--style-json` payloads under `examples/` next to `SKILL.md`. Treat them as starting points, not a whitelist: reuse one when it fits, use a close match as a base plus temporary overrides when that is enough, or build a fresh payload when none of the examples fit the request.

- `examples/address-label.json`: long address, shipping label, or other rotated paragraph printed along the paper path.
- `examples/fridge-note.json`: grocery list, meal plan, reminder, or other broad home note in ordinary orientation.
- `examples/chore-list.json`: cleaning checklist, routine, packing list, or repeated household task list.
- `examples/pantry-label.json`: jar, spice, tea, cereal, or pantry shelf label for ordinary home storage.
- `examples/cable-tag.json`: charger, cable, adapter, or power-brick tag for desks and drawers.
- `examples/storage-bin.json`: closet box, drawer, shelf, or tool bin label with a longer budget.
- `examples/receipt-note.json`: short receipt, checklist, or memo with a conservative paragraph budget.
- `examples/logo-strip.json`: long logo, banner, or sticker art that should run along the paper path.
- `examples/product-style.json`: ordinary `print compose` layout with text and image, using report-only length handling.

Typical previews:

```powershell
paperang --json print paragraph "221B Baker Street London" --dry-run --style-json .\examples\address-label.json
paperang --json print paragraph "Buy milk\nFruit\nBread" --dry-run --style-json .\examples\fridge-note.json
paperang --json print paragraph "Kitchen\nBathroom\nLaundry" --dry-run --style-json .\examples\chore-list.json
paperang --json print paragraph "PASTA" --dry-run --style-json .\examples\pantry-label.json
paperang --json print paragraph "USB-C CHARGER" --dry-run --style-json .\examples\cable-tag.json
paperang --json print paragraph "WINTER SCARVES" --dry-run --style-json .\examples\storage-bin.json
paperang --json print paragraph "Milk\nEggs\nTea" --dry-run --style-json .\examples\receipt-note.json
paperang --json print image ".\banner.png" --dry-run --style-json .\examples\logo-strip.json
paperang --json print compose "Product title" ".\badge.png" --dry-run --style-json .\examples\product-style.json
```

When a scenario sets `max_length_mm`, inspect `estimated_length_mm` and `fits_length_limit` in the dry-run result before approving paper use. If the dry-run exceeds the budget, adjust the content or styling and run a new dry-run instead of printing.

For rotated `rotate-90-cw` and `rotate-90-ccw` text and image jobs, those length fields use the head-width calibration value `printable_width_mm` when it is available. Ordinary orientation jobs and ordinary compose continue to use `advance_mm_per_px`.

Keep the same `--style-json` payload between dry-run and real print. CLI flags may override a specific field, but the safest path is to keep the payload identical across both commands.

## Human-First Style Selection

When a user asks for help choosing styling, reason from how the result should look and read on paper, not from machine-centric phrasing.

- labels and tags usually prioritize quick recognition, larger text, and low visual clutter
- notes and lists usually prioritize ordinary whole-word reading and predictable wrapping
- compose requests usually prioritize what should read first at a glance: the text, the image, or the balance between them

Default agent behavior for style selection:

1. Determine the human-visible task type.
2. Prefer the nearest built-in scenario or shipped example as a base.
3. If the base is close but not exact, add a temporary per-invocation `--style-json` override.
4. If no scenario fits, build a temporary `style-json` from the existing public controls.

Use temporary task-scoped styling by default. Only update persistent `print_defaults` when the user explicitly asks to make that behavior the default for future jobs.

Keep `break_long_words` at `false` unless the user explicitly asks for character-level splitting. If a long token must fit and the user did not request splitting, prefer preserving whole words and using `font_fit="largest-fitting"` when that better matches the user's intent.

When explaining the choice, describe it in human terms such as readability, glanceability, and expected strip length. Use dry-run fields like `estimated_length_mm`, `max_length_mm`, and `fits_length_limit` when they are available.

Respond to the user in the language they are using when it is clear. If the request language is ambiguous, follow the higher-priority environment instructions.

## Editing The Repository

When changing public behavior, keep implementation, tests, docs, and both contract copies synchronized.

| Change | Review together |
| --- | --- |
| Commands, flags, JSON, exit codes | `src/paperang_cli/cli.py`, `src/paperang_cli/commands/`, `tests/test_cli.py`, `docs/usage/commands.md`, both contract pairs |
| Config schema or defaults | `src/paperang_cli/config.py`, `paperang-cli.config.example.json`, `tests/test_config.py`, `docs/usage/configuration.md` |
| Rendering, image modes, compose | `src/paperang_cli/render.py`, `src/paperang_cli/commands/print_cmd.py`, `tests/test_render.py`, `tests/test_cli.py`, contracts |
| Models, drivers, BLE protocol | `src/paperang_cli/drivers/`, `src/paperang_cli/protocol/`, `tests/test_registry.py`, development docs, contracts |
| Publishing | `.github/workflows/`, `npm/`, `docs/agents/publishing.md` |

Never weaken a printing safety gate while refactoring.

## Verification

From the repository root, run:

```powershell
python -m pytest -q tests
python scripts/check-agent-skill.py
Set-Location npm
npm test
npm pack --dry-run
```

Use narrower tests while iterating, then run the complete suite before committing.
