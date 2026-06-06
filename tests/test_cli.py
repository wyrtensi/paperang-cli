from __future__ import annotations

import json

from click.testing import CliRunner
from PIL import Image

from paperang_cli.cli import cli
from paperang_cli import config as config_module
from paperang_cli.drivers import registry
from paperang_cli.models import BluetoothMacStatus, PrinterStatus


def test_cli_help():
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "api" in result.output
    assert "battery" in result.output
    assert "mac" in result.output
    assert "probe" in result.output
    assert "status" in result.output
    assert "discover" in result.output
    assert "print" in result.output


def test_discover_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "discover"])

    assert result.exit_code == 0
    assert '"status": "ok"' in result.output
    assert 'AA:BB:CC:DD:EE:FF' in result.output


def test_status_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "status"])

    assert result.exit_code == 0
    assert '"battery_percent": 88' in result.output


def test_battery_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "battery"])

    assert result.exit_code == 0
    assert '"battery_percent": 88' in result.output
    assert '"transport": "ble"' in result.output


def test_mac_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "mac"])

    assert result.exit_code == 0
    assert '"bluetooth_mac": "AA:BB:CC:DD:EE:FF"' in result.output
    assert '"transport": "ble"' in result.output


def test_probe_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "probe"])

    assert result.exit_code == 0
    assert '"bluetooth_mac": "AA:BB:CC:DD:EE:FF"' in result.output
    assert '"local_transport_supported": false' in result.output


def test_probe_json_reports_local_transport_support_for_p2_usb(monkeypatch):
    class FakeP2Driver:
        def status(self, address=None):
            return PrinterStatus(
                model="paperang_p2",
                address=address or "usb://paperang_p2",
                transport="usb",
                connected=True,
                battery_percent=91,
                serial_number="P2TEST",
                firmware_version="2.0.0",
                hardware_info="abcdef01",
                density=75,
                power_off_time=120,
            )

        def bluetooth_mac(self, address=None):
            return BluetoothMacStatus(
                model="paperang_p2",
                address=address or "usb://paperang_p2",
                transport="usb",
                connected=True,
                bluetooth_mac="AA:BB:CC:DD:EE:FF",
            )

        def local_transport_supported(self):
            return True

        def local_transport_note(self):
            return "Paperang P2 is supported through BLE FF00/A5 when transport='ble'. USB is available only as an experimental software path."

    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: FakeP2Driver())

    result = runner.invoke(cli, ["--json", "probe"])

    assert result.exit_code == 0
    assert '"model": "paperang_p2"' in result.output
    assert '"transport": "usb"' in result.output
    assert '"local_transport_supported": true' in result.output


def test_print_text_dry_run_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "print", "text", "test print", "--dry-run"])

    assert result.exit_code == 0
    assert '"dry_run": true' in result.output
    assert '"feed_units": 280' in result.output


def test_print_text_dry_run_forwards_styling_overrides(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "text",
            "label text",
            "--dry-run",
            "--font-family",
            "mono",
            "--autofit",
            "--min-font-size",
            "18",
            "--orientation",
            "rotate-90-cw",
        ],
    )

    assert result.exit_code == 0
    assert '"orientation": "rotate-90-cw"' in result.output
    assert fake_driver.calls[-1][0] == "print_text"
    assert fake_driver.calls[-1][1]["font_family"] == "mono"
    assert fake_driver.calls[-1][1]["autofit"] is True
    assert fake_driver.calls[-1][1]["min_font_size"] == 18
    assert fake_driver.calls[-1][1]["orientation"] == "rotate-90-cw"


def test_print_text_dry_run_forwards_font_fit(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "text",
            "shopping list",
            "--dry-run",
            "--font-fit",
            "largest-fitting",
        ],
    )

    assert result.exit_code == 0
    assert fake_driver.calls[-1][0] == "print_text"
    assert fake_driver.calls[-1][1]["font_fit"] == "largest-fitting"


def test_print_paragraph_style_json_resolves_preset_and_cli_override(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    style_path = tmp_path / "paragraph-style.json"
    style_path.write_text('{"preset": "address-label", "paragraph": {"max_length_mm": 75.0}}', encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "paragraph",
            "label text",
            "--dry-run",
            "--style-json",
            str(style_path),
            "--font-size",
            "28",
        ],
    )

    assert result.exit_code == 0
    assert fake_driver.calls[-1][0] == "print_text"
    assert fake_driver.calls[-1][1]["resolved_style"]["font_family"] == "mono"
    assert fake_driver.calls[-1][1]["resolved_style"]["font_size"] == 28
    assert fake_driver.calls[-1][1]["resolved_style"]["orientation"] == "rotate-90-cw"
    assert fake_driver.calls[-1][1]["resolved_style"]["max_length_mm"] == 75.0


