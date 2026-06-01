"""Probe command."""

from __future__ import annotations

import click

from paperang_cli.drivers import registry
from paperang_cli.models import ProbeResult
from paperang_cli.output import cli_error_boundary, emit_result


@click.command("probe")
@click.option("--address", type=str, help="Optional printer MAC address override.")
@click.pass_context
def probe_command(ctx: click.Context, address: str | None) -> None:
    """Run a safe multi-query probe and summarize the current printer state."""
    with cli_error_boundary(ctx):
        driver = registry.get_driver(ctx.obj["settings"])
        status = driver.status(address=address)
        bluetooth_mac = driver.bluetooth_mac(address=address)
        local_transport_supported = driver.local_transport_supported() if hasattr(driver, "local_transport_supported") else False
        local_transport_note = driver.local_transport_note() if hasattr(driver, "local_transport_note") else None
        result = ProbeResult(
            model=status.model,
            address=status.address,
            transport=status.transport,
            connected=status.connected,
            battery_percent=status.battery_percent,
            serial_number=status.serial_number,
            firmware_version=status.firmware_version,
            hardware_info=status.hardware_info,
            density=status.density,
            power_off_time=status.power_off_time,
            bluetooth_mac=bluetooth_mac.bluetooth_mac,
            local_transport_supported=local_transport_supported,
            local_transport_note=local_transport_note,
            raw=dict(status.raw),
        )
        emit_result(
            ctx,
            {"status": "ok", "result": result.to_dict()},
            [
                f"Model: {result.model}",
                f"Address: {result.address}",
                f"Transport: {result.transport}",
                f"Connected: {result.connected}",
                f"Battery: {result.battery_percent}",
                f"Serial: {result.serial_number}",
                f"Firmware: {result.firmware_version}",
                f"Density: {result.density}",
                f"Power-off time: {result.power_off_time}",
                f"Hardware info: {result.hardware_info}",
                f"Bluetooth MAC: {result.bluetooth_mac}",
                f"Local transport supported: {result.local_transport_supported}",
                f"Local transport note: {result.local_transport_note}",
            ],
        )