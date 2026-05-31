from __future__ import annotations

from click.testing import CliRunner
from PIL import Image

from paperang_cli.cli import cli
from paperang_cli.drivers import registry


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


def test_self_test_dry_run_json(monkeypatch, fake_driver):
    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(cli, ["--json", "print", "self-test", "--dry-run"])

    assert result.exit_code == 0
    assert '"operation": "self-test"' in result.output
    assert '"warning":' in result.output


def test_config_show_json():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "config", "show"])

    assert result.exit_code == 0
    assert '"config_exists": false' in result.output
    assert '"supported_models": [' in result.output


def test_api_p1_json():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p1"])

    assert result.exit_code == 0
    assert '"class_name": "PaperangP1"' in result.output
    assert '"styling_support": {' in result.output
    assert '"rotated_compose_supported": false' in result.output
    assert '"allow_paper_use_methods": [' in result.output
    assert '"unsupported_parity_gaps": [' in result.output


def test_api_p1_human_output():
    runner = CliRunner()

    result = runner.invoke(cli, ["api", "p1"])

    assert result.exit_code == 0
    assert "API: PaperangP1" in result.output
    assert "Status: available" in result.output
    assert "Styling support:" in result.output
    assert "Rotated compose supported: False" in result.output
    assert "allow_paper_use required for" in result.output
    assert "Unsupported parity gaps:" in result.output


def test_api_list_json():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "list"])

    assert result.exit_code == 0
    assert '"api": "p1"' in result.output
    assert '"api": "p2"' in result.output
    assert '"status": "coming-soon"' in result.output


def test_api_p2_json_marks_unavailable():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p2"])

    assert result.exit_code == 0
    assert '"available": false' in result.output
    assert '"status": "coming-soon"' in result.output
    assert '"planned_class_name": "PaperangP2"' in result.output


def test_api_p2_human_output_marks_unavailable():
    runner = CliRunner()

    result = runner.invoke(cli, ["api", "p2"])

    assert result.exit_code == 0
    assert "API: PaperangP2" in result.output
    assert "Status: coming-soon" in result.output
    assert "Import: unavailable in this package version" in result.output