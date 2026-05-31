#!/usr/bin/env python3
"""Sync versioned metadata files from the canonical version manifest."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_MANIFEST_PATH = REPO_ROOT / "src" / "paperang_cli" / "version-manifest.json"
CONTRACT_JSON_PATH = REPO_ROOT / "docs" / "agents" / "cli-contract.json"
NPM_PACKAGE_PATH = REPO_ROOT / "npm" / "package.json"
NPM_PACKAGE_LOCK_PATH = REPO_ROOT / "npm" / "package-lock.json"
REFERENCE_TARGETS = (
    REPO_ROOT / ".agents" / "skills" / "paperang-cli" / "references" / "cli-contract.md",
    REPO_ROOT / ".agents" / "skills" / "paperang-cli" / "references" / "cli-contract.json",
    REPO_ROOT / "skills" / "paperang-cli" / "references" / "cli-contract.md",
    REPO_ROOT / "skills" / "paperang-cli" / "references" / "cli-contract.json",
)


def load_version_manifest() -> dict:
    return json.loads(VERSION_MANIFEST_PATH.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync_contract_json(version: str) -> None:
    contract = json.loads(CONTRACT_JSON_PATH.read_text(encoding="utf-8"))
    contract["package_version"] = version
    write_json(CONTRACT_JSON_PATH, contract)


def sync_npm_metadata(version: str) -> None:
    package_json = json.loads(NPM_PACKAGE_PATH.read_text(encoding="utf-8"))
    package_json["version"] = version
    package_json["paperangCli"]["pythonPackageVersion"] = version
    write_json(NPM_PACKAGE_PATH, package_json)

    package_lock = json.loads(NPM_PACKAGE_LOCK_PATH.read_text(encoding="utf-8"))
    package_lock["version"] = version
    package_lock.setdefault("packages", {}).setdefault("", {})["version"] = version
    write_json(NPM_PACKAGE_LOCK_PATH, package_lock)


def sync_contract_references() -> None:
    canonical_md = REPO_ROOT / "docs" / "agents" / "cli-contract.md"
    canonical_json = CONTRACT_JSON_PATH
    source_map = {
        canonical_md.name: canonical_md,
        canonical_json.name: canonical_json,
    }

    for target in REFERENCE_TARGETS:
        source = source_map[target.name]
        shutil.copyfile(source, target)


def main() -> int:
    version = str(load_version_manifest()["version"])
    sync_contract_json(version)
    sync_npm_metadata(version)
    sync_contract_references()
    print(f"Synchronized paperang-cli metadata from version manifest: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())