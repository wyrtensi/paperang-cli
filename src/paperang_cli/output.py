"""Human and JSON output helpers."""

from __future__ import annotations

import json
from contextlib import contextmanager

import click

from paperang_cli.errors import PaperangCliError


def wants_json(ctx: click.Context) -> bool:
    return bool(ctx.obj and ctx.obj.get("json_output"))


def emit_result(ctx: click.Context, payload: dict, human_lines: list[str]) -> None:
    if wants_json(ctx):
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return

    for line in human_lines:
        click.echo(line)


def emit_error(ctx: click.Context | None, exc: PaperangCliError) -> None:
    if ctx is not None and wants_json(ctx):
        click.echo(
            json.dumps(
                {
                    "status": "error",
                    "code": exc.code,
                    "message": str(exc),
                    "exit_code": exc.exit_code,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            ),
            err=True,
        )
    else:
        click.echo(f"{exc.code}: {exc}", err=True)
    raise SystemExit(exc.exit_code)


@contextmanager
def cli_error_boundary(ctx: click.Context):
    try:
        yield
    except PaperangCliError as exc:
        emit_error(ctx, exc)