from __future__ import annotations

from pathlib import Path

from PIL import Image

from paperang_cli.config import PaperangCliConfig
from paperang_cli.drivers.paperang_p1 import PaperangP1Driver
from paperang_cli.models import PrintResult
from paperang_cli.render import RenderStyling, RenderedBitstream


def test_driver_text_uses_config_style_defaults(monkeypatch):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "text": {
                    "font_family": "mono",
                    "font_fit": "largest-fitting",
                    "autofit": True,
                    "min_font_size": 12,
                    "orientation": "rotate-90-cw",
                    "max_length_mm": 72.0,
                    "overflow_policy": "shrink-to-fit",
                    "break_long_words": False,
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
            estimated_length_mm=kwargs["estimated_length_mm"],
            max_length_mm=kwargs["max_length_mm"],
            fits_length_limit=kwargs["fits_length_limit"],
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
    assert captured["styling"]["font_fit"] == "largest-fitting"
    assert captured["styling"]["orientation"] == "rotate-90-cw"
    assert captured["styling"]["autofit"] is True
    assert captured["styling"]["min_font_size"] == 12
    assert captured["styling"]["max_length_mm"] == 72.0
    assert captured["styling"]["overflow_policy"] == "shrink-to-fit"
    assert captured["styling"]["break_long_words"] is False
    assert captured["estimated_length_mm"] is not None
    assert captured["max_length_mm"] == 72.0
    assert captured["fits_length_limit"] is True
    assert result.styling["font_family"] == "mono"


def test_driver_text_forwards_printable_width_mm_for_rotated_length(monkeypatch):
    settings = PaperangCliConfig.from_mapping(
        {
            "calibration": {
                "printable_width_mm": 41.5,
                "advance_mm_per_px": 0.1217,
            },
            "print_defaults": {
                "text": {
                    "orientation": "rotate-90-cw",
                }
            },
        }
    )
    driver = PaperangP1Driver(settings)
    captured_render: dict[str, object] = {}

    def fake_render_text_job(*args, **kwargs):
        captured_render.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 48,
            width=384,
            height=100,
            styling=RenderStyling(orientation="rotate-90-cw", font_size=24),
            estimated_length_mm=10.81,
            fits_length_limit=True,
        )

    def fake_send_bitstream_job(**kwargs):
        return PrintResult(
            model="paperang_p1",
            address="AA:BB:CC:DD:EE:FF",
            operation=kwargs["operation"],
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"],
            feed_units=280,
            font_size=kwargs["font_size"],
            bytes_sent=len(kwargs["bitstream"]),
            estimated_length_mm=kwargs["estimated_length_mm"],
            max_length_mm=kwargs["max_length_mm"],
            fits_length_limit=kwargs["fits_length_limit"],
            styling=kwargs["styling"],
        )

    monkeypatch.setattr("paperang_cli.drivers.paperang_p1.render_text_job", fake_render_text_job)
    monkeypatch.setattr(driver, "_send_bitstream_job", fake_send_bitstream_job)

    driver.print_text(
        "rotated label",
        paragraph=False,
        font_size=24,
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

    assert captured_render["printable_width_mm"] == 41.5


def test_driver_image_uses_config_style_defaults(monkeypatch, tmp_path: Path):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "image": {
                    "mode": "photo",
                    "orientation": "rotate-90-ccw",
                    "max_length_mm": 90.0,
                    "fit_mode": "fit-within-length",
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
            estimated_length_mm=kwargs["estimated_length_mm"],
            max_length_mm=kwargs["max_length_mm"],
            fits_length_limit=kwargs["fits_length_limit"],
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
    assert captured["styling"]["max_length_mm"] == 90.0
    assert captured["styling"]["fit_mode"] == "fit-within-length"
    assert captured["estimated_length_mm"] is not None
    assert captured["max_length_mm"] == 90.0
    assert captured["fits_length_limit"] is True
    assert result.styling["orientation"] == "rotate-90-ccw"


def test_driver_compose_uses_supported_config_style_defaults(monkeypatch, tmp_path: Path):
    settings = PaperangCliConfig.from_mapping(
        {
            "print_defaults": {
                "compose": {
                    "font_family": "mono",
                    "font_size": 30,
                    "min_font_size": 14,
                    "font_fit": "largest-fitting",
                    "horizontal_padding_px": 4,
                    "vertical_padding_px": 5,
                    "line_spacing_px": 2,
                    "layout": "image-above",
                    "spacer_height_px": 20,
                    "image_mode": "photo",
                    "max_length_mm": 55.0,
                    "overflow_policy": "report-only",
                    "break_long_words": False,
                }
            }
        }
    )
    driver = PaperangP1Driver(settings)
    image_path = tmp_path / "sample-compose.png"
    Image.new("RGB", (32, 16), "white").save(image_path)
    captured_render: dict[str, object] = {}
    captured_send: dict[str, object] = {}

    def fake_render_compose_job(*args, **kwargs):
        captured_render.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 48,
            width=384,
            height=600,
            styling=RenderStyling(
                layout="image-above",
                font_family="mono",
                font_size=30,
                min_font_size=14,
                font_fit="largest-fitting",
                horizontal_padding_px=4,
                vertical_padding_px=5,
                line_spacing_px=2,
                max_length_mm=55.0,
                overflow_policy="report-only",
                break_long_words=False,
                mode="photo",
                conversion="dither",
            ),
            estimated_length_mm=73.02,
            max_length_mm=55.0,
            fits_length_limit=False,
        )

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
            estimated_length_mm=kwargs["estimated_length_mm"],
            max_length_mm=kwargs["max_length_mm"],
            fits_length_limit=kwargs["fits_length_limit"],
            styling=kwargs["styling"],
        )

    monkeypatch.setattr("paperang_cli.drivers.paperang_p1.render_compose_job", fake_render_compose_job)
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
    assert captured_render["min_font_size"] == 14
    assert captured_render["font_fit"] == "largest-fitting"
    assert captured_render["horizontal_padding_px"] == 4
    assert captured_render["vertical_padding_px"] == 5
    assert captured_render["line_spacing_px"] == 2
    assert captured_render["spacer_height_px"] == 20
    assert captured_render["max_length_mm"] == 55.0
    assert captured_render["overflow_policy"] == "report-only"
    assert captured_render["break_long_words"] is False
    assert captured_send["styling"]["layout"] == "image-above"
    assert captured_send["styling"]["font_fit"] == "largest-fitting"
    assert captured_send["styling"]["mode"] == "photo"
    assert captured_send["estimated_length_mm"] == 73.02
    assert captured_send["max_length_mm"] == 55.0
    assert captured_send["fits_length_limit"] is False
    assert result.styling["font_family"] == "mono"
