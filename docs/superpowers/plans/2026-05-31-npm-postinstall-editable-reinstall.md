# npm Postinstall Editable Reinstall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the npm wrapper replace an existing same-version editable Python installation with the matching PyPI wheel without reinstalling heavy dependencies.

**Architecture:** Add a focused npm helper that builds and runs the two pip commands used by `postinstall`: dependency-aware upgrade first, top-level force reinstall second. Keep `postinstall.js` responsible for Python selection and the existing `--user` retry. Add unit coverage for command construction and a release-validation Python script for the published-wheel integration path.

**Tech Stack:** Node.js CommonJS, Node built-in test runner, Python virtual environments, pip, repository version sync script.

---

### Task 1: Add Pip Install Command Coverage

**Files:**
- Create: `npm/lib/python-installer.js`
- Modify: `npm/scripts/postinstall.js`
- Modify: `npm/test/python-launcher.test.js`

- [ ] **Step 1: Write the failing unit test**

Import `buildPipInstallArgs` from `../lib/python-installer` and assert that it returns:

```js
[
  ["-m", "pip", "install", "--upgrade", "--user", "paperang-cli==0.1.5"],
  [
    "-m",
    "pip",
    "install",
    "--force-reinstall",
    "--no-deps",
    "--user",
    "paperang-cli==0.1.5"
  ]
]
```

- [ ] **Step 2: Run the npm unit tests and verify RED**

Run: `Set-Location npm; npm test; Set-Location ..`

Expected: FAIL because `../lib/python-installer` does not exist.

- [ ] **Step 3: Add the minimal installer helper**

Create `npm/lib/python-installer.js` with:

```js
"use strict";

const { spawnSync } = require("node:child_process");

function buildPipInstallArgs(packageSpec, extraArgs = []) {
  return [
    ["-m", "pip", "install", "--upgrade", ...extraArgs, packageSpec],
    [
      "-m",
      "pip",
      "install",
      "--force-reinstall",
      "--no-deps",
      ...extraArgs,
      packageSpec
    ]
  ];
}

function runPipInstall(candidate, packageSpec, extraArgs = []) {
  let result = { status: 0 };

  for (const args of buildPipInstallArgs(packageSpec, extraArgs)) {
    result = spawnSync(candidate.command, [...candidate.args, ...args], {
      stdio: "inherit",
      windowsHide: true
    });

    if (result.status !== 0) {
      return result;
    }
  }

  return result;
}

module.exports = {
  buildPipInstallArgs,
  runPipInstall
};
```

Replace the local `runPip` function in `npm/scripts/postinstall.js` with
`runPipInstall(candidate, packageSpec)` and
`runPipInstall(candidate, packageSpec, ["--user"])`.

- [ ] **Step 4: Run the npm unit tests and verify GREEN**

Run: `Set-Location npm; npm test; Set-Location ..`

Expected: PASS.

### Task 2: Add Published-Wheel Release Validation

**Files:**
- Create: `scripts/check-npm-editable-reinstall.py`
- Modify: `docs/agents/publishing.md`

- [ ] **Step 1: Add the release-validation script**

Create a Python script that:

1. Reads the current version from `src/paperang_cli/version-manifest.json`.
2. Creates a temporary virtual environment.
3. Installs the repository in editable mode with `--no-deps`.
4. Runs the same dependency-aware upgrade and top-level force reinstall commands.
5. Asserts that `pip freeze` does not contain an editable `paperang-cli`.
6. Imports `paperang_cli` and asserts that its path is inside the temporary virtual environment.
7. Runs `pip check`.

Add `--package-version` so the script can verify an already-published version
such as `0.1.5` before `0.1.6` exists.

- [ ] **Step 2: Document release validation**

Add this post-PyPI, pre-npm check to `docs/agents/publishing.md`:

```powershell
python scripts/check-npm-editable-reinstall.py
```

Explain that the command verifies replacement of a same-version editable
installation with the published wheel.

- [ ] **Step 3: Verify the release-validation script against the current published wheel**

Run: `python scripts/check-npm-editable-reinstall.py --package-version 0.1.5`

Expected: PASS with an import path inside the temporary virtual environment.

### Task 3: Update Documentation And Release Metadata

**Files:**
- Modify: `SECURITY.md`
- Modify: `npm/README.md`
- Modify: `docs/agents/publishing.md`
- Modify: `src/paperang_cli/version-manifest.json`
- Regenerate: `docs/agents/cli-contract.json`
- Regenerate: `.agents/skills/paperang-cli/references/cli-contract.json`
- Regenerate: `skills/paperang-cli/references/cli-contract.json`
- Regenerate: `npm/package.json`
- Regenerate: `npm/package-lock.json`

- [ ] **Step 1: Document the two-command postinstall flow**

Update the npm wrapper documentation to state that postinstall:

1. Runs `pip install --upgrade paperang-cli==<matching-version>`.
2. Runs `pip install --force-reinstall --no-deps paperang-cli==<matching-version>`.
3. Retries the complete sequence with `--user` if the first scope fails.

Explain that the second command replaces same-version editable installs without
reinstalling heavy dependencies.

- [ ] **Step 2: Bump the source-of-truth version**

Change `src/paperang_cli/version-manifest.json` to:

```json
{
  "version": "0.1.6"
}
```

- [ ] **Step 3: Synchronize generated metadata**

Run: `python scripts/sync-version-manifest.py`

Expected: `Synchronized paperang-cli metadata from version manifest: 0.1.6`

### Task 4: Verify, Commit, And Push

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run Python tests**

Run: `python -m pytest -q tests`

Expected: PASS.

- [ ] **Step 2: Validate the Agent Skill mirrors**

Run: `python scripts/check-agent-skill.py`

Expected: PASS.

- [ ] **Step 3: Validate the npm wrapper**

Run:

```powershell
Set-Location npm
npm test
npm pack --dry-run
Set-Location ..
```

Expected: PASS.

- [ ] **Step 4: Validate package metadata**

Run:

```powershell
python -m build
python -m twine check dist/*
```

Expected: PASS.

- [ ] **Step 5: Check the diff**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only intentional files are modified.

- [ ] **Step 6: Commit as wyrtensi**

Run:

```powershell
git add .
git commit -m "fix: reinstall python package from npm wrapper"
```

- [ ] **Step 7: Push main without publishing**

Run: `git push origin main`

Expected: `main` is pushed. Do not create a GitHub Release or tag.
