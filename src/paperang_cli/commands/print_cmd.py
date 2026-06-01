"""Printing commands."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import click

from paperang_cli.drivers import registry
from paperang_cli.errors import ConfigError
from paperang_cli.output import cli_error_boundary, emit_result
from paperang_cli.presets import get_builtin_presets
from paperang_cli.render import resolve_image_conversion
from paperang_cli.style_resolution import resolve_operation_style


@click.group("print")
def print_group() -> None:
    """Print text, print images, or run the built-in self-test."""


@print_group.command("text")
@click.argument("text")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for this print job.")
@click.option(
    "--font-family",
    type=click.Choice(["sans", "mono", "serif"], case_sensitive=False),
    default=None,
    help="Override the generic system font family for this print job.",
)
@click.option("--min-font-size", type=int, default=None, help="Minimum font size to use when autofit is enabled.")
@click.option(
    "--font-fit",
    type=click.Choice(["manual", "largest-fitting"], case_sensitive=False),
    default=None,
    help="How to choose the text font size. largest-fitting starts from a large ceiling and shrinks to the biggest size that fits.",
)
@click.option("--autofit/--no-autofit", default=None, help="Enable or disable rotated-label font autofit.")
@click.option(
    "--orientation",
    type=click.Choice(["normal", "rotate-90-cw", "rotate-90-ccw"], case_sensitive=False),
    default=None,
    help="Render orientation for the print job.",
)
@click.option("--style-json", type=str, default=None, help="Path to a JSON style payload, or - to read JSON from stdin.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_text_command(
    ctx: click.Context,
    text: str,
    address: str | None,
    font_size: int | None,
    font_family: str | None,
    min_font_size: int | None,
    font_fit: str | None,
    autofit: bool | None,
    orientation: str | None,
    style_json: str | None,
    feed_mm: float | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print a single line or short block of text."""
    _run_print(
        ctx,
        text=text,
        paragraph=False,
        address=address,
        font_size=font_size,
        font_family=font_family.lower() if font_family else None,
        min_font_size=min_font_size,
        font_fit=font_fit.lower() if font_fit else None,
        autofit=autofit,
        orientation=orientation.lower() if orientation else None,
        style_json=style_json,
        feed_mm=feed_mm,
        allow_paper_use=allow_paper_use,
        dry_run=dry_run,
    )


