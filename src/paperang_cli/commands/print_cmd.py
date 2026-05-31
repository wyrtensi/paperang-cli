"""Printing commands."""

from __future__ import annotations

from pathlib import Path

import click

from paperang_cli.drivers import registry
from paperang_cli.output import cli_error_boundary, emit_result
from paperang_cli.render import resolve_image_conversion


@click.group("print")
def print_group() -> None:
    """Print text, print images, or run the built-in self-test."""


@print_group.command("text")
@click.argument("text")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for this print job.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_text_command(
    ctx: click.Context,
    text: str,
    address: str | None,
    font_size: int | None,
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
        feed_mm=feed_mm,
        allow_paper_use=allow_paper_use,
        dry_run=dry_run,
    )


@print_group.command("paragraph")
@click.argument("text")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for this print job.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option("--allow-paper-use", is_flag=True, help="Permit a real paper-consuming print.")
@click.option("--dry-run", is_flag=True, help="Render and validate without sending anything to the printer.")
@click.pass_context
def print_paragraph_command(
    ctx: click.Context,
    text: str,
    address: str | None,
    font_size: int | None,
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
    feed_mm: float | None,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        result = driver.print_text(
            text,
            paragraph=paragraph,
            font_size=font_size,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=address,
        )
        _emit_print_result(ctx, result)


@print_group.command("image")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option(
    "--mode",
    type=click.Choice(["sticker", "photo"], case_sensitive=False),
    default="sticker",
    show_default=True,
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
    feed_mm: float | None,
    mode: str,
    conversion: str,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print a local image file after converting it to a monochrome printer bitstream."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = driver.print_image(
            image_path,
            conversion=resolved_conversion,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=address,
        )
        _emit_print_result(ctx, result)


@print_group.command("compose")
@click.argument("text")
@click.argument("image_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.option("--font-size", type=int, help="Override font size for the text block.")
@click.option("--feed-mm", type=float, help="Override post-print feed in millimeters.")
@click.option(
    "--layout",
    type=click.Choice(["text-above", "image-above"], case_sensitive=False),
    default="text-above",
    show_default=True,
    help="Vertical arrangement for the composed print.",
)
@click.option(
    "--mode",
    type=click.Choice(["sticker", "photo"], case_sensitive=False),
    default="sticker",
    show_default=True,
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
    feed_mm: float | None,
    layout: str,
    mode: str,
    conversion: str,
    allow_paper_use: bool,
    dry_run: bool,
) -> None:
    """Print wrapped text together with a local image in one combined layout."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = driver.print_compose(
            text,
            image_path,
            layout=layout.lower(),
            font_size=font_size,
            conversion=resolved_conversion,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
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
    if result.bytes_sent is not None:
        human_lines.append(f"Bytes prepared: {result.bytes_sent}")
    if result.battery_after is not None:
        human_lines.append(f"Battery after: {result.battery_after}")

    emit_result(ctx, {"status": "ok", "result": result.to_dict()}, human_lines)