from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from paperang_cli.protocol import image_data
from paperang_cli.render import (
    RenderStyling,
    RenderedBitstream,
    _render_text_canvas,
    feed_units_from_mm,
    render_compose_job,
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


def test_binary_text_canvas_contains_only_black_and_white_pixels():
    canvas = _render_text_canvas(
        "P2 crisp text",
        printer_width=576,
        font_size=32,
        paragraph=False,
        binary_text=True,
    )

    assert set(np.unique(np.array(canvas))).issubset({0, 255})


def test_render_text_bitstream_forwards_font_fit(monkeypatch):
    captured: dict[str, object] = {}

    def fake_render_text_job(*args, **kwargs):
        captured.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 48,
            width=384,
            height=10,
            styling=RenderStyling(font_fit="largest-fitting", min_font_size=12),
        )

    monkeypatch.setattr("paperang_cli.render.render_text_job", fake_render_text_job)

    payload = render_text_bitstream(
        "hello from tests",
        printer_width=384,
        paragraph=True,
        font_size=24,
        min_font_size=12,
        font_fit="largest-fitting",
    )

    assert isinstance(payload, bytes)
    assert captured["font_fit"] == "largest-fitting"
    assert captured["min_font_size"] == 12


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


def test_render_text_job_autofits_rotated_multiline_text(monkeypatch):
    text = "\n".join(["label"] * 20)

    def fake_render_text_canvas(*args, font_size, **kwargs):
        return Image.new("L", (10, font_size * 20), 255)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", fake_render_text_canvas)

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


def test_render_text_job_rotated_length_uses_printable_width_mm(monkeypatch):
    monkeypatch.setattr(
        "paperang_cli.render._render_text_canvas",
        lambda *args, **kwargs: Image.new("L", (192, 40), 255),
    )

    rendered = render_text_job(
        "rotated length",
        printer_width=384,
        paragraph=True,
        font_size=24,
        orientation="rotate-90-cw",
        max_length_mm=22.0,
        overflow_policy="error",
        advance_mm_per_px=0.1,
        printable_width_mm=44.0,
    )

    assert rendered.estimated_length_mm == pytest.approx(22.0)
    assert rendered.fits_length_limit is True


def test_render_text_job_rejects_unknown_font_family():
    with pytest.raises(ValueError, match="Unsupported font family"):
        render_text_job("hello", printer_width=384, font_family="comic-sans")


def test_wrap_text_breaks_long_words_when_enabled(monkeypatch):
    monkeypatch.setattr(
        image_data,
        "_text_size",
        lambda draw, text, font: (len(text) * 10, 10, (0, 0, len(text) * 10, 10)),
    )

    wrapped = image_data._wrap_text(object(), "ABCDE", object(), 25, break_long_words=True)

    assert wrapped == ["AB", "CD", "E"]


def test_wrap_text_keeps_long_words_when_disabled(monkeypatch):
    monkeypatch.setattr(
        image_data,
        "_text_size",
        lambda draw, text, font: (len(text) * 10, 10, (0, 0, len(text) * 10, 10)),
    )

    wrapped = image_data._wrap_text(object(), "ABCDE", object(), 25, break_long_words=False)

    assert wrapped == ["ABCDE"]


def test_load_text_font_fallback_preserves_requested_size(monkeypatch):
    monkeypatch.setattr(
        image_data,
        "FONT_CANDIDATES",
        {
            "sans": {"windows": [], "portable": ["missing-sans-font.ttf"]},
            "mono": {"windows": [], "portable": ["missing-mono-font.ttf"]},
            "serif": {"windows": [], "portable": ["missing-serif-font.ttf"]},
        },
    )

    small_font = image_data._load_text_font(8)
    large_font = image_data._load_text_font(24)
    draw = ImageDraw.Draw(Image.new("L", (1, 1), 255))

    assert image_data._text_size(draw, "SUPERCALIFRAGILISTICEXPIALIDOCIOUS", small_font)[0] < image_data._text_size(
        draw,
        "SUPERCALIFRAGILISTICEXPIALIDOCIOUS",
        large_font,
    )[0]


def test_render_text_job_shrinks_to_fit_max_length(monkeypatch):
    def fake_render_text_canvas(*args, font_size, **kwargs):
        return Image.new("L", (120, font_size * 4), 255)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", fake_render_text_canvas)

    rendered = render_text_job(
        "long text",
        printer_width=384,
        paragraph=True,
        font_size=32,
        min_font_size=10,
        overflow_policy="shrink-to-fit",
        max_length_mm=4.0,
        advance_mm_per_px=0.1,
    )

    assert rendered.styling.font_size == 10
    assert rendered.fits_length_limit is True
    assert rendered.estimated_length_mm == pytest.approx(4.0)


