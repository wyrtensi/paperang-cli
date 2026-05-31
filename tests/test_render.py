from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from paperang_cli.render import (
    feed_units_from_mm,
    render_composed_bitstream,
    render_image_bitstream,
    render_image_job,
    render_text_bitstream,
    render_text_job,
    resolve_image_conversion,
)


def test_feed_units_match_calibrated_p1_behavior():
    assert feed_units_from_mm(5.0) == 280


def test_render_text_bitstream_returns_bytes():
    payload = render_text_bitstream("hello from tests", printer_width=384, paragraph=True, font_size=24)

    assert isinstance(payload, bytes)
    assert len(payload) > 0
    assert (len(payload) * 8) % 384 == 0


def test_render_text_job_rotates_label_and_reports_styling():
    rendered = render_text_job(
        "hello from rotated label",
        printer_width=384,
        font_size=36,
        font_family="mono",
        orientation="rotate-90-cw",
    )

    assert rendered.width == 384
    assert rendered.height > 0
    assert rendered.styling.orientation == "rotate-90-cw"
    assert rendered.styling.font_family == "mono"
    assert rendered.styling.font_size == 36


def test_render_text_job_autofits_rotated_multiline_text():
    text = "\n".join(["label"] * 20)

    rendered = render_text_job(
        text,
        printer_width=384,
        paragraph=True,
        font_size=32,
        min_font_size=10,
        autofit=True,
        orientation="rotate-90-cw",
    )

    assert rendered.width == 384
    assert rendered.styling.autofit_applied is True
    assert rendered.styling.font_size < 32


def test_render_text_job_rejects_rotated_multiline_text_without_autofit():
    text = "\n".join(["label"] * 30)

    with pytest.raises(ValueError, match="too wide"):
        render_text_job(
            text,
            printer_width=384,
            paragraph=True,
            font_size=32,
            orientation="rotate-90-cw",
        )


def test_render_text_job_rejects_unknown_font_family():
    with pytest.raises(ValueError, match="Unsupported font family"):
        render_text_job("hello", printer_width=384, font_family="comic-sans")


def test_render_image_bitstream_returns_bytes(tmp_path: Path):
    image_path = tmp_path / "sample.png"
    image = Image.new("RGB", (24, 24), "white")
    image.putpixel((12, 12), (0, 0, 0))
    image.save(image_path)

    payload = render_image_bitstream(image_path, printer_width=384, conversion="threshold")

    assert isinstance(payload, bytes)
    assert len(payload) > 0
    assert (len(payload) * 8) % 384 == 0


def test_render_image_bitstream_supports_photo_dither(tmp_path: Path):
    image_path = tmp_path / "sample-photo.png"
    image = Image.linear_gradient("L").resize((48, 32)).convert("RGB")
    image.save(image_path)

    payload = render_image_bitstream(image_path, printer_width=384, conversion="dither")

    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_render_image_job_rotates_source_before_conversion(tmp_path: Path):
    image_path = tmp_path / "sample-rotated.png"
    image = Image.new("RGB", (64, 20), "white")
    image.putpixel((60, 10), (0, 0, 0))
    image.save(image_path)

    rendered = render_image_job(
        image_path,
        printer_width=384,
        conversion="threshold",
        orientation="rotate-90-ccw",
        mode="sticker",
    )

    assert rendered.width == 384
    assert rendered.height > 0
    assert rendered.styling.orientation == "rotate-90-ccw"
    assert rendered.styling.conversion == "threshold"
    assert rendered.styling.mode == "sticker"


def test_render_composed_bitstream_returns_bytes(tmp_path: Path):
    image_path = tmp_path / "sample-compose.png"
    image = Image.new("RGB", (32, 24), "white")
    image.putpixel((4, 4), (0, 0, 0))
    image.save(image_path)

    payload = render_composed_bitstream(
        "label title",
        image_path,
        printer_width=384,
        font_size=28,
        conversion="threshold",
        layout="text-above",
    )

    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_render_composed_bitstream_accepts_ordinary_compose_styling(tmp_path: Path):
    image_path = tmp_path / "sample-styled-compose.png"
    Image.new("RGB", (32, 24), "white").save(image_path)

    payload = render_composed_bitstream(
        "styled label",
        image_path,
        printer_width=384,
        font_size=28,
        font_family="mono",
        horizontal_padding_px=4,
        vertical_padding_px=5,
        line_spacing_px=2,
        spacer_height_px=20,
    )

    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_resolve_image_conversion_uses_mode_defaults():
    assert resolve_image_conversion(mode="sticker") == "threshold"
    assert resolve_image_conversion(mode="photo") == "dither"
    assert resolve_image_conversion(mode="photo", conversion="edge") == "edge"