def test_print_paragraph_style_json_rejects_non_boolean_flags(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    style_path = tmp_path / "paragraph-style-invalid.json"
    style_path.write_text('{"paragraph": {"break_long_words": "false"}}', encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "paragraph",
            "label text",
            "--dry-run",
            "--style-json",
            str(style_path),
        ],
    )

    assert result.exit_code == 2
    assert '"status": "error"' in result.output
    assert '"code": "CONFIG_ERROR"' in result.output
    assert 'style_json_payload.paragraph.break_long_words must be a boolean' in result.output


def test_print_paragraph_style_json_reports_missing_file_as_config_error(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    style_path = tmp_path / "missing-style.json"

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "paragraph",
            "label text",
            "--dry-run",
            "--style-json",
            str(style_path),
        ],
    )

    assert result.exit_code == 2
    assert '"status": "error"' in result.output
    assert '"code": "CONFIG_ERROR"' in result.output
    assert 'Failed to read style JSON' in result.output


def test_cli_rejects_p1_usb_transport_as_unsupported(tmp_path):
    runner = CliRunner()
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(
        json.dumps(
            {
                "model": "paperang_p1",
                "transport": "usb",
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["--json", "--config", str(config_path), "config", "show"])

    assert result.exit_code == 2
    assert '"status": "error"' in result.output
    assert '"code": "CONFIG_ERROR"' in result.output
    assert "Unsupported transport 'usb' for model 'paperang_p1'" in result.output


def test_print_image_dry_run_json(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (16, 16), "black").save(image_path)

    result = runner.invoke(cli, ["--json", "print", "image", str(image_path), "--dry-run"])

    assert result.exit_code == 0
    assert '"operation": "image"' in result.output
    assert '"source_path":' in result.output


def test_print_image_dry_run_forwards_orientation(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "sample-rotate.png"
    Image.new("RGB", (16, 16), "black").save(image_path)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "image",
            str(image_path),
            "--dry-run",
            "--orientation",
            "rotate-90-ccw",
        ],
    )

    assert result.exit_code == 0
    assert '"orientation": "rotate-90-ccw"' in result.output
    assert fake_driver.calls[-1][0] == "print_image"
    assert fake_driver.calls[-1][1]["orientation"] == "rotate-90-ccw"


def test_print_image_photo_mode_resolves_to_dither(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "photo.png"
    Image.linear_gradient("L").resize((32, 24)).convert("RGB").save(image_path)

    result = runner.invoke(cli, ["--json", "print", "image", str(image_path), "--dry-run", "--mode", "photo"])

    assert result.exit_code == 0
    assert '"conversion": "dither"' in result.output
    assert fake_driver.calls[-1][1]["conversion"] == "dither"
    assert fake_driver.calls[-1][1]["mode"] == "photo"


def test_print_image_style_json_resolves_preset_and_cli_override(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "logo.png"
    Image.new("RGB", (24, 24), "black").save(image_path)
    style_path = tmp_path / "image-style.json"
    style_path.write_text('{"preset": "logo-strip", "image": {"fit_mode": "fit-within-length", "max_length_mm": 70.0}}', encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "image",
            str(image_path),
            "--dry-run",
            "--style-json",
            str(style_path),
            "--conversion",
            "edge",
        ],
    )

    assert result.exit_code == 0
    assert fake_driver.calls[-1][0] == "print_image"
    assert fake_driver.calls[-1][1]["resolved_style"]["orientation"] == "rotate-90-cw"
    assert fake_driver.calls[-1][1]["resolved_style"]["fit_mode"] == "fit-within-length"
    assert fake_driver.calls[-1][1]["resolved_style"]["max_length_mm"] == 70.0
    assert fake_driver.calls[-1][1]["resolved_style"]["conversion"] == "edge"


def test_print_compose_dry_run_json(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "badge.png"
    Image.new("RGB", (24, 24), "black").save(image_path)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "compose",
            "test print label",
            str(image_path),
            "--dry-run",
            "--layout",
            "image-above",
            "--mode",
            "photo",
        ],
    )

    assert result.exit_code == 0
    assert '"operation": "compose"' in result.output
    assert '"layout": "image-above"' in result.output
    assert '"conversion": "dither"' in result.output
    assert fake_driver.calls[-1][0] == "print_compose"
    assert fake_driver.calls[-1][1]["layout"] == "image-above"
    assert fake_driver.calls[-1][1]["mode"] == "photo"


def test_print_compose_style_json_resolves_json_and_cli_override(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "compose-style.png"
    Image.new("RGB", (24, 24), "black").save(image_path)
    style_path = tmp_path / "compose-style.json"
    style_path.write_text(
        '{"compose": {"font_family": "mono", "font_size": 26, "max_length_mm": 55.0, "overflow_policy": "report-only", "break_long_words": false, "image_mode": "photo"}}',
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "compose",
            "test print label",
            str(image_path),
            "--dry-run",
            "--style-json",
            str(style_path),
            "--layout",
            "image-above",
        ],
    )

    assert result.exit_code == 0
    assert fake_driver.calls[-1][0] == "print_compose"
    assert fake_driver.calls[-1][1]["resolved_style"]["font_family"] == "mono"
    assert fake_driver.calls[-1][1]["resolved_style"]["font_size"] == 26
    assert fake_driver.calls[-1][1]["resolved_style"]["image_mode"] == "photo"
    assert fake_driver.calls[-1][1]["resolved_style"]["layout"] == "image-above"
    assert fake_driver.calls[-1][1]["resolved_style"]["max_length_mm"] == 55.0


def test_print_compose_supports_font_fit_and_min_font_size(monkeypatch, fake_driver, tmp_path):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)
    image_path = tmp_path / "compose-largest-fit.png"
    Image.new("RGB", (24, 24), "black").save(image_path)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "compose",
            "household checklist",
            str(image_path),
            "--dry-run",
            "--font-fit",
            "largest-fitting",
            "--min-font-size",
            "14",
        ],
    )

    assert result.exit_code == 0
    assert fake_driver.calls[-1][0] == "print_compose"
    assert fake_driver.calls[-1][1]["font_fit"] == "largest-fitting"
    assert fake_driver.calls[-1][1]["min_font_size"] == 14


