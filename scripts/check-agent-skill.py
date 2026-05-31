#!/usr/bin/env python3
"""Validate the bundled paperang-cli Agent Skill and synchronized references."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "paperang-cli"
PUBLIC_SKILL_ROOT = REPO_ROOT / "skills" / "paperang-cli"
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
REQUIRED_SKILL_FILES = (
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "agents" / "openai.yaml",
    SKILL_ROOT / "references" / "cli-contract.md",
    SKILL_ROOT / "references" / "cli-contract.json",
)
REQUIRED_SAFETY_TEXT = (
    "--dry-run",
    "--allow-paper-use",
    "--allow-large-paper-use",
    "SAFETY_ERROR",
    "Never automatically append an allow flag or retry.",
    "Real BLE communication and physical printing have been tested only on Windows.",
)


def validate_required_files() -> None:
    for path in REQUIRED_SKILL_FILES:
        assert path.is_file(), f"Missing Agent Skill file: {path}"


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


def validate_public_skill_sync() -> None:
    project_files = {
        path.relative_to(SKILL_ROOT)
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
    }
    public_files = {
        path.relative_to(PUBLIC_SKILL_ROOT)
        for path in PUBLIC_SKILL_ROOT.rglob("*")
        if path.is_file()
    }

    assert public_files == project_files, "Public Agent Skill mirror file list is out of sync"
    for relative_path in project_files:
        assert (PUBLIC_SKILL_ROOT / relative_path).read_bytes() == (SKILL_ROOT / relative_path).read_bytes(), (
            f"Out-of-sync public Agent Skill mirror: {relative_path}"
        )


def validate_version_sync() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = project["project"]["version"]
    init_text = (REPO_ROOT / "src" / "paperang_cli" / "__init__.py").read_text(encoding="utf-8")
    init_version = re.search(r'__version__ = "([^"]+)"', init_text).group(1)
    contract = json.loads((SKILL_ROOT / "references" / "cli-contract.json").read_text(encoding="utf-8"))

    assert package_version == init_version == contract["package_version"]


def validate_safety_rules() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_SAFETY_TEXT:
        assert required_text in skill_text, f"Missing required safety guidance: {required_text}"


def main() -> int:
    validate_required_files()
    validate_frontmatter()
    validate_reference_sync()
    validate_public_skill_sync()
    validate_version_sync()
    validate_safety_rules()
    print("paperang-cli Agent Skill is valid; references and public mirror are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