@print_group.command("paragraph")
@click.argument("text")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for this print job.")
@click.option(
    "--font-family",
    type=click.Choice(["sans", "mono", "serif"], case_sensitive=False),
    default=None,
    help="Override the generic system font family for this print job.",
)
@click.option("--min-font-size", type=int, default=None, help="Minimum font size to use when autofit is enabled.")
@click.option(
    "--font-fit",
    type=click.Choice(["manual", "largest-fitting"], case_sensitive=False),
    default=None,
    help="How to choose the text font size. largest-fitting starts from a large ceiling and shrinks to the biggest size that fits.",
)
@click.option("--autofit/--no-autofit", default=None, help="Enable or disable rotated-label font autofit.")
@click.option(
    "--orientation",
    type=click.Choice(["normal", "rotate-90-cw", "rotate-90-ccw"], case_sensitive=False),
    default=None,
    help="Render orientation for this print job.",
)
@click.option("--style-json", type=str, default=None, help="Path to a JSON style payload, or - to read JSON from stdin.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_paragraph_command(
    ctx: click.Context,
    text: str,
    address: str | None,
    font_size: int | None,
    font_family: str | None,
    min_font_size: int | None,
    font_fit: str | None,
    autofit: bool | None,
    orientation: str | None,
    style_json: str | None,
    feed_mm: float | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print a wrapped paragraph using the paragraph rendering mode."""
    _run_print(
        ctx,
        text=text,
        paragraph=True,
        address=address,
        font_size=font_size,
        font_family=font_family.lower() if font_family else None,
        min_font_size=min_font_size,
        font_fit=font_fit.lower() if font_fit else None,
        autofit=autofit,
        orientation=orientation.lower() if orientation else None,
        style_json=style_json,
        feed_mm=feed_mm,
        allow_paper_use=allow_paper_use,
        dry_run=dry_run,
    )


def _run_print(
    ctx: click.Context,
    *,
    text: str,
    paragraph: bool,
    address: str | None,
    font_size: int | None,
    font_family: str | None,
    min_font_size: int | None,
    font_fit: str | None,
    autofit: bool | None,
    orientation: str | None,
    style_json: str | None,
    feed_mm: float | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    with cli_error_boundary(ctx):
        settings = ctx.obj["settings"]
        driver = registry.get_driver(ctx.obj["settings"])
        resolved_style = None
        if style_json is not None:
            resolved_style = _resolve_style_json(
                operation="paragraph" if paragraph else "text",
                print_defaults=asdict(settings.print_defaults.paragraph if paragraph else settings.print_defaults.text),
                presets=_combined_presets(settings),
                style_json_payload=_load_style_json_payload(style_json),
                cli_overrides={
                    "font_size": font_size,
                    "font_family": font_family,
                    "min_font_size": min_font_size,
                    "font_fit": font_fit,
                    "autofit": autofit,
                    "orientation": orientation,
                },
            )
        result = driver.print_text(
            text,
            paragraph=paragraph,
            font_size=font_size,
            font_family=font_family,
            min_font_size=min_font_size,
            font_fit=font_fit,
            autofit=autofit,
            orientation=orientation,
            horizontal_padding_px=None,
            vertical_padding_px=None,
            line_spacing_px=None,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            resolved_style=resolved_style,
            address=address,
        )
        _emit_print_result(ctx, result)


@print_group.command("image")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option(
    "--orientation",
    type=click.Choice(["normal", "rotate-90-cw", "rotate-90-ccw"], case_sensitive=False),
    default=None,
    help="Render orientation for the image print.",
)
@click.option("--style-json", type=str, default=None, help="Path to a JSON style payload, or - to read JSON from stdin.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option(
    "--mode",
    type=click.Choice(["sticker", "photo"], case_sensitive=False),
    default=None,
    help="High-level image preset. Sticker uses hard contrast, while photo uses dithering.",
)
@click.option(
    "--conversion",
    type=click.Choice(["threshold", "edge", "dither"], case_sensitive=False),
    default=None,
    help="Optional low-level conversion override. When provided, it takes precedence over --mode.",
)
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming image print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_image_command(
    ctx: click.Context,
    image_path: Path,
    address: str | None,
    orientation: str | None,
    style_json: str | None,
    feed_mm: float | None,
    mode: str | None,
    conversion: str | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print a local image file after converting it to a monochrome printer bitstream."""
    with cli_error_boundary(ctx):
        settings = ctx.obj["settings"]
        driver = registry.get_driver(settings)
        resolved_style = None
        resolved_conversion = None
        if style_json is not None:
            resolved_style = _resolve_style_json(
                operation="image",
                print_defaults=asdict(settings.print_defaults.image),
                presets=_combined_presets(settings),
                style_json_payload=_load_style_json_payload(style_json),
                cli_overrides={
                    "mode": mode.lower() if mode else None,
                    "conversion": conversion.lower() if conversion else None,
                    "orientation": orientation.lower() if orientation else None,
                },
            )
        elif mode is not None or conversion is not None:
            resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = driver.print_image(
            image_path,
            mode=mode.lower() if mode else None,
            conversion=resolved_conversion,
            orientation=orientation.lower() if orientation else None,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            resolved_style=resolved_style,
            address=address,
        )
        _emit_print_result(ctx, result)


@print_group.command("compose")
@click.argument("text")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for the text block.")
@click.option("--min-font-size", type=int, default=None, help="Minimum font size to use when largest-fitting is enabled.")
@click.option(
    "--font-fit",
    type=click.Choice(["manual", "largest-fitting"], case_sensitive=False),
    default=None,
    help="How to choose the compose text font size. largest-fitting starts from a large ceiling and shrinks to the biggest size that fits.",
)
@click.option("--style-json", type=str, default=None, help="Path to a JSON style payload, or - to read JSON from stdin.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option(
    "--layout",
    type=click.Choice(["text-above", "image-above"], case_sensitive=False),
    default=None,
    help="Vertical arrangement for the composed print.",
)
@click.option(
    "--mode",
    type=click.Choice(["sticker", "photo"], case_sensitive=False),
    default=None,
    help="Image preset for the image part of the composed print.",
)
@click.option(
    "--conversion",
    type=click.Choice(["threshold", "edge", "dither"], case_sensitive=False),
    default=None,
    help="Optional low-level conversion override for the image part. When provided, it takes precedence over --mode.",
)
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming composed print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_compose_command(
    ctx: click.Context,
    text: str,
    image_path: Path,
    address: str | None,
    font_size: int | None,
    min_font_size: int | None,
    font_fit: str | None,
    style_json: str | None,
    feed_mm: float | None,
    layout: str | None,
    mode: str | None,
    conversion: str | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print wrapped text together with a local image in one combined layout."""
    with cli_error_boundary(ctx):
        settings = ctx.obj["settings"]
        driver = registry.get_driver(settings)
        resolved_style = None
        resolved_conversion = None
        if style_json is not None:
            resolved_style = _resolve_style_json(
                operation="compose",
                print_defaults=asdict(settings.print_defaults.compose),
                presets=_combined_presets(settings),
                style_json_payload=_load_style_json_payload(style_json),
                cli_overrides={
                    "font_size": font_size,
                    "min_font_size": min_font_size,
                    "font_fit": font_fit.lower() if font_fit else None,
                    "layout": layout.lower() if layout else None,
                    "image_mode": mode.lower() if mode else None,
                    "image_conversion": conversion.lower() if conversion else None,
                },
            )
        elif mode is not None or conversion is not None:
            resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = driver.print_compose(
            text,
            image_path,
            layout=layout.lower() if layout else None,
            font_size=font_size,
            min_font_size=min_font_size,
            font_fit=font_fit.lower() if font_fit else None,
            mode=mode.lower() if mode else None,
            conversion=resolved_conversion,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            resolved_style=resolved_style,
            address=address,
        )
        _emit_print_result(ctx, result)


@print_group.command("self-test")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option(
    "--allow-large-paper-use",
    is_flag=True,
    help="Permit the built-in self-test, which consumes substantially more paper than ordinary prints.",
)
@click.option("--dry-run", is_flag=True, help="Validate the command path without sending the self-test to the printer.")
@click.pass_context
def print_self_test_command(
    ctx: click.Context,
    address: str | None,
    allow_large_paper_use: bool,
    dry_run: bool,
) -> None:
    """Run the printer self-test with an explicit large-paper-use warning."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        result = driver.self_test(
            allow_large_paper_use=allow_large_paper_use,
            dry_run=dry_run,
            address=address,
        )
        _emit_print_result(ctx, result)


def _emit_print_result(ctx: click.Context, result) -> None:
    human_lines = [
        f"Operation: {result.operation}",
        f"Dry run: {result.dry_run}",
        f"Address: {result.address}",
    ]
    if result.warning:
        human_lines.append(f"Warning: {result.warning}")
    if result.source_path:
        human_lines.append(f"Source path: {result.source_path}")
    if result.conversion:
        human_lines.append(f"Conversion: {result.conversion}")
    if result.layout:
        human_lines.append(f"Layout: {result.layout}")
    if result.feed_mm is not None:
        human_lines.append(f"Feed mm: {result.feed_mm}")
    if result.feed_units is not None:
        human_lines.append(f"Feed units: {result.feed_units}")
    if result.font_size is not None:
        human_lines.append(f"Font size: {result.font_size}")
    if result.estimated_length_mm is not None:
        human_lines.append(f"Estimated length mm: {result.estimated_length_mm}")
    if result.max_length_mm is not None:
        human_lines.append(f"Max length mm: {result.max_length_mm}")
    if result.fits_length_limit is not None:
        human_lines.append(f"Fits length limit: {result.fits_length_limit}")
    if result.styling:
        orientation = result.styling.get("orientation")
        font_family = result.styling.get("font_family")
        autofit_applied = result.styling.get("autofit_applied")
        if orientation:
            human_lines.append(f"Orientation: {orientation}")
        if font_family:
            human_lines.append(f"Font family: {font_family}")
        if autofit_applied:
            human_lines.append("Autofit applied: True")
        mode = result.styling.get("mode")
        if mode:
            human_lines.append(f"Mode: {mode}")
    if result.bytes_sent is not None:
        human_lines.append(f"Bytes prepared: {result.bytes_sent}")
    if result.battery_after is not None:
        human_lines.append(f"Battery after: {result.battery_after}")

    emit_result(ctx, {"status": "ok", "result": result.to_dict()}, human_lines)


def _load_style_json_payload(style_json: str) -> dict[str, object]:
    try:
        if style_json == "-":
            raw_payload = click.get_text_stream("stdin").read()
        else:
            raw_payload = Path(style_json).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"Failed to read style JSON: {exc}") from exc

    try:
        parsed = json.loads(raw_payload or "{}")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Failed to parse style JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("Style JSON must be a JSON object")
    return parsed


def _resolve_style_json(
    *,
    operation: str,
    print_defaults: dict[str, object],
    presets: dict[str, dict[str, object]],
    style_json_payload: dict[str, object],
    cli_overrides: dict[str, object],
) -> dict[str, object]:
    try:
        return resolve_operation_style(
            operation=operation,
            print_defaults=print_defaults,
            presets=presets,
            style_json_payload=style_json_payload,
            cli_overrides=cli_overrides,
        )
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def _combined_presets(settings) -> dict[str, dict[str, object]]:
    presets = get_builtin_presets()
    presets.update(settings.presets)
    return presets
