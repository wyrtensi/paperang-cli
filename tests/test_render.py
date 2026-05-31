from __future__ import annotations

from pathlib import Path

from PIL import Image

from paperang_cli.render import (
    feed_units_from_mm,
    render_composed_bitstream,
    render_image_bitstream,
    render_text_bitstream,
    resolve_image_conversion,
)


def test_feed_units_match_calibrated_p1_behavior():
    assert feed_units_from_mm(5.0) == 280


def test_render_text_bitstream_returns_bytes():
    payload = render_text_bitstream("hello from tests", printer_width=384, paragraph=True, font_size=24)

    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_render_image_bitstream_returns_bytes(tmp_path: Path):
    image_path = tmp_path / "sample.png"
    image = Image.new("RGB", (24, 24), "white")
    image.putpixel((12, 12), (0, 0, 0))
    image.save(image_path)

    payload = render_image_bitstream(image_path, printer_width=384, conversion="threshold")

    assert isinstance(payload, bytes)
    assert len(payload) > 0


def test_render_image_bitstream_supports_photo_dither(tmp_path: Path):
    image_path = tmp_path / "sample-photo.png"
    image = Image.linear_gradient("L").resize((48, 32)).convert("RGB")
    image.save(image_path)

    payload = render_image_bitstream(image_path, printer_width=384, conversion="dither")

    assert isinstance(payload, bytes)
    assert len(payload) > 0


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


def test_resolve_image_conversion_uses_mode_defaults():
    assert resolve_image_conversion(mode="sticker") == "threshold"
    assert resolve_image_conversion(mode="photo") == "dither"
    assert resolve_image_conversion(mode="photo", conversion="edge") == "edge"