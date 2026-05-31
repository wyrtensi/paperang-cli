#!/usr/bin/env python3
"""Validate the bundled paperang-cli Agent Skill and synchronized references."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "paperang-cli"
CONTRACT_PAIRS = (
    (
        REPO_ROOT / "docs" / "agents" / "cli-contract.md",
        SKILL_ROOT / "references" / "cli-contract.md",
    ),
    (
        REPO_ROOT / "docs" / "agents" / "cli-contract.json",
        SKILL_ROOT / "references" / "cli-contract.json",
    ),
)


def validate_frontmatter() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", skill_text, re.DOTALL)
    assert match is not None, "SKILL.md must start with YAML frontmatter"

    frontmatter = {}
    for line in match.group(1).splitlines():
        key, value = line.split(":", maxsplit=1)
        frontmatter[key.strip()] = value.strip().strip('"')

    assert set(frontmatter) == {"name", "description", "license"}
    assert frontmatter["name"] == "paperang-cli"
    assert frontmatter["description"]
    assert len(frontmatter["description"]) <= 1024
    assert frontmatter["license"] == "MIT"


def validate_reference_sync() -> None:
    for canonical, bundled in CONTRACT_PAIRS:
        assert bundled.read_bytes() == canonical.read_bytes(), f"Out-of-sync bundled reference: {bundled}"


def main() -> int:
    validate_frontmatter()
    validate_reference_sync()
    print("paperang-cli Agent Skill is valid and references are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
