"""Abstract printer driver boundary for future models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from paperang_cli.config import PaperangCliConfig
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus


class PrinterDriver(ABC):
    model_id = "unknown"
    transport = "unknown"

    def __init__(self, settings: PaperangCliConfig):
        self.settings = settings

    @abstractmethod
    def discover(self) -> list[PrinterDevice]:
        raise NotImplementedError

    @abstractmethod
    def status(self, address: str | None = None) -> PrinterStatus:
        raise NotImplementedError

    @abstractmethod
    def battery(self, address: str | None = None) -> BatteryStatus:
        raise NotImplementedError

    @abstractmethod
    def bluetooth_mac(self, address: str | None = None) -> BluetoothMacStatus:
        raise NotImplementedError

    @abstractmethod
    def print_text(
        self,
        text: str,
        *,
        paragraph: bool,
        font_size: int | None,
        font_family: str | None,
        min_font_size: int | None,
        autofit: bool | None,
        orientation: str | None,
        horizontal_padding_px: int | None,
        vertical_padding_px: int | None,
        line_spacing_px: int | None,
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        raise NotImplementedError

    @abstractmethod
    def print_image(
        self,
        image_path: Path,
        *,
        mode: str | None,
        conversion: str | None,
        orientation: str | None,
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        raise NotImplementedError

    @abstractmethod
    def print_compose(
        self,
        text: str,
        image_path: Path,
        *,
        layout: str | None,
        font_size: int | None,
        mode: str | None,
        conversion: str | None,
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        raise NotImplementedError

    @abstractmethod
    def self_test(
        self,
        *,
        allow_large_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        raise NotImplementedError