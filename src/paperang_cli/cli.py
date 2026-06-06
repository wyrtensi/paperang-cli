"""Standalone paperang-cli entrypoint."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click

from paperang_cli import __version__
from paperang_cli.commands.api_cmd import api_group
from paperang_cli.commands.capabilities_cmd import capabilities_command
from paperang_cli.commands.battery import battery_command
from paperang_cli.commands.config_cmd import config_group
from paperang_cli.commands.discover import discover_command
from paperang_cli.commands.mac import mac_command
from paperang_cli.commands.print_cmd import print_group
from paperang_cli.commands.probe import probe_command
from paperang_cli.commands.status import status_command
from paperang_cli.config import load_config
from paperang_cli.errors import PaperangCliError


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Path to a paperang-cli JSON config file.",
)
@click.option("--printer", "printer_name", type=str, help="Named printer profile from the config printers map.")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON output.")
@click.option("--debug", is_flag=True, help="Enable verbose logging.")
@click.version_option(version=__version__)
@click.pass_context
def cli(
    ctx: click.Context,
    config_path: Path | None,
    printer_name: str | None,
    json_output: bool,
    debug: bool,
) -> None:
    """Standalone CLI for Paperang printers."""
    configure_logging(debug)
    try:
        settings, resolved_path, config_exists = load_config(config_path, printer_name=printer_name)
    except PaperangCliError as exc:
        if json_output:
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
            raise SystemExit(exc.exit_code)
        raise click.ClickException(str(exc)) from exc

    ctx.obj = {
        "settings": settings,
        "config_path": resolved_path,
        "config_exists": config_exists,
        "printer_name": printer_name,
        "json_output": json_output,
        "debug": debug,
    }


cli.add_command(status_command)
cli.add_command(battery_command)
cli.add_command(mac_command)
cli.add_command(probe_command)
cli.add_command(discover_command)
cli.add_command(api_group)
cli.add_command(print_group)
cli.add_command(config_group)
cli.add_command(capabilities_command)


def main() -> None:
    cli()
