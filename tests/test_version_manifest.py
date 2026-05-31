from __future__ import annotations

import json
from pathlib import Path

from paperang_cli import __version__
from paperang_cli._version import load_version_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_version_matches_manifest():
    manifest = load_version_manifest()

    assert __version__ == manifest["version"]


def test_contract_json_version_matches_manifest():
    manifest_version = load_version_manifest()["version"]
    contract = json.loads((ROOT / "docs" / "agents" / "cli-contract.json").read_text(encoding="utf-8"))

    assert contract["package_version"] == manifest_version


def test_npm_metadata_matches_manifest():
    manifest_version = load_version_manifest()["version"]
    package_json = json.loads((ROOT / "npm" / "package.json").read_text(encoding="utf-8"))
    package_lock = json.loads((ROOT / "npm" / "package-lock.json").read_text(encoding="utf-8"))

    assert package_json["version"] == manifest_version
    assert package_json["paperangCli"]["pythonPackageVersion"] == manifest_version
    assert package_lock["version"] == manifest_version
    assert package_lock["packages"][""]["version"] == manifest_version