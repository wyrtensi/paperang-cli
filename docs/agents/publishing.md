# Publishing Runbook For Agents

## Scope

This runbook covers repository bootstrap, PyPI Trusted Publishing, routine Python releases, and the planned npm wrapper.

The canonical repository is:

- GitHub: `wyrtensi/paperang-cli`
- PyPI project: `paperang-cli`

Keep the Python package at the repository root. If an npm wrapper is added later, place it under `npm/` in the same repository.

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

- tests on Linux, macOS, and Windows
- Python `3.10`, `3.12`, and `3.14`
- wheel and sdist builds
- `twine check`
- wheel-content verification

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

## Routine PyPI Release

Before every release:

1. Update `version` in `pyproject.toml`.
2. Update `__version__` in `src/paperang_cli/__init__.py`.
3. Run local release checks.
4. Commit and push the version change.
5. Wait for CI to pass.
6. Create a GitHub Release with tag `v<package-version>`.

Example:

```powershell
gh release create v0.1.1 --repo wyrtensi/paperang-cli --target main --title "paperang-cli v0.1.1" --generate-notes
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

## Planned npm Wrapper

Do not create a separate npm bridge repository. Add a small wrapper under `npm/` when PyPI publishing is stable.

The wrapper should:

- use package name `paperang-cli` if the npm name remains available
- expose `paperang` and `paperang-cli` executable shims
- install the matching `paperang-cli==<version>` Python package from PyPI
- keep `package.json.repository.url` exactly aligned with `https://github.com/wyrtensi/paperang-cli.git`
- test the npm package with `npm pack --dry-run`
- publish only after the matching PyPI version exists
- use Node `24` and npm `>=11.5.1`
- publish from a GitHub-hosted runner with `id-token: write`

npm Trusted Publishing is configured in the settings of an existing npm package. Unlike PyPI pending publishers, npm package ownership must be bootstrapped before the trusted publisher can be added.

After the initial npm package exists:

1. Open the package settings on npmjs.com.
2. Add a GitHub Actions Trusted Publisher for `wyrtensi/paperang-cli`.
3. Enter the npm workflow filename only.
4. Select the allowed publish action.
5. Prefer staged publishing when the npm wrapper is implemented.
6. Restrict traditional token publishing after OIDC is verified.

Official reference:

- https://docs.npmjs.com/trusted-publishers/
