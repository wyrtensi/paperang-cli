"""Config commands."""

from __future__ import annotations

from pathlib import Path

import click

from paperang_cli.config import write_example_config
from paperang_cli.drivers.registry import supported_models
from paperang_cli.output import cli_error_boundary, emit_result


@click.group("config")
def config_group() -> None:
    """Inspect or initialize paperang-cli configuration."""


@config_group.command("show")
@click.pass_context
def show_config_command(ctx: click.Context) -> None:
    """Show the resolved config and whether it came from a file."""
    settings = ctx.obj["settings"]
    config_path = ctx.obj["config_path"]
    config_exists = ctx.obj["config_exists"]
    emit_result(
        ctx,
        {
            "status": "ok",
            "result": {
                "config_path": str(config_path),
                "config_exists": config_exists,
                "config": settings.to_dict(),
                "supported_models": supported_models(),
            },
        },
        [
            f"Config path: {config_path}",
            f"Config exists: {config_exists}",
            f"Active printer: {settings.active_printer or '<single>'}",
            f"Default printer: {settings.default_printer or '<single>'}",
            f"Model: {settings.model}",
            f"MAC address: {settings.macaddress or '<unset>'}",
            f"Printer width: {settings.printerwidth}",
            f"Print density: {settings.print_density}",
            f"Post-print feed mm: {settings.post_print_feed_mm}",
            f"Supported models: {', '.join(supported_models())}",
        ],
    )


@config_group.command("path")
@click.pass_context
def config_path_command(ctx: click.Context) -> None:
    """Show the resolved config path."""
    config_path = ctx.obj["config_path"]
    emit_result(
        ctx,
        {"status": "ok", "result": {"config_path": str(config_path)}},
        [str(config_path)],
    )


@config_group.command("init")
@click.option(
    "--path",
    "destination",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Write the example config to a custom destination.",
)
@click.option("--force", is_flag=True, help="Overwrite an existing destination if present.")
@click.pass_context
def config_init_command(ctx: click.Context, destination: Path | None, force: bool) -> None:
    """Write an example config file for the standalone CLI project."""
    with cli_error_boundary(ctx):
        target = destination or ctx.obj["config_path"]
        written_path = write_example_config(target, overwrite=force)
        emit_result(
            ctx,
            {"status": "ok", "result": {"config_path": str(written_path)}},
            [f"Wrote example config to {written_path}"],
        )
