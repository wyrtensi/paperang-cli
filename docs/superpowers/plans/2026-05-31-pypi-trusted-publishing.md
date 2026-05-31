# PyPI Trusted Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare `paperang-cli` for a safe first GitHub push and PyPI Trusted Publishing release.

**Architecture:** Keep the Python package as the root of its own GitHub repository. Use a user-writable default config directory, CI for tests and distributions, and a release-triggered OIDC publishing workflow. Document manual PyPI setup separately from automatable GitHub operations.

**Tech Stack:** Python, setuptools, pytest, GitHub Actions, PyPI Trusted Publishing, GitHub CLI.

---

### Task 1: Expand Ignore Rules

**Files:**
- Modify: `.gitignore`

- [x] Add Python, test, editor, OS, local-config, release-artifact, and future npm-wrapper ignore rules.
- [x] Initialize git and verify generated files remain ignored.

### Task 2: Move Default Config To A User Directory

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/paperang_cli/config.py`
- Modify: `README.md`
- Modify: `docs/usage/configuration.md`
- Modify: `docs/agents/cli-contract.md`
- Modify: `docs/agents/cli-contract.json`
- Modify: `AGENTS.md`

- [x] Add failing tests for Windows APPDATA and XDG default paths.
- [x] Run the focused tests and confirm the expected failure.
- [x] Implement the user config directory.
- [x] Run the focused tests and full suite.
- [x] Synchronize the public docs and contract.

### Task 3: Add Release Metadata And CI

**Files:**
- Modify: `pyproject.toml`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/pypi-publish.yml`

- [x] Add author, GitHub URLs, classifiers, and build validation dependencies.
- [x] Add cross-platform tests and distribution checks.
- [x] Add SHA-pinned PyPI Trusted Publishing workflow.
- [x] Validate YAML structure and package builds locally.

### Task 4: Add Agent Publishing Runbook

**Files:**
- Create: `docs/agents/publishing.md`
- Modify: `docs/index.md`
- Modify: `AGENTS.md`
- Modify: `README.md`

- [x] Document bootstrap, first push, GitHub environment setup, PyPI pending publisher setup, manual first release, routine releases, troubleshooting, and future npm direction.
- [x] Link the runbook from agent and user entry points.

### Task 5: Bootstrap GitHub Repository

**Files:**
- Verify: all tracked files

- [x] Initialize git with branch `main`.
- [x] Confirm ignored files are not staged.
- [x] Configure local commit identity as `wyrtensi`.
- [x] Create the initial commit.
- [x] Push to `git@github.com:wyrtensi/paperang-cli.git`.
- [x] Create the GitHub environment `pypi`.

### Task 6: Hand Off Manual Registry Step

**Files:**
- Verify: `docs/agents/publishing.md`

- [ ] Report the exact PyPI pending publisher values.
- [ ] Wait for the user to complete the PyPI UI step before dispatching the first publish workflow.
