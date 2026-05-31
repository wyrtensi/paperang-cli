# Publishing Runbook For Agents

## Scope

This runbook covers repository bootstrap, PyPI Trusted Publishing, routine Python releases, and the npm wrapper.

The canonical repository is:

- GitHub: `wyrtensi/paperang-cli`
- PyPI project: `paperang-cli`

Keep the Python package at the repository root and the npm wrapper under `npm/` in the same repository.

## Safety Boundary

Agents may automate:

- local tests and package builds
- git initialization, commits, and pushes when explicitly requested
- GitHub repository inspection through `gh`
- GitHub environment creation through `gh`
- GitHub Actions workflow dispatch after registry trust is configured
- GitHub Release creation after explicit user approval

Agents must ask the user to complete registry UI steps that require interactive account access:

- PyPI pending publisher creation
- npm package ownership bootstrap
- npm trusted publisher configuration
- registry 2FA and token-access restrictions

Do not create or store long-lived PyPI or npm publish tokens when Trusted Publishing is available.

## Local Release Checks

From the repository root:

```powershell
python -m pip install -e ".[dev,release]"
python -m pytest -q tests
python -m build
python -m twine check dist/*
```

Verify that the wheel contains the package and MIT license:

```powershell
python -c "from pathlib import Path; from zipfile import ZipFile; wheel=next(Path('dist').glob('*.whl')); names=ZipFile(wheel).namelist(); assert 'paperang_cli/cli.py' in names; assert any(name.endswith('.dist-info/licenses/LICENSE') for name in names)"
```

Remove local `build/` and `dist/` output after inspection unless the user wants to keep the artifacts.

## Repository Bootstrap

The GitHub repository already exists and is intended to receive this standalone package:

```powershell
gh repo view wyrtensi/paperang-cli
```

Initialize and inspect the local repository:

```powershell
git init -b main
git status --short --ignored
git check-ignore -v .pytest_cache src/paperang_cli.egg-info src/paperang_cli/__pycache__ tests/__pycache__ paperang-cli.config.json
```

Configure the local commit identity:

```powershell
git config user.name wyrtensi
git config user.email "<GitHub noreply email for wyrtensi>"
```

Create and push the initial commit only after tests and package validation pass:

```powershell
git add .
git status --short
git commit -m "feat: publish standalone paperang cli"
git remote add origin git@github.com:wyrtensi/paperang-cli.git
git push -u origin main
```

## GitHub Automation

### CI

`.github/workflows/ci.yml` runs:

- compatibility tests on Linux, macOS, and Windows
- Python `3.10`, `3.12`, and `3.14`
- wheel and sdist builds
- `twine check`
- wheel-content verification
- Agent Skill validation, mirror synchronization checks, and fallback-installer tests

Real BLE communication and physical printing have been tested only on Windows. CI on Linux and macOS does not change that hardware-support statement.

### Agent Skill

The public distributable Agent Skill lives at `skills/paperang-cli/`. A byte-identical copy lives at `.agents/skills/paperang-cli/` so compatible agents can discover it automatically while working inside the repository.

Validate both copies and the fallback installer before pushing:

```powershell
python scripts/check-agent-skill.py
python -m pytest -q tests/test_install_agent_skill.py tests/test_check_agent_skill.py
gh skill publish skills --dry-run
```

Preview and install the public copy through GitHub CLI `2.90.0` or newer:

```powershell
gh skill preview wyrtensi/paperang-cli paperang-cli
gh skill install wyrtensi/paperang-cli paperang-cli --agent cursor --scope user
gh skill install wyrtensi/paperang-cli paperang-cli --agent antigravity --scope user
gh skill update paperang-cli --dry-run
```

Do not create a separate Agent Skill release from this repository. Application release tags snapshot the matching skill automatically, so Python, npm, and Agent Skill versions remain aligned.

Recommended manual hardening after the release flow is proven: add an active repository ruleset that prevents updates and deletion of release tags such as `v*` and `npm-v*` without blocking tag creation. `gh skill publish skills --dry-run` reports a warning until tag protection exists.

### PyPI Publish

`.github/workflows/pypi-publish.yml` runs on:

- a published GitHub Release
- manual `workflow_dispatch`

The workflow:

1. builds wheel and sdist
2. verifies package metadata
3. confirms that a GitHub Release tag matches `v<package-version>`
4. runs `twine check`
5. uploads distributions as a GitHub Actions artifact
6. publishes through PyPI OIDC from the `pypi` GitHub environment

Only the publish job receives `id-token: write`.

## Create The GitHub Environment

Create the environment after the repository has its first pushed commit:

```powershell
gh api --method PUT repos/wyrtensi/paperang-cli/environments/pypi
```

Recommended manual hardening in GitHub:

1. Open `https://github.com/wyrtensi/paperang-cli/settings/environments`.
2. Open the `pypi` environment.
3. Add a required reviewer for releases.
4. Keep environment secrets empty. PyPI publishing uses OIDC.

## Configure The PyPI Pending Publisher

PyPI supports creating a new project through a pending Trusted Publisher. A manual upload is not required.

Open:

```text
https://pypi.org/manage/account/publishing/
```

Add a pending GitHub publisher with:

| Field | Value |
| --- | --- |
| PyPI project name | `paperang-cli` |
| GitHub owner | `wyrtensi` |
| GitHub repository | `paperang-cli` |
| Workflow filename | `pypi-publish.yml` |
| Environment name | `pypi` |

