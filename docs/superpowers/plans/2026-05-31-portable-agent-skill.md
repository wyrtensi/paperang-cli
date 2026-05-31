# Portable Agent Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-contained cross-platform `paperang-cli` Agent Skill and a portable installer.

**Architecture:** Store a repository-local skill under `.agents/skills/paperang-cli` and a checked byte-identical public distribution mirror under `skills/paperang-cli`. Install personal copies with GitHub CLI or a Python fallback that copies local files or downloads a fixed remote allowlist.

**Tech Stack:** Markdown, YAML, JSON, Python standard library, pytest, GitHub Actions

---

### Task 1: Installer tests

**Files:**
- Create: `tests/test_install_agent_skill.py`
- Create: `scripts/install-agent-skill.py`

- [x] Write tests for target directory selection, local copy, overwrite refusal, and forced replacement.
- [x] Run `python -m pytest -q tests/test_install_agent_skill.py` and confirm failure before implementation.
- [x] Implement the portable installer with local and GitHub sources.
- [x] Run `python -m pytest -q tests/test_install_agent_skill.py`.

### Task 2: Canonical skill

**Files:**
- Create: `.agents/skills/paperang-cli/SKILL.md`
- Create: `.agents/skills/paperang-cli/agents/openai.yaml`
- Create: `.agents/skills/paperang-cli/references/cli-contract.md`
- Create: `.agents/skills/paperang-cli/references/cli-contract.json`

- [x] Initialize the skill layout with the skill creator.
- [x] Adapt the legacy workspace skill into a portable repository-independent skill.
- [x] Add synchronized bundled contract references.
- [x] Validate the skill frontmatter.

### Task 3: Documentation and CI

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `.github/workflows/ci.yml`

- [x] Document repository discovery and personal installation.
- [x] Add a ready-to-paste request for another agent.
- [x] Add CI checks for installer tests, skill validity, and synchronized references.
- [x] Run the complete local verification suite.

### Task 4: Publish

- [ ] Commit from the configured `wyrtensi` identity.
- [ ] Push `main`.
- [ ] Wait for GitHub CI.
