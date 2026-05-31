"""Battery command."""

from __future__ import annotations

import click

from paperang_cli.drivers import registry
from paperang_cli.output import cli_error_boundary, emit_result


@click.command("battery")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.pass_context
def battery_command(ctx: click.Context, address: str | None) -> None:
    """Query only the current printer battery level without printing."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        battery = driver.battery(address=address)
        emit_result(
            ctx,
            {"status": "ok", "result": battery.to_dict()},
            [
                f"Model: {battery.model}",
                f"Address: {battery.address}",
                f"Connected: {battery.connected}",
                f"Battery: {battery.battery_percent}",
            ],
        )