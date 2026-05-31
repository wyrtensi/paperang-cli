from __future__ import annotations

import json

import pytest

from paperang_cli import config as config_module
from paperang_cli.errors import ConfigError


def test_load_config_uses_defaults_when_default_file_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "paperang-cli.config.json"
    monkeypatch.setattr(config_module, "default_config_path", lambda: missing_path)

    settings, resolved_path, exists = config_module.load_config()

    assert exists is False
    assert resolved_path == missing_path
    assert settings.model == "paperang_p1"
    assert settings.post_print_feed_mm == 5.0


def test_default_config_path_uses_appdata_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(config_module.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert config_module.default_config_path() == tmp_path / "paperang-cli" / "paperang-cli.config.json"


def test_default_config_path_uses_xdg_config_home_when_available(monkeypatch, tmp_path):
    monkeypatch.setattr(config_module.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert config_module.default_config_path() == tmp_path / "paperang-cli" / "paperang-cli.config.json"


def test_load_config_explicit_missing_path_raises(tmp_path):
    with pytest.raises(ConfigError):
        config_module.load_config(tmp_path / "missing.json")


def test_write_example_config_creates_file(tmp_path):
    destination = tmp_path / "paperang-cli.config.json"

    written = config_module.write_example_config(destination)

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert written == destination
    assert payload["model"] == "paperang_p1"
    assert payload["print_defaults"]["text"]["font_family"] == "sans"
    assert payload["print_defaults"]["image"]["orientation"] == "normal"
    assert "orientation" not in payload["print_defaults"]["compose"]
    assert "autofit" not in payload["print_defaults"]["compose"]


def test_load_config_accepts_partial_json_mapping(tmp_path):
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(json.dumps({"macaddress": "11:22:33:44:55:66"}), encoding="utf-8")

    settings, resolved_path, exists = config_module.load_config(config_path)

    assert exists is True
    assert resolved_path == config_path
    assert settings.macaddress == "11:22:33:44:55:66"
    assert settings.printerwidth == 384
    assert settings.print_density == 75
    assert settings.post_print_feed_mm == 5.0
    assert settings.print_defaults.text.font_family == "sans"
    assert settings.print_defaults.compose.layout == "text-above"


def test_load_config_accepts_partial_nested_print_defaults(tmp_path):
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(
        json.dumps(
            {
                "print_defaults": {
                    "text": {
                        "font_family": "mono",
                        "autofit": True,
                        "min_font_size": 18,
                        "orientation": "rotate-90-cw"
                    },
                    "image": {
                        "orientation": "rotate-90-ccw"
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    settings, _, exists = config_module.load_config(config_path)

    assert exists is True
    assert settings.print_defaults.text.font_family == "mono"
    assert settings.print_defaults.text.autofit is True
    assert settings.print_defaults.text.min_font_size == 18
    assert settings.print_defaults.text.orientation == "rotate-90-cw"
    assert settings.print_defaults.image.orientation == "rotate-90-ccw"
    assert settings.print_defaults.paragraph.orientation == "normal"
    assert settings.print_defaults.compose.layout == "text-above"


def test_load_config_rejects_invalid_nested_print_defaults(tmp_path):
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(
        json.dumps(
            {
                "print_defaults": {
                    "text": {
                        "font_family": "comic-sans"
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="print_defaults.text.font_family"):
        config_module.load_config(config_path)
