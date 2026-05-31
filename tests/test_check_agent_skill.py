from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check-agent-skill.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_agent_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_skill_contract_version_matches_python_package():
    checker = load_checker()

    checker.validate_version_sync()


def test_skill_keeps_hardware_safety_rules_close_at_hand():
    checker = load_checker()

    checker.validate_safety_rules()


def test_public_skill_mirror_matches_project_skill():
    checker = load_checker()

    checker.validate_public_skill_sync()
