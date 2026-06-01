from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from paperang_cli import PaperangP1
from paperang_cli.api import PaperangP1 as PackagePaperangP1
from paperang_cli.api import get_api_contract, list_api_contract_summaries
from paperang_cli.drivers import registry


def test_api_package_import_exposes_p1_facade():
    assert PackagePaperangP1 is PaperangP1


def test_api_catalog_lists_available_and_coming_soon_entries():
    summaries = list_api_contract_summaries()

    assert summaries[0]["api"] == "p1"
    assert summaries[0]["available"] is True
    assert summaries[1]["api"] == "p2"
    assert summaries[1]["available"] is False
    assert summaries[1]["status"] == "coming-soon"


def test_api_contract_for_p2_is_placeholder_only():
    contract = get_api_contract("p2")

    assert contract["availability"]["available"] is False
    assert contract["planned_class_name"] == "PaperangP2"
    assert contract["class_name"] is None
    assert contract["methods"] == []


def test_api_connect_runs_non_printing_readiness(monkeypatch, fake_driver):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")

    returned = printer.connect()

    assert returned is printer
    assert printer.connected is True
    assert fake_driver.calls[-1][0] == "battery"
    assert fake_driver.calls[-1][1]["address"] == "AA:BB:CC:DD:EE:FF"


def test_api_disconnect_clears_cached_address(monkeypatch, fake_driver):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")
    printer.connect()

    printer.disconnect()

    assert printer.connected is False
    assert printer.address == "AA:BB:CC:DD:EE:FF"


def test_api_reads_explicit_config_file(monkeypatch, fake_driver, tmp_path):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(
        json.dumps(
            {
                "macaddress": "11:22:33:44:55:66",
                "print_density": 80,
                "post_print_feed_mm": 6.5,
            }
        ),
        encoding="utf-8",
    )

    printer = PaperangP1(config_path=config_path)

    assert printer.config_exists is True
    assert printer.config_path == config_path
    assert printer.address == "11:22:33:44:55:66"
    assert printer.settings.print_density == 80
    assert printer.settings.post_print_feed_mm == 6.5


def test_api_print_paragraph_delegates_to_driver(monkeypatch, fake_driver):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")

    result = printer.print_paragraph(
        "hello",
        font_size=20,
        font_family="mono",
        min_font_size=18,
        font_fit="largest-fitting",
        autofit=True,
        orientation="rotate-90-cw",
        dry_run=True,
    )

    assert result.operation == "paragraph"
    assert fake_driver.calls[-1][0] == "print_text"
    assert fake_driver.calls[-1][1]["paragraph"] is True
    assert fake_driver.calls[-1][1]["font_size"] == 20
    assert fake_driver.calls[-1][1]["font_family"] == "mono"
    assert fake_driver.calls[-1][1]["min_font_size"] == 18
    assert fake_driver.calls[-1][1]["font_fit"] == "largest-fitting"
    assert fake_driver.calls[-1][1]["autofit"] is True
    assert fake_driver.calls[-1][1]["orientation"] == "rotate-90-cw"


def test_api_print_image_resolves_mode_to_conversion(monkeypatch, fake_driver, tmp_path):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "sample.png"
    Image.linear_gradient("L").resize((32, 24)).convert("RGB").save(image_path)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")

    result = printer.print_image(image_path, mode="photo", orientation="rotate-90-cw", dry_run=True)

    assert result.conversion == "dither"
    assert fake_driver.calls[-1][0] == "print_image"
    assert fake_driver.calls[-1][1]["mode"] == "photo"
    assert fake_driver.calls[-1][1]["conversion"] == "dither"
    assert fake_driver.calls[-1][1]["orientation"] == "rotate-90-cw"


def test_api_print_compose_resolves_mode_and_layout(monkeypatch, fake_driver, tmp_path):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "sample-compose.png"
    Image.new("RGB", (32, 24), "white").save(image_path)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")

    result = printer.print_compose(
        "hello label",
        image_path,
        layout="image-above",
        min_font_size=14,
        font_fit="largest-fitting",
        mode="photo",
        dry_run=True,
    )

    assert result.operation == "compose"
    assert fake_driver.calls[-1][0] == "print_compose"
    assert fake_driver.calls[-1][1]["layout"] == "image-above"
    assert fake_driver.calls[-1][1]["min_font_size"] == 14
    assert fake_driver.calls[-1][1]["font_fit"] == "largest-fitting"
    assert fake_driver.calls[-1][1]["mode"] == "photo"
    assert fake_driver.calls[-1][1]["conversion"] == "dither"


def test_api_bt_mac_alias_delegates(monkeypatch, fake_driver):
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    printer = PaperangP1(address="AA:BB:CC:DD:EE:FF")

    result = printer.get_bt_mac()

    assert result.bluetooth_mac == "AA:BB:CC:DD:EE:FF"
    assert fake_driver.calls[-1][0] == "bluetooth_mac"


def test_readme_and_p1_api_docs_cover_font_fit_surface():
    repo_root = Path(__file__).resolve().parents[1]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    api_docs = (repo_root / "docs" / "usage" / "p1-api.md").read_text(encoding="utf-8")

    assert "font-fit" in readme_text
    assert "font_fit=" in api_docs
    assert "feed_mm=" in api_docs
    assert "print_compose()" in api_docs and "font_fit=" in api_docs