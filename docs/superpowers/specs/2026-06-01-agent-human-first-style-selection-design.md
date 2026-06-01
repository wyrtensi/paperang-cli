# Agent Human-First Style Selection Design

## Goal

Document a human-first policy for agent-driven style selection in `paperang-cli` without changing Python implementation files.

The agent should understand existing JSON controls such as `font_fit`, `max_length_mm`, `min_font_size`, and `break_long_words`, choose between built-in scenarios and temporary per-invocation overrides, explain the choice in human terms, and keep permanent defaults unchanged unless the user explicitly asks for them.

## Non-Goals

- Do not change `.py` files.
- Do not introduce a new public render mode.
- Do not change calibration fields such as `printable_width_mm` or `advance_mm_per_px`.
- Do not silently enable character-chunk splitting for long words.

## Existing Inputs The Agent May Use

The policy operates only on already-supported public surfaces:

- built-in scenarios from `src/paperang_cli/presets.py`
- ready `style-json` examples under `skills/paperang-cli/examples/` and `.agents/skills/paperang-cli/examples/`
- per-invocation JSON overrides via `--style-json`
- persistent config defaults under `print_defaults`
- dry-run metadata such as `estimated_length_mm`, `max_length_mm`, and `fits_length_limit`

## Design Principles

### Human-first decision making

The agent should choose styling based on how a person is likely to read or use the print, not on machine-centric wording.

Examples:

- labels and tags prioritize quick recognition, large text, and low visual clutter
- notes and lists prioritize readable word boundaries and natural wrapping
- compose layouts prioritize overall readability and whether text or image should visually lead

### Scenario-first, override-second

The agent should first look for the closest existing scenario and reuse it as a base when it fits.

If the scenario is close but not exact, the agent should add a temporary per-invocation `style-json` override rather than inventing a new permanent preset.

If no scenario fits, the agent should build a temporary `style-json` payload from the public fields already supported by the CLI.

### Temporary by default, persistent only on request

The default workflow is temporary task-scoped styling.

The agent should not update persistent `print_defaults` unless the user explicitly asks for behavior like “make this the default for all future prints”.

### Whole words by default

The agent should not enable `break_long_words=true` unless the user explicitly asks for character-level splitting or chooses a style that clearly requires it.

When a long token must fit and the user did not request splitting, the preferred order is:

1. preserve whole words with `break_long_words=false`
2. use `font_fit="largest-fitting"` when appropriate
3. explain the expected paper result in human terms

## Agent Selection Policy

### Step 1: classify the task

The agent should classify the request into a human-visible use case such as:

- label or tag
- note or memo
- list or checklist
- long rotated label
- compose badge or product card
- image strip

### Step 2: choose a base

The agent should prefer a nearby built-in scenario or shipped example when one matches the intent.

Scenarios are starting points, not a whitelist and not a hidden alternate render engine.

### Step 3: decide between ordinary wrapping and largest-fitting

Recommended defaults:

- for labels and tags: bias toward `font_fit="largest-fitting"` when the user wants the biggest readable text that still fits
- for notes and lists: bias toward ordinary word wrapping with `break_long_words=false`
- for borderline cases: prefer preserving whole words before character-level splitting

### Step 4: explain expected paper output

The agent should explain choices in human terms, for example:

- “I kept whole-word wrapping so the note reads naturally.”
- “I used the label scenario and asked for the largest fitting text so it stays bold at a glance.”
- “This should come out as a strip around 8 to 9 cm long.”

The agent may use dry-run length metadata to support that explanation.

### Step 5: respond in the user's language

The agent should answer in the language used by the user when it is clear.

If the request language is ambiguous, the agent should follow the higher-priority environment instructions.

Internal skill wording and bundled examples may remain in English.

## Documentation Changes Required

Update these surfaces so they describe the same policy:

- `.agents/skills/paperang-cli/SKILL.md`
- `skills/paperang-cli/SKILL.md`
- `docs/agents/cli-contract.md`
- `docs/agents/cli-contract.json`
- `.agents/skills/paperang-cli/references/cli-contract.md`
- `.agents/skills/paperang-cli/references/cli-contract.json`
- `skills/paperang-cli/references/cli-contract.md`
- `skills/paperang-cli/references/cli-contract.json`
- `README.md`
- `docs/usage/commands.md`
- `docs/usage/configuration.md`
- `docs/usage/p1-api.md`

## Validation

The documentation-only update should be validated with:

- `python scripts/check-agent-skill.py`
- targeted checks that mirrored contract and skill reference copies remain synchronized

## Acceptance Criteria

- The skill explicitly says scenarios are starting points, not a whitelist.
- The skill explicitly says the agent should reason from human readability and expected paper appearance.
- The skill explicitly says `break_long_words=true` requires an explicit user request.
- The skill explicitly says temporary `style-json` is the default and persistent config changes require explicit user approval.
- The skill explicitly says the response language should follow the user when clear.
- The agent contract mirrors the same policy in both Markdown and JSON.
- README and usage docs explain scenario-vs-override behavior and the “whole words by default” rule.
- No `.py` files are modified.