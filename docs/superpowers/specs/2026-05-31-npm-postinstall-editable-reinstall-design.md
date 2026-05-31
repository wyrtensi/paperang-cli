# npm Postinstall Editable Reinstall Design

## Goal

Ensure that installing or upgrading the npm wrapper replaces an existing editable
`paperang-cli` Python installation with the matching wheel from PyPI, even when
both installations report the same version.

## Problem

The npm wrapper currently runs:

```powershell
python -m pip install --upgrade paperang-cli==<matching-version>
```

When the selected Python environment already contains an editable installation
with the same version, pip reports that the requirement is already satisfied.
The npm install succeeds, but `python -m paperang_cli` continues importing the
developer checkout instead of the published wheel.

## Design

Keep the existing dependency-aware pip install, then always reinstall only the
top-level Python package:

```powershell
python -m pip install --upgrade paperang-cli==<matching-version>
python -m pip install --force-reinstall --no-deps paperang-cli==<matching-version>
```

The first command installs or updates runtime dependencies. The second command
replaces the top-level package with the PyPI wheel without redownloading or
reinstalling heavy dependencies. Apply the existing `--user` retry behavior to
the complete two-command sequence so both commands target the same install
scope.

Keep the wrapper small: do not add editable-install detection, metadata parsing,
or platform-specific branches. A deterministic reinstall is simpler and also
repairs stale ordinary installations of the matching package version.

## Testing

Add focused unit coverage for the pip argument construction used by
`npm/scripts/postinstall.js`.

Add an integration test that:

1. Creates an isolated virtual environment.
2. Installs the repository in editable mode.
3. Runs the same two-command install sequence used by the npm wrapper.
4. Asserts that `pip freeze` no longer reports an editable `paperang-cli`.
5. Asserts that importing `paperang_cli` resolves inside the virtual
   environment's `site-packages`.
6. Runs `pip check`.

The integration test may use the network because its purpose is to verify
replacement with the matching published PyPI wheel. Run it as release
validation after `paperang-cli==0.1.6` exists on PyPI; keep pre-publish CI
coverage focused on argument construction so CI does not require an unpublished
wheel.

## Documentation

Update `SECURITY.md`, `npm/README.md`, and `docs/agents/publishing.md` to explain
the two-step postinstall behavior and why the second command uses
`--force-reinstall --no-deps`.

## Release

Bump the source-of-truth version to `0.1.6` and run the repository sync script
so Python, npm, and contract metadata remain aligned. Commit and push the
changes without creating a GitHub Release. Publishing PyPI and npm remains a
separate, explicit operation.
