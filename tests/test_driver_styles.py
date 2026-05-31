from __future__ import annotations

from pathlib import Path

from PIL import Image

from paperang_cli.config import PaperangCliConfig
from paperang_cli.drivers.paperang_p1 import PaperangP1Driver
from paperang_cli.models import PrintResult


def test_driver_text_uses_config_style_defaults(monkeypatch):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "text": {
                    "font_family": "mono",
                    "autofit": True,
                    "min_font_size": 12,
                    "orientation": "rotate-90-cw"
                }
            }
        }
    )
    driver = PaperangP1Driver(settings)
    captured: dict[str, object] = {}

    def fake_send_bitstream_job(**kwargs):
        captured.update(kwargs)
        return PrintResult(
            model="paperang_p1",
            address="AA:BB:CC:DD:EE:FF",
            operation=kwargs["operation"],
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"],
            feed_units=280,
            font_size=kwargs["font_size"],
            bytes_sent=len(kwargs["bitstream"]),
            styling=kwargs["styling"],
        )

    monkeypatch.setattr(driver, "_send_bitstream_job", fake_send_bitstream_job)

    result = driver.print_text(
        "long label",
        paragraph=False,
        font_size=None,
        font_family=None,
        min_font_size=None,
        autofit=None,
        orientation=None,
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        feed_mm=None,
        allow_paper_use=False,
        dry_run=True,
    )

    assert captured["operation"] == "text"
    assert captured["styling"]["font_family"] == "mono"
    assert captured["styling"]["orientation"] == "rotate-90-cw"
    assert captured["styling"]["autofit"] is True
    assert captured["styling"]["min_font_size"] == 12
    assert result.styling["font_family"] == "mono"


def test_driver_image_uses_config_style_defaults(monkeypatch, tmp_path: Path):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "image": {
                    "mode": "photo",
                    "orientation": "rotate-90-ccw"
                }
            }
        }
    )
    driver = PaperangP1Driver(settings)
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (32, 16), "white").save(image_path)
    captured: dict[str, object] = {}

    def fake_send_bitstream_job(**kwargs):
        captured.update(kwargs)
        return PrintResult(
            model="paperang_p1",
            address="AA:BB:CC:DD:EE:FF",
            operation=kwargs["operation"],
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"],
            feed_units=280,
            bytes_sent=len(kwargs["bitstream"]),
            conversion=kwargs["conversion"],
            styling=kwargs["styling"],
        )

    monkeypatch.setattr(driver, "_send_bitstream_job", fake_send_bitstream_job)

    result = driver.print_image(
        image_path,
        mode=None,
        conversion=None,
        orientation=None,
        feed_mm=None,
        allow_paper_use=False,
        dry_run=True,
    )

    assert captured["conversion"] == "dither"
    assert captured["styling"]["orientation"] == "rotate-90-ccw"
    assert captured["styling"]["mode"] == "photo"
    assert result.styling["orientation"] == "rotate-90-ccw"


def test_driver_compose_uses_supported_config_style_defaults(monkeypatch, tmp_path: Path):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "compose": {
                    "font_family": "mono",
                    "font_size": 30,
                    "horizontal_padding_px": 4,
                    "vertical_padding_px": 5,
                    "line_spacing_px": 2,
                    "layout": "image-above",
                    "spacer_height_px": 20,
                    "image_mode": "photo"
                }
            }
        }
    )
    driver = PaperangP1Driver(settings)
    image_path = tmp_path / "sample-compose.png"
    Image.new("RGB", (32, 16), "white").save(image_path)
    captured_render: dict[str, object] = {}
    captured_send: dict[str, object] = {}

    def fake_render_composed_bitstream(*args, **kwargs):
        captured_render.update(kwargs)
        return b"\x00" * 48

    def fake_send_bitstream_job(**kwargs):
        captured_send.update(kwargs)
        return PrintResult(
            model="paperang_p1",
            address="AA:BB:CC:DD:EE:FF",
            operation=kwargs["operation"],
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"],
            feed_units=280,
            bytes_sent=len(kwargs["bitstream"]),
            styling=kwargs["styling"],
        )

    monkeypatch.setattr("paperang_cli.drivers.paperang_p1.render_composed_bitstream", fake_render_composed_bitstream)
    monkeypatch.setattr(driver, "_send_bitstream_job", fake_send_bitstream_job)

    result = driver.print_compose(
        "label",
        image_path,
        layout=None,
        font_size=None,
        mode=None,
        conversion=None,
        feed_mm=None,
        allow_paper_use=False,
        dry_run=True,
    )

    assert captured_render["font_family"] == "mono"
    assert captured_render["horizontal_padding_px"] == 4
    assert captured_render["vertical_padding_px"] == 5
    assert captured_render["line_spacing_px"] == 2
    assert captured_render["spacer_height_px"] == 20
    assert captured_send["styling"]["layout"] == "image-above"
    assert captured_send["styling"]["mode"] == "photo"
    assert result.styling["font_family"] == "mono"
