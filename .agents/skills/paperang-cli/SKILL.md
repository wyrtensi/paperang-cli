---
name: paperang-cli
description: "Use when operating, automating, debugging, reviewing, or extending paperang-cli for Paperang P1 printers: BLE discovery, readiness queries, JSON output, configuration, dry-run validation, paper-use approval, image or compose printing, self-test caution, CLI contracts, rendering, drivers, protocol changes, tests, or release automation."
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
2. Use non-printing commands first: `config show`, `discover`, `probe`, `status`, `battery`, and `mac`.
3. Run a successful matching `print ... --dry-run` before every real print.
4. Keep content, image, layout, mode, conversion, font size, font family, orientation, autofit intent, and feed options unchanged between dry-run and real print.
5. Treat an imperative user request such as "print this" as approval for exactly one matching non-self-test real print after a successful dry-run. Report the dry-run result, but do not ask the same question again.
6. Ask for explicit approval before consuming paper when the request is exploratory or ambiguous, when parameters change after the dry-run, or before copies, retries, and repeated prints.
7. Add `--allow-paper-use` only after approval from the current request or a follow-up for `print text`, `print paragraph`, `print image`, or `print compose`.
8. Add `--allow-large-paper-use` only after specific follow-up approval for `print self-test`.
9. If the CLI returns `SAFETY_ERROR`, stop. Never automatically append an allow flag or retry.

`print image` and `print compose` are experimental physical-output paths. A successful dry-run validates rendering and packaging, not printer readiness or final paper quality.

## Approval Interpretation

- "Print this text", "print this image", and "print this label" authorize one matching real print after a successful dry-run.
- "Can this be printed?", "preview this", and "show me how this would look" do not authorize paper use.
- A first print does not authorize another copy, a retry, or a print with changed parameters.
- Always ask again before `print self-test` because it consumes substantially more paper.

## Supported Hardware

The current release supports `paperang_p1` over BLE only.

The API catalog may also list planned placeholders such as `p2`, but those are not available in this package version.

- Do not invent or document local, cable, or USB transport fallbacks.
- Do not assume other models are available because extension points exist.
- Ask for manual physical validation before repeated image or compose printing.

## Safe Readiness Sequence

```powershell
paperang --json config show
paperang --json discover
paperang --json probe
paperang --json battery
```

Stop and report failures before printing.

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
