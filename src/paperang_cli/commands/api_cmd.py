"""Read-only API inspection commands."""

from __future__ import annotations

import click

from paperang_cli.api import (
    format_api_catalog_human_lines,
    format_api_contract_human_lines,
    get_api_contract,
    list_api_contract_summaries,
)
from paperang_cli.output import emit_result


@click.group("api")
def api_group() -> None:
    """Inspect the public Python API exposed by paperang-cli."""


@api_group.command("list")
@click.pass_context
def api_list_command(ctx: click.Context) -> None:
    """List known model-specific API entries and their availability."""

    emit_result(
        ctx,
        {"status": "ok", "result": list_api_contract_summaries()},
        format_api_catalog_human_lines(),
    )


@api_group.command("p1")
@click.pass_context
def api_p1_command(ctx: click.Context) -> None:
    """Show the supported Paperang P1 Python API contract."""

    emit_result(
        ctx,
        {"status": "ok", "result": get_api_contract("p1")},
        format_api_contract_human_lines("p1"),
    )


@api_group.command("p2")
@click.pass_context
def api_p2_command(ctx: click.Context) -> None:
    """Show the placeholder contract for a future Paperang P2 Python API."""

    emit_result(
        ctx,
        {"status": "ok", "result": get_api_contract("p2")},
        format_api_contract_human_lines("p2"),
    )