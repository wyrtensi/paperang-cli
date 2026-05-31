"""Discover command."""

from __future__ import annotations

import click

from paperang_cli.drivers import registry
from paperang_cli.output import cli_error_boundary, emit_result


@click.command("discover")
@click.pass_context
def discover_command(ctx: click.Context) -> None:
    """Discover nearby supported printers without printing."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        devices = driver.discover()
        payload = [device.to_dict() for device in devices]
        if devices:
            human_lines = [f"{device.name} [{device.address}]" for device in devices]
        else:
            human_lines = ["No supported printers discovered."]
        emit_result(ctx, {"status": "ok", "result": payload}, human_lines)