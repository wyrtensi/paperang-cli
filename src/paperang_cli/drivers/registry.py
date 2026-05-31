"""Driver registry for supported printer models."""

from __future__ import annotations

from paperang_cli.config import PaperangCliConfig
from paperang_cli.errors import ConfigError
from paperang_cli.drivers.base import PrinterDriver
from paperang_cli.drivers.paperang_p1 import PaperangP1Driver

DRIVER_REGISTRY: dict[str, type[PrinterDriver]] = {
    "paperang_p1": PaperangP1Driver,
}


def supported_models() -> list[str]:
    return sorted(DRIVER_REGISTRY.keys())


def get_driver(settings: PaperangCliConfig) -> PrinterDriver:
    driver_cls = DRIVER_REGISTRY.get(settings.model)
    if driver_cls is None:
        supported = ", ".join(supported_models())
        raise ConfigError(f"Unsupported model '{settings.model}'. Supported models: {supported}")
    return driver_cls(settings)