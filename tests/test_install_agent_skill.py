from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "install-agent-skill.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_agent_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def create_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    (source / "agents").mkdir(parents=True)
    (source / "references").mkdir()
    (source / "SKILL.md").write_text("---\nname: paperang-cli\ndescription: test\n---\n", encoding="utf-8")
    (source / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
    (source / "references" / "cli-contract.md").write_text("contract\n", encoding="utf-8")
    (source / "references" / "cli-contract.json").write_text("{}\n", encoding="utf-8")
    return source


def test_target_directories_cover_supported_clients(tmp_path):
    installer = load_installer()

    assert installer.target_directories(tmp_path, "all") == [
        tmp_path / ".codex" / "skills" / "paperang-cli",
        tmp_path / ".claude" / "skills" / "paperang-cli",
        tmp_path / ".copilot" / "skills" / "paperang-cli",
        tmp_path / ".agents" / "skills" / "paperang-cli",
    ]


def test_install_local_copies_skill_files(tmp_path):
    installer = load_installer()
    source = create_source(tmp_path)

    destinations = installer.install_skill(source, tmp_path / "home", "codex", force=False)

    assert destinations == [tmp_path / "home" / ".codex" / "skills" / "paperang-cli"]
    assert (destinations[0] / "SKILL.md").read_text(encoding="utf-8").startswith("---")
    assert (destinations[0] / "references" / "cli-contract.json").read_text(encoding="utf-8") == "{}\n"


def test_install_local_refuses_to_overwrite_existing_skill(tmp_path):
    installer = load_installer()
    source = create_source(tmp_path)
    destination = tmp_path / "home" / ".codex" / "skills" / "paperang-cli"
    destination.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="--force"):
        installer.install_skill(source, tmp_path / "home", "codex", force=False)


def test_install_local_force_replaces_existing_skill(tmp_path):
    installer = load_installer()
    source = create_source(tmp_path)
    destination = tmp_path / "home" / ".codex" / "skills" / "paperang-cli"
    destination.mkdir(parents=True)
    (destination / "stale.txt").write_text("stale\n", encoding="utf-8")

    installer.install_skill(source, tmp_path / "home", "codex", force=True)

    assert not (destination / "stale.txt").exists()
    assert (destination / "SKILL.md").exists()


def test_download_remote_skill_fetches_fixed_file_set(tmp_path):
    installer = load_installer()
    source = create_source(tmp_path)
    destination = tmp_path / "download"

    installer.download_remote_skill(destination, source.as_uri())

    assert sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    ) == sorted(installer.SKILL_FILES)