Values are case-sensitive. Enter the workflow filename only, not `.github/workflows/pypi-publish.yml`.

Official references:

- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- https://docs.pypi.org/trusted-publishers/using-a-publisher/

## First PyPI Publish

After the pending publisher exists, dispatch the workflow manually:

```powershell
gh workflow run pypi-publish.yml --repo wyrtensi/paperang-cli --ref main
gh run list --repo wyrtensi/paperang-cli --workflow pypi-publish.yml --limit 5
```

Inspect the selected run:

```powershell
gh run view <run-id> --repo wyrtensi/paperang-cli
gh run view <run-id> --repo wyrtensi/paperang-cli --log-failed
```

Confirm the published package:

```powershell
python -m pip index versions paperang-cli
```

## Changing The Version

Use one source of truth for release version changes:

1. Edit `src/paperang_cli/version-manifest.json`.
2. Run `python scripts/sync-version-manifest.py`.
3. Run at least `python scripts/check-agent-skill.py`.
4. Run the normal release validation flow before tagging or publishing.

What the sync script updates for you:

- `docs/agents/cli-contract.json`
- `.agents/skills/paperang-cli/references/cli-contract.json`
- `skills/paperang-cli/references/cli-contract.json`
- `npm/package.json`
- `npm/package-lock.json`

Most human-facing docs intentionally say `current release` instead of repeating a literal version number. That means a routine version bump normally does not require manual edits across README pages or usage guides.

## Routine PyPI Release

Before every release:

1. Update `src/paperang_cli/version-manifest.json`.
2. Run `python scripts/sync-version-manifest.py`.
3. Run local release checks.
4. Commit and push the synchronized version change.
5. Wait for CI to pass.
6. Create a GitHub Release with tag `v<package-version>`.

Example:

```powershell
$version = (Get-Content src/paperang_cli/version-manifest.json | ConvertFrom-Json).version
gh release create "v$version" --repo wyrtensi/paperang-cli --target main --title "paperang-cli v$version" --generate-notes
```

Publishing the GitHub Release triggers PyPI publishing automatically.

## PyPI OIDC Troubleshooting

If publishing fails:

1. Confirm the workflow file exists at `.github/workflows/pypi-publish.yml`.
2. Confirm the GitHub environment is named exactly `pypi`.
3. Confirm the pending or active PyPI publisher uses owner `wyrtensi`, repository `paperang-cli`, workflow `pypi-publish.yml`, and environment `pypi`.
4. Confirm the publish job has `id-token: write`.
5. Confirm the workflow runs on a GitHub-hosted runner.
6. Confirm that the version has not already been uploaded to PyPI.
7. Inspect failed logs with `gh run view <run-id> --log-failed`.

## npm Wrapper

Do not create a separate npm bridge repository. The small wrapper lives under `npm/` in this repository.

The wrapper:

- uses package name `paperang-cli`
- exposes `paperang` and `paperang-cli` executable shims
- installs the matching `paperang-cli==<version>` Python package from PyPI
- keeps `package.json.repository.url` exactly aligned with `https://github.com/wyrtensi/paperang-cli.git`
- tests the npm package with `npm test` and `npm pack --dry-run`
- publishes only after the matching PyPI version exists
- uses Node `24` and npm `>=11.5.1`
- publishes from a GitHub-hosted runner with `id-token: write`

npm Trusted Publishing is configured in the settings of an existing npm package. Unlike PyPI pending publishers, npm package ownership must be bootstrapped before the trusted publisher can be added.

Validate the wrapper locally:

```powershell
Set-Location npm
npm ci --ignore-scripts
npm test
npm pack --dry-run
Set-Location ..
```

## First npm Publish

The first npm publish is a one-time interactive bootstrap because the package settings do not exist before the package exists:

```powershell
npm login
npm whoami
Set-Location npm
npm publish --access public
Set-Location ..
```

Do not add an npm token to GitHub Actions.

Create the GitHub environment used by the automated workflow:

```powershell
gh api --method PUT repos/wyrtensi/paperang-cli/environments/npm
```

After the initial npm package exists:

1. Open the package settings on npmjs.com.
2. Add a GitHub Actions Trusted Publisher.
3. Use owner `wyrtensi`, repository `paperang-cli`, workflow filename `npm-publish.yml`, and environment `npm`.
4. Allow `npm publish`.
5. Verify OIDC publishing on the next release.
6. Restrict traditional token publishing after OIDC is verified.

For maximum protection after the basic flow is proven, switch the trusted publisher to stage-only permission and update the workflow from `npm publish` to `npm stage publish`. Staged releases require interactive review before they become public.

## Routine npm Release

`.github/workflows/npm-publish.yml` automatically runs after a successful PyPI publish. It can also be dispatched manually or triggered with a matching `npm-v<version>` tag.

Before a release:

1. Keep `src/paperang_cli/version-manifest.json` as the single source of truth.
2. Run `python scripts/sync-version-manifest.py` before committing a release bump.
3. Publish the Python package first.
4. Let the npm workflow verify PyPI availability, run wrapper tests, inspect the tarball, and publish through OIDC.

The workflow is idempotent: it skips `npm publish` when the matching npm version already exists.

Official reference:

- https://docs.npmjs.com/trusted-publishers/