def test_self_test_dry_run_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "print", "self-test", "--dry-run"])

    assert result.exit_code == 0
    assert '"operation": "self-test"' in result.output
    assert '"warning":' in result.output


def test_config_show_json(monkeypatch, tmp_path):
    runner = CliRunner()
    monkeypatch.delenv("PAPERANG_CLI_CONFIG", raising=False)
    monkeypatch.setattr(config_module, "default_config_path", lambda: tmp_path / "paperang-cli.config.json")

    result = runner.invoke(cli, ["--json", "config", "show"])

    assert result.exit_code == 0
    assert '"config_exists": false' in result.output
    assert '"supported_models": [' in result.output


def test_global_printer_option_selects_named_profile(monkeypatch, fake_driver, tmp_path):
    captured = {}
    config_path = tmp_path / "paperang-cli.config.json"
    config_path.write_text(
        json.dumps(
            {
                "default_printer": "p1-kitchen",
                "printers": {
                    "p1-kitchen": {
                        "model": "paperang_p1",
                        "transport": "ble",
                        "macaddress": "AA:BB:CC:DD:EE:01",
                    },
                    "p2-desk": {
                        "model": "paperang_p2",
                        "transport": "ble",
                        "macaddress": "AA:BB:CC:DD:EE:02",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_get_driver(settings):
        captured["settings"] = settings
        return fake_driver

    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", fake_get_driver)

    result = runner.invoke(
        cli,
        [
            "--json",
            "--config",
            str(config_path),
            "--printer",
            "p2-desk",
            "status",
        ],
    )

    assert result.exit_code == 0
    assert captured["settings"].active_printer == "p2-desk"
    assert captured["settings"].model == "paperang_p2"
    assert captured["settings"].macaddress == "AA:BB:CC:DD:EE:02"


def test_api_p1_json():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p1"])

    assert result.exit_code == 0
    assert '"class_name": "PaperangP1"' in result.output
    assert '"styling_support": {' in result.output
    assert '"rotated_compose_supported": false' in result.output
    assert '"allow_paper_use_methods": [' in result.output
    assert '"unsupported_parity_gaps": [' in result.output


def test_api_p1_json_mentions_cli_style_json_and_length_metrics():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p1"])

    assert result.exit_code == 0
    assert '"preset_catalog_available": true' in result.output
    assert '"cli_style_json_support": true' in result.output
    assert '"python_api_style_json_support": false' in result.output
    assert '"length_metrics": [' in result.output


def test_api_p1_human_output():
    runner = CliRunner()

    result = runner.invoke(cli, ["api", "p1"])

    assert result.exit_code == 0
    assert "API: PaperangP1" in result.output
    assert "Status: available" in result.output
    assert "Styling support:" in result.output
    assert "CLI style-json support: True" in result.output
    assert "Python API style-json support: False" in result.output
    assert "Length metrics:" in result.output
    assert "Rotated compose supported: False" in result.output
    assert "allow_paper_use required for" in result.output
    assert "Unsupported parity gaps:" in result.output


def test_api_list_json():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "list"])

    assert result.exit_code == 0
    assert '"api": "p1"' in result.output
    assert '"api": "p2"' in result.output
    assert '"status": "available"' in result.output


def test_api_p2_json_reports_live_contract():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p2"])

    assert result.exit_code == 0
    assert '"available": true' in result.output
    assert '"status": "available"' in result.output
    assert '"class_name": "PaperangP2"' in result.output
    assert '"transport": "ble"' in result.output


def test_api_p2_human_output_reports_live_contract():
    runner = CliRunner()

    result = runner.invoke(cli, ["api", "p2"])

    assert result.exit_code == 0
    assert "API: PaperangP2" in result.output
    assert "Status: available" in result.output
    assert "Import: from paperang_cli import PaperangP2" in result.output
    assert "Transport: ble" in result.output
