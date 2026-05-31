"""Rendering and feed helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from paperang_cli.protocol import image_data

DEFAULT_TEXT_FONT_SIZE = 36
DEFAULT_PARAGRAPH_FONT_SIZE = 24
DEFAULT_COMPOSE_FONT_SIZE = 28
FEED_UNITS_PER_MM = 56
IMAGE_MODE_TO_CONVERSION = {
    "sticker": "threshold",
    "photo": "dither",
}
COMPOSE_LAYOUTS = {"text-above", "image-above"}


def resolve_image_conversion(*, mode: str | None = None, conversion: str | None = None) -> str:
    if conversion:
        return conversion.lower()

    resolved_mode = (mode or "sticker").lower()
    try:
        return IMAGE_MODE_TO_CONVERSION[resolved_mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported image mode: {resolved_mode}") from exc


def _resample_lanczos():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def _floyd_steinberg_dither():
    if hasattr(Image, "Dither"):
        return Image.Dither.FLOYDSTEINBERG
    return Image.FLOYDSTEINBERG


def _render_dithered_image_bitstream(image_path: str | Path, *, printer_width: int) -> bytes:
    binary_image = _render_dithered_image_binary(image_path, printer_width=printer_width)
    return image_data.binimage2bitstream(binary_image)


def _render_dithered_image_binary(image_path: str | Path, *, printer_width: int) -> np.ndarray:
    with Image.open(image_path) as image:
        grayscale = ImageOps.autocontrast(image.convert("L"))
        height = max(1, round(printer_width / grayscale.width * grayscale.height))
        resized = grayscale.resize((printer_width, height), _resample_lanczos())
        dithered = resized.convert("1", dither=_floyd_steinberg_dither())

    return (np.array(dithered, dtype=np.uint8) == 0).astype(int)


def _render_text_canvas(
    text: str,
    *,
    printer_width: int,
    font_size: int,
    paragraph: bool,
) -> Image.Image:
    horizontal_padding = 12 if paragraph else 16
    vertical_padding = 10 if paragraph else 12
    message = text if text else " "

    font = image_data._load_text_font(font_size)
    probe_image = Image.new("L", (1, 1), 255)
    probe_draw = ImageDraw.Draw(probe_image)
    max_text_width = max(1, printer_width - horizontal_padding * 2)
    lines = image_data._wrap_text(probe_draw, message, font, max_text_width)

    line_metrics = [image_data._text_size(probe_draw, line, font) for line in lines]
    text_width = max(metric[0] for metric in line_metrics)
    line_height = max(metric[1] for metric in line_metrics)
    line_spacing = max(6, font_size // 4)
    text_height = line_height * len(lines) + line_spacing * max(0, len(lines) - 1)

    image_width = min(printer_width, max(text_width + horizontal_padding * 2, 1))
    image_height = max(text_height + vertical_padding * 2, 1)
    text_image = Image.new("L", (image_width, image_height), 255)
    text_draw = ImageDraw.Draw(text_image)
    current_y = vertical_padding
    for line, (_, _, bbox) in zip(lines, line_metrics):
        text_draw.text(
            (horizontal_padding - bbox[0], current_y - bbox[1]),
            line,
            fill=0,
            font=font,
        )
        current_y += line_height + line_spacing

    canvas = Image.new("L", (printer_width, text_image.height), 255)
    offset_x = max(0, (printer_width - text_image.width) // 2)
    canvas.paste(text_image, (offset_x, 0))
    return canvas


def _render_image_binary(
    image_path: str | Path,
    *,
    printer_width: int,
    conversion: str,
) -> np.ndarray:
    if conversion == "dither":
        return _render_dithered_image_binary(image_path, printer_width=printer_width)

    with Image.open(image_path) as image:
        pixel_data = np.array(image.convert("RGB"))

    return image_data.im2binimage(
        pixel_data,
        conversion=conversion,
        printer_width=printer_width,
    )


def _binary_image_to_canvas(binary_image: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(binary_image == 1, 0, 255).astype(np.uint8), mode="L")


def feed_units_from_mm(feed_mm: float) -> int:
    return max(0, int(round(feed_mm * FEED_UNITS_PER_MM)))


def render_text_bitstream(
    text: str,
    *,
    printer_width: int = 384,
    paragraph: bool = False,
    font_size: int | None = None,
) -> bytes:
    resolved_font_size = font_size
    if resolved_font_size is None:
        resolved_font_size = DEFAULT_PARAGRAPH_FONT_SIZE if paragraph else DEFAULT_TEXT_FONT_SIZE

    canvas = _render_text_canvas(
        text,
        printer_width=printer_width,
        font_size=resolved_font_size,
        paragraph=paragraph,
    )
    binary_image = (np.array(canvas) < 128).astype(int)
    return image_data.binimage2bitstream(binary_image)


def render_image_bitstream(
    image_path: str | Path,
    *,
    printer_width: int = 384,
    conversion: str = "threshold",
) -> bytes:
    binary_image = _render_image_binary(
        image_path,
        printer_width=printer_width,
        conversion=conversion,
    )
    return image_data.binimage2bitstream(binary_image)


def render_composed_bitstream(
    text: str,
    image_path: str | Path,
    *,
    printer_width: int = 384,
    font_size: int | None = None,
    conversion: str = "threshold",
    layout: str = "text-above",
) -> bytes:
    resolved_layout = layout.lower()
    if resolved_layout not in COMPOSE_LAYOUTS:
        raise ValueError(f"Unsupported compose layout: {layout}")

    resolved_font_size = font_size or DEFAULT_COMPOSE_FONT_SIZE
    text_canvas = _render_text_canvas(
        text,
        printer_width=printer_width,
        font_size=resolved_font_size,
        paragraph=True,
    )
    image_canvas = _binary_image_to_canvas(
        _render_image_binary(
            image_path,
            printer_width=printer_width,
            conversion=conversion,
        )
    )
    spacer = Image.new("L", (printer_width, 12), 255)

    segments = [text_canvas, spacer, image_canvas]
    if resolved_layout == "image-above":
        segments = [image_canvas, spacer, text_canvas]

    canvas_height = sum(segment.height for segment in segments)
    canvas = Image.new("L", (printer_width, canvas_height), 255)
    current_y = 0
    for segment in segments:
        canvas.paste(segment, (0, current_y))
        current_y += segment.height

    binary_image = (np.array(canvas) < 128).astype(int)
    return image_data.binimage2bitstream(binary_image)