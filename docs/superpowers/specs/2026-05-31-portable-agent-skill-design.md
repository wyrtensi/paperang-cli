# Portable Agent Skill Design

## Goal

Publish a self-contained `paperang-cli` Agent Skill that is discoverable from a repository checkout and installable for common agent clients on Windows, Linux, and macOS.

## Canonical Layout

Store one canonical skill at:

```text
.agents/skills/paperang-cli/
```

This location follows the open Agent Skills directory format and is discovered as a project skill by GitHub Copilot. Do not commit duplicate `.github/skills`, `.claude/skills`, or `.codex/skills` copies because duplicate files would drift.

The skill contains:

```text
.agents/skills/paperang-cli/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── cli-contract.md
    └── cli-contract.json
```

The reference files are synchronized copies of the canonical repository contract under `docs/agents/`. They make an installed personal skill self-contained outside a repository checkout.

## Installation

Prefer GitHub CLI `2.90.0+` for preview, provenance-aware installation, updates, and host-specific placement across its supported editor and coding-agent list.

Keep a byte-identical distributable mirror at `skills/paperang-cli/` so GitHub CLI preview, install, update, and publish flows use the standard visible skill convention.

Add `scripts/install-agent-skill.py` as a transparent cross-platform fallback. It installs the distributable skill into one or more common personal skill locations:

| Target | Destination |
| --- | --- |
| `codex` | `~/.codex/skills/paperang-cli` |
| `claude` | `~/.claude/skills/paperang-cli` |
| `copilot` | `~/.copilot/skills/paperang-cli` |
| `cursor` | `~/.cursor/skills/paperang-cli` |
| `antigravity` | `~/.gemini/antigravity/skills/paperang-cli` |
| `agents` | `~/.agents/skills/paperang-cli` |
| `all` | all destinations above |

The installer supports:

- `--source auto`: prefer a local checkout and otherwise download from GitHub
- `--source local`: copy from a checkout
- `--source github`: download from the public repository
- `--force`: replace an existing installed copy
- `--home PATH`: override the home directory for tests and controlled installs
- `--ref REF`: choose the GitHub branch, tag, or commit used for download

The remote mode downloads a fixed allowlist of skill files. It does not execute downloaded code.

## Safety And Portability

The skill is available to agents on all operating systems. This does not expand hardware claims: real BLE communication and physical printing remain tested only on Windows. Linux and macOS compatibility checks are not hardware validation.

The skill must keep printing safety rules close to the top of `SKILL.md`: perform matching dry-runs, request explicit approval before paper use, and never automatically append allow flags after a safety error.

## Documentation And Validation

Update README with:

- repository-checkout discovery through `.agents/skills/`
- local installer commands
- direct-download installer commands for PowerShell and POSIX shells
- a ready-to-paste request for another agent

Extend CI to:

- validate skill frontmatter
- prove bundled reference copies match `docs/agents/`
- prove the public distribution mirror matches `.agents/skills/`
- run installer tests
