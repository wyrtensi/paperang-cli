"""Rendering and feed helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from paperang_cli.protocol import image_data

DEFAULT_TEXT_FONT_SIZE = 36
DEFAULT_PARAGRAPH_FONT_SIZE = 24
DEFAULT_COMPOSE_FONT_SIZE = 28
FEED_UNITS_PER_MM = 56
MIN_AUTOFIT_FONT_SIZE = 8
IMAGE_MODE_TO_CONVERSION = {
    "sticker": "threshold",
    "photo": "dither",
}
COMPOSE_LAYOUTS = {"text-above", "image-above"}
ORIENTATION_ROTATIONS = {
    "normal": None,
    "rotate-90-cw": 270,
    "rotate-90-ccw": 90,
}


@dataclass(slots=True)
class RenderStyling:
    orientation: str = "normal"
    font_family: str | None = None
    font_size: int | None = None
    min_font_size: int | None = None
    autofit: bool | None = None
    autofit_applied: bool = False
    horizontal_padding_px: int | None = None
    vertical_padding_px: int | None = None
    line_spacing_px: int | None = None
    mode: str | None = None
    conversion: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return asdict(self)


@dataclass(slots=True)
class RenderedBitstream:
    bitstream: bytes
    width: int
    height: int
    styling: RenderStyling


def resolve_image_conversion(*, mode: str | None = None, conversion: str | None = None) -> str:
    if conversion:
        return conversion.lower()

    resolved_mode = (mode or "sticker").lower()
    try:
        return IMAGE_MODE_TO_CONVERSION[resolved_mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported image mode: {resolved_mode}") from exc


def _resolve_font_family(font_family: str) -> str:
    resolved_font_family = font_family.strip().lower()
    if resolved_font_family not in image_data.FONT_CANDIDATES:
        raise ValueError(f"Unsupported font family: {font_family}")
    return resolved_font_family


def _resample_lanczos():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def _floyd_steinberg_dither():
    if hasattr(Image, "Dither"):
        return Image.Dither.FLOYDSTEINBERG
    return Image.FLOYDSTEINBERG


def _rotate_image(image: Image.Image, orientation: str) -> Image.Image:
    if orientation == "normal":
        return image.copy()

    rotation = ORIENTATION_ROTATIONS.get(orientation)
    if rotation is None:
        raise ValueError(f"Unsupported orientation: {orientation}")
    return image.rotate(rotation, expand=True)


def _render_dithered_image_binary(
    image_path: str | Path,
    *,
    printer_width: int,
    orientation: str = "normal",
) -> np.ndarray:
    with Image.open(image_path) as source_image:
        image = _rotate_image(source_image, orientation)
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
    font_family: str = "sans",
    horizontal_padding_px: int | None = None,
    vertical_padding_px: int | None = None,
    line_spacing_px: int | None = None,
    wrap_to_printer_width: bool = True,
) -> Image.Image:
    horizontal_padding = horizontal_padding_px if horizontal_padding_px is not None else (12 if paragraph else 16)
    vertical_padding = vertical_padding_px if vertical_padding_px is not None else (10 if paragraph else 12)
    message = text if text else " "

    font = image_data._load_text_font(font_size, font_family=font_family)
    probe_image = Image.new("L", (1, 1), 255)
    probe_draw = ImageDraw.Draw(probe_image)
    if wrap_to_printer_width:
        max_text_width = max(1, printer_width - horizontal_padding * 2)
        lines = image_data._wrap_text(probe_draw, message, font, max_text_width)
    else:
        lines = message.splitlines() or [message]

    line_metrics = [image_data._text_size(probe_draw, line, font) for line in lines]
    text_width = max(metric[0] for metric in line_metrics)
    line_height = max(metric[1] for metric in line_metrics)
    line_spacing = line_spacing_px if line_spacing_px is not None else max(6, font_size // 4)
    text_height = line_height * len(lines) + line_spacing * max(0, len(lines) - 1)

    image_width = max(text_width + horizontal_padding * 2, 1)
    if wrap_to_printer_width:
        image_width = min(printer_width, image_width)

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

    return text_image


def _render_image_binary(
    image_path: str | Path,
    *,
    printer_width: int,
    conversion: str,
    orientation: str = "normal",
) -> np.ndarray:
    if conversion == "dither":
        return _render_dithered_image_binary(
            image_path,
            printer_width=printer_width,
            orientation=orientation,
        )

    with Image.open(image_path) as source_image:
        image = _rotate_image(source_image, orientation)
        pixel_data = np.array(image.convert("RGB"))

    return image_data.im2binimage(
        pixel_data,
        conversion=conversion,
        printer_width=printer_width,
    )


def _binary_image_to_canvas(binary_image: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(binary_image == 1, 0, 255).astype(np.uint8), mode="L")


def _finalize_canvas(canvas: Image.Image, *, printer_width: int, orientation: str) -> Image.Image:
    if orientation == "normal":
        oriented = canvas
    else:
        rotation = ORIENTATION_ROTATIONS.get(orientation)
        if rotation is None:
            raise ValueError(f"Unsupported orientation: {orientation}")
        oriented = canvas.rotate(rotation, expand=True, fillcolor=255)

    if oriented.width > printer_width:
        raise ValueError(
            f"Rendered content is too wide for printer width {printer_width} after applying orientation {orientation}"
        )

    final_canvas = Image.new("L", (printer_width, oriented.height), 255)
    offset_x = max(0, (printer_width - oriented.width) // 2)
    final_canvas.paste(oriented, (offset_x, 0))
    return final_canvas


def _rendered_bitstream(canvas: Image.Image, *, styling: RenderStyling) -> RenderedBitstream:
    binary_image = (np.array(canvas) < 128).astype(int)
    return RenderedBitstream(
        bitstream=image_data.binimage2bitstream(binary_image),
        width=canvas.width,
        height=canvas.height,
        styling=styling,
    )


def render_text_job(
    text: str,
    *,
    printer_width: int = 384,
    paragraph: bool = False,
    font_size: int | None = None,
    font_family: str = "sans",
    min_font_size: int | None = None,
    autofit: bool = False,
    orientation: str = "normal",
    horizontal_padding_px: int | None = None,
    vertical_padding_px: int | None = None,
    line_spacing_px: int | None = None,
) -> RenderedBitstream:
    resolved_font_size = font_size or (DEFAULT_PARAGRAPH_FONT_SIZE if paragraph else DEFAULT_TEXT_FONT_SIZE)
    resolved_min_font_size = min_font_size if min_font_size is not None else MIN_AUTOFIT_FONT_SIZE
    resolved_font_family = _resolve_font_family(font_family)
    if resolved_min_font_size > resolved_font_size:
        raise ValueError("min_font_size must be less than or equal to font_size")

    font_sizes = [resolved_font_size]
    if autofit and orientation != "normal":
        font_sizes = list(range(resolved_font_size, resolved_min_font_size - 1, -1))

    for candidate_size in font_sizes:
        text_image = _render_text_canvas(
            text,
            printer_width=printer_width,
            font_size=candidate_size,
            paragraph=paragraph,
            font_family=resolved_font_family,
            horizontal_padding_px=horizontal_padding_px,
            vertical_padding_px=vertical_padding_px,
            line_spacing_px=line_spacing_px,
            wrap_to_printer_width=orientation == "normal",
        )
        try:
            final_canvas = _finalize_canvas(text_image, printer_width=printer_width, orientation=orientation)
        except ValueError:
            if candidate_size != font_sizes[-1]:
                continue
            raise

        resolved_horizontal_padding = horizontal_padding_px if horizontal_padding_px is not None else (12 if paragraph else 16)
        resolved_vertical_padding = vertical_padding_px if vertical_padding_px is not None else (10 if paragraph else 12)
        resolved_line_spacing = line_spacing_px if line_spacing_px is not None else max(6, candidate_size // 4)
        return _rendered_bitstream(
            final_canvas,
            styling=RenderStyling(
                orientation=orientation,
                font_family=resolved_font_family,
                font_size=candidate_size,
                min_font_size=min_font_size,
                autofit=autofit,
                autofit_applied=autofit and candidate_size != resolved_font_size,
                horizontal_padding_px=resolved_horizontal_padding,
                vertical_padding_px=resolved_vertical_padding,
                line_spacing_px=resolved_line_spacing,
            ),
        )

    raise ValueError(
        f"Rendered content is too wide for printer width {printer_width} even after autofit down to {resolved_min_font_size}"
    )


def render_image_job(
    image_path: str | Path,
    *,
    printer_width: int = 384,
    conversion: str = "threshold",
    orientation: str = "normal",
    mode: str | None = None,
) -> RenderedBitstream:
    binary_image = _render_image_binary(
        image_path,
        printer_width=printer_width,
        conversion=conversion,
        orientation=orientation,
    )
    canvas = _binary_image_to_canvas(binary_image)
    if canvas.width != printer_width:
        raise ValueError(f"Rendered image width {canvas.width} does not match printer width {printer_width}")

    return _rendered_bitstream(
        canvas,
        styling=RenderStyling(
            orientation=orientation,
            mode=mode,
            conversion=conversion,
        ),
    )


def feed_units_from_mm(feed_mm: float) -> int:
    return max(0, int(round(feed_mm * FEED_UNITS_PER_MM)))


def render_text_bitstream(
    text: str,
    *,
    printer_width: int = 384,
    paragraph: bool = False,
    font_size: int | None = None,
    font_family: str = "sans",
    min_font_size: int | None = None,
    autofit: bool = False,
    orientation: str = "normal",
    horizontal_padding_px: int | None = None,
    vertical_padding_px: int | None = None,
    line_spacing_px: int | None = None,
) -> bytes:
    return render_text_job(
        text,
        printer_width=printer_width,
        paragraph=paragraph,
        font_size=font_size,
        font_family=font_family,
        min_font_size=min_font_size,
        autofit=autofit,
        orientation=orientation,
        horizontal_padding_px=horizontal_padding_px,
        vertical_padding_px=vertical_padding_px,
        line_spacing_px=line_spacing_px,
    ).bitstream


def render_image_bitstream(
    image_path: str | Path,
    *,
    printer_width: int = 384,
    conversion: str = "threshold",
    orientation: str = "normal",
) -> bytes:
    return render_image_job(
        image_path,
        printer_width=printer_width,
        conversion=conversion,
        orientation=orientation,
    ).bitstream


def render_composed_bitstream(
    text: str,
    image_path: str | Path,
    *,
    printer_width: int = 384,
    font_size: int | None = None,
    font_family: str = "sans",
    horizontal_padding_px: int | None = None,
    vertical_padding_px: int | None = None,
    line_spacing_px: int | None = None,
    spacer_height_px: int | None = None,
    conversion: str = "threshold",
    layout: str = "text-above",
) -> bytes:
    resolved_layout = layout.lower()
    if resolved_layout not in COMPOSE_LAYOUTS:
        raise ValueError(f"Unsupported compose layout: {layout}")

    resolved_font_size = font_size or DEFAULT_COMPOSE_FONT_SIZE
    resolved_font_family = _resolve_font_family(font_family)
    resolved_spacer_height = spacer_height_px if spacer_height_px is not None else 12
    if resolved_spacer_height < 0:
        raise ValueError("spacer_height_px must be zero or greater")

    text_canvas = _finalize_canvas(
        _render_text_canvas(
            text,
            printer_width=printer_width,
            font_size=resolved_font_size,
            paragraph=True,
            font_family=resolved_font_family,
            horizontal_padding_px=horizontal_padding_px,
            vertical_padding_px=vertical_padding_px,
            line_spacing_px=line_spacing_px,
        ),
        printer_width=printer_width,
        orientation="normal",
    )
    image_canvas = _binary_image_to_canvas(
        _render_image_binary(
            image_path,
            printer_width=printer_width,
            conversion=conversion,
        )
    )
    spacer = Image.new("L", (printer_width, resolved_spacer_height), 255)

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