def test_render_text_job_rejects_max_length_overflow_when_policy_is_error(monkeypatch):
    def fake_render_text_canvas(*args, font_size, **kwargs):
        return Image.new("L", (120, font_size * 4), 255)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", fake_render_text_canvas)

    with pytest.raises(ValueError, match="too long"):
        render_text_job(
            "long text",
            printer_width=384,
            paragraph=True,
            font_size=32,
            overflow_policy="error",
            max_length_mm=4.0,
            advance_mm_per_px=0.1,
        )


def test_render_text_job_finds_largest_fitting_font_without_explicit_font_size(monkeypatch):
    def fake_render_text_canvas(*args, font_size, **kwargs):
        return Image.new("L", (120, font_size * 4), 255)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", fake_render_text_canvas)

    rendered = render_text_job(
        "long text",
        printer_width=384,
        paragraph=True,
        font_size=None,
        min_font_size=10,
        font_fit="largest-fitting",
        max_length_mm=6.0,
        advance_mm_per_px=0.1,
    )

    assert rendered.styling.font_fit == "largest-fitting"
    assert rendered.styling.font_size == 15
    assert rendered.fits_length_limit is True


def test_render_text_job_rejects_largest_fitting_without_length_or_rotation():
    with pytest.raises(ValueError, match="requires max_length_mm or rotated orientation"):
        render_text_job(
            "plain note",
            printer_width=384,
            paragraph=True,
            font_fit="largest-fitting",
            orientation="normal",
        )


def test_render_text_job_reports_resolved_min_font_size(monkeypatch):
    monkeypatch.setattr("paperang_cli.render._render_text_canvas", lambda *args, **kwargs: Image.new("L", (120, 40), 255))

    rendered = render_text_job(
        "largest fit label",
        printer_width=384,
        paragraph=True,
        font_size=24,
        min_font_size=None,
        font_fit="largest-fitting",
        max_length_mm=20.0,
        advance_mm_per_px=0.1,
    )

    assert rendered.styling.min_font_size == 8


def test_render_text_job_largest_fitting_shrinks_single_long_word_instead_of_clipping():
    rendered = render_text_job(
        "SUPERCALIFRAGILISTICEXPIALIDOCIOUS",
        printer_width=128,
        paragraph=True,
        font_size=None,
        min_font_size=4,
        font_fit="largest-fitting",
        break_long_words=False,
        max_length_mm=200.0,
    )

    assert rendered.styling.font_fit == "largest-fitting"
    assert rendered.styling.break_long_words is False
    assert rendered.styling.font_size < 96
    assert rendered.styling.autofit_applied is True


def test_render_compose_job_largest_fitting_shrinks_single_long_word_instead_of_clipping(tmp_path: Path):
    image_path = tmp_path / "sample-compose-wide-word.png"
    Image.new("RGB", (32, 16), "white").save(image_path)

    rendered = render_compose_job(
        "SUPERCALIFRAGILISTICEXPIALIDOCIOUS",
        image_path,
        printer_width=128,
        font_size=None,
        min_font_size=4,
        font_fit="largest-fitting",
        break_long_words=False,
        max_length_mm=200.0,
    )

    assert rendered.styling.font_fit == "largest-fitting"
    assert rendered.styling.break_long_words is False
    assert rendered.styling.font_size < 96


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


def test_render_image_job_fits_within_max_length(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "sample-fit-length.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr(
        "paperang_cli.render._render_image_binary",
        lambda *args, **kwargs: np.ones((300, 384), dtype=int),
    )

    rendered = render_image_job(
        image_path,
        printer_width=384,
        conversion="threshold",
        max_length_mm=20.0,
        fit_mode="fit-within-length",
        advance_mm_per_px=0.1,
    )

    assert rendered.height == 200
    assert rendered.fits_length_limit is True
    assert rendered.estimated_length_mm == pytest.approx(20.0)


def test_render_image_job_rotated_length_uses_printable_width_mm(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "sample-fit-length-rotated.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr(
        "paperang_cli.render._render_image_binary",
        lambda *args, **kwargs: np.ones((250, 384), dtype=int),
    )

    rendered = render_image_job(
        image_path,
        printer_width=384,
        conversion="threshold",
        orientation="rotate-90-cw",
        max_length_mm=22.0,
        fit_mode="fit-within-length",
        advance_mm_per_px=0.1,
        printable_width_mm=44.0,
    )

    assert rendered.height == 192
    assert rendered.fits_length_limit is True
    assert rendered.estimated_length_mm == pytest.approx(22.0)


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


