"""CLI command for runtime capability detection."""
from __future__ import annotations

import json as _json

import click

from paperang_cli.protocol._capabilities import report


@click.command("capabilities")
@click.pass_context
def capabilities_command(ctx: click.Context) -> None:
    """Print detected runtime capabilities (transport availability, versions, permissions)."""
    payload = {"status": "ok", "capabilities": report()}
    if (ctx.obj or {}).get("json_output"):
        click.echo(_json.dumps(payload, indent=2))
    else:
        for cap in payload["capabilities"]:
            mark = "OK " if cap["available"] else "FAIL"
            click.echo(f"[{mark}] {cap['name']}: {cap['detail']} (layer={cap['layer']})")
