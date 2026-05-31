#!/usr/bin/env python3
"""Validate the bundled paperang-cli Agent Skill and synchronized references."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "paperang-cli"
PUBLIC_SKILL_ROOT = REPO_ROOT / "skills" / "paperang-cli"
VERSION_MANIFEST_PATH = REPO_ROOT / "src" / "paperang_cli" / "version-manifest.json"
VERSION_MODULE_PATH = REPO_ROOT / "src" / "paperang_cli" / "_version.py"
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


def load_version_manifest() -> dict:
    return json.loads(VERSION_MANIFEST_PATH.read_text(encoding="utf-8"))


def load_runtime_version() -> str:
    spec = importlib.util.spec_from_file_location("paperang_cli_version", VERSION_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.__version__


def validate_version_sync() -> None:
    package_version = str(load_version_manifest()["version"])
    runtime_version = load_runtime_version()
    contract = json.loads((SKILL_ROOT / "references" / "cli-contract.json").read_text(encoding="utf-8"))

    assert package_version == runtime_version == contract["package_version"]


def validate_safety_rules() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_SAFETY_TEXT:
        assert required_text in skill_text, f"Missing required safety guidance: {required_text}"

    policy = json.loads((SKILL_ROOT / "references" / "cli-contract.json").read_text(encoding="utf-8"))["safety_policy"]
    assert policy["imperative_request_authorizes_one_matching_non_self_test_real_print"] is True
    assert policy["follow_up_real_print_approval_required_when_initial_request_is_exploratory_or_ambiguous"] is True
    assert {"parameters changed after dry-run", "copies", "retries", "repeated prints"} <= set(
        policy["new_approval_required_for"]
    )
    assert policy["self_test_always_requires_specific_follow_up_approval"] is True


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
