"""Status command."""

from __future__ import annotations

import click

from paperang_cli.drivers import registry
from paperang_cli.output import cli_error_boundary, emit_result


@click.command("status")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.pass_context
def status_command(ctx: click.Context, address: str | None) -> None:
    """Query printer status without printing."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        status = driver.status(address=address)
        emit_result(
            ctx,
            {"status": "ok", "result": status.to_dict()},
            [
                f"Model: {status.model}",
                f"Address: {status.address}",
                f"Connected: {status.connected}",
                f"Battery: {status.battery_percent}",
                f"Serial: {status.serial_number}",
                f"Firmware: {status.firmware_version}",
                f"Density: {status.density}",
                f"Power-off time: {status.power_off_time}",
                f"Hardware info: {status.hardware_info}",
            ],
        )