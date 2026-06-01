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
    SKILL_ROOT / "examples" / "address-label.json",
    SKILL_ROOT / "examples" / "fridge-note.json",
    SKILL_ROOT / "examples" / "chore-list.json",
    SKILL_ROOT / "examples" / "pantry-label.json",
    SKILL_ROOT / "examples" / "cable-tag.json",
    SKILL_ROOT / "examples" / "storage-bin.json",
    SKILL_ROOT / "examples" / "receipt-note.json",
    SKILL_ROOT / "examples" / "logo-strip.json",
    SKILL_ROOT / "examples" / "product-style.json",
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
REQUIRED_SCENARIO_TEXT = (
    "examples/address-label.json",
    "examples/receipt-note.json",
    "examples/logo-strip.json",
    "examples/product-style.json",
    "estimated_length_mm",
    "fits_length_limit",
)
EXPECTED_SCENARIO_PAYLOADS = {
    "address-label.json": ("preset", "paragraph"),
    "receipt-note.json": ("preset", "paragraph"),
    "logo-strip.json": ("preset", "image"),
    "product-style.json": ("compose",),
}
REQUIRED_HOME_SCENARIO_TEXT = (
    "examples/pantry-label.json",
    "examples/cable-tag.json",
    "examples/storage-bin.json",
)
EXPECTED_HOME_SCENARIO_PAYLOADS = {
    "pantry-label.json": ("preset", "paragraph"),
    "cable-tag.json": ("preset", "paragraph"),
    "storage-bin.json": ("preset", "paragraph"),
}
REQUIRED_GENERAL_HOME_SCENARIO_TEXT = (
    "examples/fridge-note.json",
    "examples/chore-list.json",
)
EXPECTED_GENERAL_HOME_SCENARIO_PAYLOADS = {
    "fridge-note.json": ("preset", "paragraph"),
    "chore-list.json": ("preset", "paragraph"),
}
REQUIRED_SCENARIO_FLEXIBILITY_TEXT = (
    "starting points, not a whitelist",
    "build a fresh payload when none of the examples fit the request",
)
REQUIRED_FONT_FIT_GUIDANCE = (
    "font-fit",
    "font-fit mode",
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


def validate_scenario_examples() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_SCENARIO_TEXT:
        assert required_text in skill_text, f"Missing scenario guidance text: {required_text}"

    for file_name, required_keys in EXPECTED_SCENARIO_PAYLOADS.items():
        payload = json.loads((SKILL_ROOT / "examples" / file_name).read_text(encoding="utf-8"))
        for required_key in required_keys:
            assert required_key in payload, f"Scenario example {file_name} is missing key: {required_key}"


def validate_home_scenario_examples() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_HOME_SCENARIO_TEXT:
        assert required_text in skill_text, f"Missing home scenario guidance text: {required_text}"

    for file_name, required_keys in EXPECTED_HOME_SCENARIO_PAYLOADS.items():
        payload = json.loads((SKILL_ROOT / "examples" / file_name).read_text(encoding="utf-8"))
        for required_key in required_keys:
            assert required_key in payload, f"Home scenario example {file_name} is missing key: {required_key}"


def validate_general_home_scenario_examples() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_GENERAL_HOME_SCENARIO_TEXT:
        assert required_text in skill_text, f"Missing general home scenario guidance text: {required_text}"

    for file_name, required_keys in EXPECTED_GENERAL_HOME_SCENARIO_PAYLOADS.items():
        payload = json.loads((SKILL_ROOT / "examples" / file_name).read_text(encoding="utf-8"))
        for required_key in required_keys:
            assert required_key in payload, f"General home scenario example {file_name} is missing key: {required_key}"


def validate_scenario_choice_flexibility() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required_text in REQUIRED_SCENARIO_FLEXIBILITY_TEXT:
        assert required_text in skill_text, f"Missing scenario flexibility guidance text: {required_text}"


def validate_font_fit_guidance() -> None:
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    contract_markdown = (SKILL_ROOT / "references" / "cli-contract.md").read_text(encoding="utf-8")
    contract_json = json.loads((SKILL_ROOT / "references" / "cli-contract.json").read_text(encoding="utf-8"))

    assert REQUIRED_FONT_FIT_GUIDANCE[0] in skill_text, "Skill guidance must mention font-fit in matching dry-runs"
    assert REQUIRED_FONT_FIT_GUIDANCE[0] in contract_markdown, (
        "Human-readable contract guidance must mention font-fit in matching dry-runs"
    )
    assert REQUIRED_FONT_FIT_GUIDANCE[1] in contract_json["safety_policy"]["matching_dry_run_definition"], (
        "Machine-readable contract guidance must mention font-fit mode in matching dry-runs"
    )


def main() -> int:
    validate_required_files()
    validate_frontmatter()
    validate_reference_sync()
    validate_public_skill_sync()
    validate_version_sync()
    validate_safety_rules()
    validate_scenario_examples()
    validate_home_scenario_examples()
    validate_general_home_scenario_examples()
    validate_scenario_choice_flexibility()
    validate_font_fit_guidance()
    print("paperang-cli Agent Skill is valid; references and public mirror are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
