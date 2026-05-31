# License And README Design

## Scope

Update the standalone `paperang-cli` package only. Do not rewrite the legacy repository README or its root license.

## License

Add a package-local `LICENSE` file using the standard MIT License text.

Preserve attribution for the earlier Paperang P1 control work:

- Copyright (c) 2017 ihc童鞋@提不起劲
- Copyright (c) 2019 BroncoTc

Add the current package maintainer:

- Copyright (c) 2026 wyrtensi

## README

Rewrite `paperang-cli/README.md` as the primary human entry point for the standalone package.

The README should:

- explain what the package does
- state the supported model and BLE-only transport boundary
- provide installation and first-run commands
- lead with safe non-printing checks and matching dry-runs
- document real-print allow flags
- summarize commands without duplicating the full command reference
- describe experimental image and compose printing clearly
- link to package documentation
- acknowledge the earlier Paperang P1 control work
- link to the package-local MIT license

Avoid protocol internals and implementation notes that do not help ordinary users.

## Verification

- Confirm that the package-local license contains all three copyright lines.
- Confirm that README links resolve to existing local files.
- Run the existing package tests.

## Repository Note

The available workspace tree does not contain `.git` metadata, so this design document cannot be committed locally.
