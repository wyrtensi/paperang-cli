# PyPI Trusted Publishing Design

## Goal

Prepare `paperang-cli` as a standalone public GitHub repository and publish its Python package to PyPI through GitHub Actions Trusted Publishing before adding an npm wrapper.

## Repository Strategy

Use one repository:

- GitHub: `wyrtensi/paperang-cli`
- PyPI: `paperang-cli`
- Future npm wrapper: `npm/` inside the same repository

Do not create a separate npm bridge repository. The project owns the Python source code, so a colocated npm wrapper is simpler to version and audit.

## Release Automation

Add:

- CI across Linux, macOS, and Windows
- package builds for wheel and sdist
- `twine check`
- wheel content checks
- PyPI publish workflow for GitHub Release `published` and manual `workflow_dispatch`
- GitHub environment `pypi`
- OIDC permission only on the publish job
- SHA-pinned GitHub Actions

Use PyPI pending publisher for the first release:

- project: `paperang-cli`
- owner: `wyrtensi`
- repository: `paperang-cli`
- workflow: `pypi-publish.yml`
- environment: `pypi`

## Config Path Fix

Installed packages must not use `site-packages` as the default writable config location.

Use a per-user config directory:

- Windows: `%APPDATA%\paperang-cli\paperang-cli.config.json`
- Other platforms: `$XDG_CONFIG_HOME/paperang-cli/paperang-cli.config.json` when `XDG_CONFIG_HOME` exists
- Other platforms without XDG override: `~/.config/paperang-cli/paperang-cli.config.json`

Keep the existing precedence:

1. `--config PATH`
2. `PAPERANG_CLI_CONFIG`
3. per-user default path
4. built-in defaults

## Git Ignore Policy

Ignore Python caches, build output, test and type-check caches, local virtual environments, local configuration, editor settings, operating-system clutter, logs, wheel and tarball output, and future npm local artifacts.

## Agent Runbook

Add `docs/agents/publishing.md` with:

- bootstrap and first push
- GitHub environment setup
- PyPI pending publisher setup
- manual first publish
- ordinary release flow
- OIDC troubleshooting
- future npm wrapper direction
- explicit boundary between automatable GitHub steps and manual registry UI steps

## Verification

- Test default config paths with environment overrides.
- Run the Python test suite.
- Build wheel and sdist.
- Run `twine check`.
- Verify wheel contents.
- Initialize git and inspect ignored files before the first commit.
