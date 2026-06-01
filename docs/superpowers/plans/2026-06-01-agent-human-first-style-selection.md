# Agent Human-First Style Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the skill, contract, and user-facing documentation around a human-first agent policy for choosing existing JSON styling controls and scenarios.

**Architecture:** Keep all behavior in documentation and contract surfaces. Update both public and installable skill copies, keep contract mirrors synchronized, and describe one consistent policy: scenario-first, override-second, whole words by default, persistent defaults only by explicit user request.

**Tech Stack:** Markdown, JSON, existing skill validation script

---

### Task 1: Update the skill policy

**Files:**
- Modify: `.agents/skills/paperang-cli/SKILL.md`
- Modify: `skills/paperang-cli/SKILL.md`

- [ ] Add a section describing the human-first selection policy.
- [ ] State that scenarios are starting points, not a whitelist.
- [ ] State that the agent should prefer temporary `style-json` overrides by default.
- [ ] State that persistent config changes require explicit user direction.
- [ ] State that `break_long_words=true` must not be enabled unless the user explicitly asks.
- [ ] State that user-facing replies should follow the user's language when clear.

### Task 2: Update the canonical contract

**Files:**
- Modify: `docs/agents/cli-contract.md`
- Modify: `docs/agents/cli-contract.json`

- [ ] Add the same policy to the human-readable contract.
- [ ] Add matching machine-readable fields describing scenario usage, temporary-vs-persistent config behavior, whole-word default behavior, and response-language guidance.
- [ ] Keep the wording tied to existing public controls rather than implying a new render mode.

### Task 3: Sync bundled contract mirrors

**Files:**
- Modify: `.agents/skills/paperang-cli/references/cli-contract.md`
- Modify: `.agents/skills/paperang-cli/references/cli-contract.json`
- Modify: `skills/paperang-cli/references/cli-contract.md`
- Modify: `skills/paperang-cli/references/cli-contract.json`

- [ ] Copy the canonical contract updates into both bundled reference locations.
- [ ] Confirm the mirror content stays byte-for-byte aligned with the canonical contract files.

### Task 4: Update user-facing docs

**Files:**
- Modify: `README.md`
- Modify: `docs/usage/commands.md`
- Modify: `docs/usage/configuration.md`
- Modify: `docs/usage/p1-api.md`

- [ ] Explain that built-in scenarios are reusable bases that may be overridden per invocation.
- [ ] Explain that ordinary word wrapping with `break_long_words=false` is the default human-friendly behavior.
- [ ] Explain when `largest-fitting` is the more human-friendly choice.
- [ ] Explain that persistent `print_defaults` are for explicit “make this the default” requests, while one-off tasks should prefer temporary `style-json`.

### Task 5: Validate synchronization

**Files:**
- Modify: none

- [ ] Run `python scripts/check-agent-skill.py`.
- [ ] Inspect the result to confirm the public and installable skill bundles remain synchronized.
- [ ] Stop if the validator reports drift and fix only the documentation or reference files needed to restore sync.