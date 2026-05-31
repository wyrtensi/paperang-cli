"""Bluetooth MAC command."""

from __future__ import annotations

import click

from paperang_cli.drivers import registry
from paperang_cli.output import cli_error_boundary, emit_result


@click.command("mac")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.pass_context
def mac_command(ctx: click.Context, address: str | None) -> None:
    """Query the printer-reported Bluetooth MAC address without printing."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        mac_status = driver.bluetooth_mac(address=address)
        emit_result(
            ctx,
            {"status": "ok", "result": mac_status.to_dict()},
            [
                f"Model: {mac_status.model}",
                f"Address: {mac_status.address}",
                f"Connected: {mac_status.connected}",
                f"Bluetooth MAC: {mac_status.bluetooth_mac}",
            ],
        )