def test_render_composed_bitstream_forwards_font_fit_and_min_font_size(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "sample-compose-forward.png"
    Image.new("RGB", (32, 24), "white").save(image_path)
    captured: dict[str, object] = {}

    def fake_render_compose_job(*args, **kwargs):
        captured.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 48,
            width=384,
            height=10,
            styling=RenderStyling(font_fit="largest-fitting", min_font_size=14),
        )

    monkeypatch.setattr("paperang_cli.render.render_compose_job", fake_render_compose_job)

    payload = render_composed_bitstream(
        "label title",
        image_path,
        printer_width=384,
        font_size=28,
        min_font_size=14,
        font_fit="largest-fitting",
        max_length_mm=55.0,
        conversion="threshold",
        layout="text-above",
    )

    assert isinstance(payload, bytes)
    assert captured["font_fit"] == "largest-fitting"
    assert captured["min_font_size"] == 14
    assert captured["max_length_mm"] == 55.0


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


def test_render_compose_job_reports_length_overflow_when_policy_is_report_only(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "compose-report-only.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", lambda *args, **kwargs: Image.new("L", (384, 60), 255))
    monkeypatch.setattr("paperang_cli.render._render_image_binary", lambda *args, **kwargs: np.ones((80, 384), dtype=int))

    rendered = render_compose_job(
        "compose label",
        image_path,
        printer_width=384,
        spacer_height_px=10,
        max_length_mm=10.0,
        overflow_policy="report-only",
        advance_mm_per_px=0.1,
    )

    assert rendered.height == 150
    assert rendered.fits_length_limit is False
    assert rendered.estimated_length_mm == pytest.approx(15.0)


def test_render_compose_job_rejects_length_overflow_when_policy_is_error(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "compose-error.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", lambda *args, **kwargs: Image.new("L", (384, 60), 255))
    monkeypatch.setattr("paperang_cli.render._render_image_binary", lambda *args, **kwargs: np.ones((80, 384), dtype=int))

    with pytest.raises(ValueError, match="too long"):
        render_compose_job(
            "compose label",
            image_path,
            printer_width=384,
            spacer_height_px=10,
            max_length_mm=10.0,
            overflow_policy="error",
            advance_mm_per_px=0.1,
        )


def test_render_compose_job_finds_largest_fitting_font_without_explicit_font_size(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "compose-largest-fit.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr(
        "paperang_cli.render._render_text_canvas",
        lambda *args, font_size, **kwargs: Image.new("L", (384, font_size * 5), 255),
    )
    monkeypatch.setattr("paperang_cli.render._render_image_binary", lambda *args, **kwargs: np.ones((80, 384), dtype=int))

    rendered = render_compose_job(
        "compose label",
        image_path,
        printer_width=384,
        font_size=None,
        min_font_size=10,
        font_fit="largest-fitting",
        spacer_height_px=10,
        max_length_mm=20.0,
        advance_mm_per_px=0.1,
    )

    assert rendered.styling.font_fit == "largest-fitting"
    assert rendered.styling.font_size == 22
    assert rendered.fits_length_limit is True


def test_render_compose_job_reports_resolved_styling_defaults(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "compose-resolved-style.png"
    Image.new("RGB", (8, 8), "white").save(image_path)

    monkeypatch.setattr("paperang_cli.render._render_text_canvas", lambda *args, **kwargs: Image.new("L", (200, 60), 255))
    monkeypatch.setattr("paperang_cli.render._render_image_binary", lambda *args, **kwargs: np.ones((80, 384), dtype=int))

    rendered = render_compose_job(
        "compose label",
        image_path,
        printer_width=384,
        font_size=24,
        min_font_size=None,
        font_fit="largest-fitting",
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        spacer_height_px=None,
        max_length_mm=40.0,
        advance_mm_per_px=0.1,
    )

    assert rendered.styling.min_font_size == 8
    assert rendered.styling.horizontal_padding_px == 12
    assert rendered.styling.vertical_padding_px == 10
    assert rendered.styling.line_spacing_px == 6
    assert rendered.styling.to_dict()["spacer_height_px"] == 12


def test_resolve_image_conversion_uses_mode_defaults():
    assert resolve_image_conversion(mode="sticker") == "threshold"
    assert resolve_image_conversion(mode="photo") == "dither"
    assert resolve_image_conversion(mode="photo", conversion="edge") == "edge"
