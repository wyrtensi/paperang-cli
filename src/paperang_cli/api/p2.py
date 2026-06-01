"""High-level Python API for Paperang P2."""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from paperang_cli.config import PaperangCliConfig, load_config
from paperang_cli.drivers import registry
from paperang_cli.drivers.base import PrinterDriver
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus
from paperang_cli.render import resolve_image_conversion


class PaperangP2:
    """High-level Paperang P2 facade.

    This public API delegates to the driver layer so USB/BLE transport
    selection, rendering, dry-run behavior, and safety gates remain aligned
    with the CLI.
    """

    def __init__(
        self,
        *,
        address: str | None = None,
        transport: str | None = None,
        config_path: str | PathLike[str] | None = None,
        printer_width: int | None = None,
        print_density: int | None = None,
        post_print_feed_mm: float | None = None,
        discovery_names: list[str] | None = None,
    ) -> None:
        base_settings, resolved_config_path, config_exists = _load_api_settings(config_path)
        self.settings = _merge_settings(
            base_settings,
            address=address,
            transport=transport,
            printer_width=printer_width,
            print_density=print_density,
            post_print_feed_mm=post_print_feed_mm,
            discovery_names=discovery_names,
        )
        self.config_path = resolved_config_path
        self.config_exists = config_exists
        self._driver: PrinterDriver = registry.get_driver(self.settings)
        self._connected_address: str | None = self.settings.macaddress or None

    @property
    def address(self) -> str | None:
        return self._connected_address or self.settings.macaddress or None

    @property
    def connected(self) -> bool:
        return self._connected_address is not None

    def discover(self) -> list[PrinterDevice]:
        return self._driver.discover()

    def connect(self, address: str | None = None) -> "PaperangP2":
        battery = self.get_battery(address=address)
        self._remember_address(battery.address)
        return self

    def disconnect(self) -> None:
        self._connected_address = None

    def get_status(self, *, address: str | None = None) -> PrinterStatus:
        status = self._driver.status(address=self._resolve_address(address))
        self._remember_address(status.address)
        return status

    def get_battery(self, *, address: str | None = None) -> BatteryStatus:
        battery = self._driver.battery(address=self._resolve_address(address))
        self._remember_address(battery.address)
        return battery

    def get_bluetooth_mac(self, *, address: str | None = None) -> BluetoothMacStatus:
        bluetooth_mac = self._driver.bluetooth_mac(address=self._resolve_address(address))
        self._remember_address(bluetooth_mac.address)
        return bluetooth_mac

    def get_bt_mac(self, *, address: str | None = None) -> BluetoothMacStatus:
        return self.get_bluetooth_mac(address=address)

    def print_text(
        self,
        text: str,
        *,
        font_size: int | None = None,
        font_family: str | None = None,
        min_font_size: int | None = None,
        font_fit: str | None = None,
        autofit: bool | None = None,
        orientation: str | None = None,
        feed_mm: float | None = None,
        dry_run: bool = False,
        allow_paper_use: bool = False,
        address: str | None = None,
    ) -> PrintResult:
        result = self._driver.print_text(
            text,
            paragraph=False,
            font_size=font_size,
            font_family=font_family.lower() if font_family else None,
            min_font_size=min_font_size,
            font_fit=font_fit,
            autofit=autofit,
            orientation=orientation.lower() if orientation else None,
            horizontal_padding_px=None,
            vertical_padding_px=None,
            line_spacing_px=None,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=self._resolve_address(address),
        )
        self._remember_address(result.address)
        return result

    def print_paragraph(
        self,
        text: str,
        *,
        font_size: int | None = None,
        font_family: str | None = None,
        min_font_size: int | None = None,
        font_fit: str | None = None,
        autofit: bool | None = None,
        orientation: str | None = None,
        feed_mm: float | None = None,
        dry_run: bool = False,
        allow_paper_use: bool = False,
        address: str | None = None,
    ) -> PrintResult:
        result = self._driver.print_text(
            text,
            paragraph=True,
            font_size=font_size,
            font_family=font_family.lower() if font_family else None,
            min_font_size=min_font_size,
            font_fit=font_fit,
            autofit=autofit,
            orientation=orientation.lower() if orientation else None,
            horizontal_padding_px=None,
            vertical_padding_px=None,
            line_spacing_px=None,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=self._resolve_address(address),
        )
        self._remember_address(result.address)
        return result

    def print_image(
        self,
        image_path: str | PathLike[str],
        *,
        mode: str | None = None,
        conversion: str | None = None,
        orientation: str | None = None,
        feed_mm: float | None = None,
        dry_run: bool = False,
        allow_paper_use: bool = False,
        address: str | None = None,
    ) -> PrintResult:
        resolved_conversion = None
        if mode is not None or conversion is not None:
            resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = self._driver.print_image(
            Path(image_path),
            mode=mode.lower() if mode else None,
            conversion=resolved_conversion,
            orientation=orientation.lower() if orientation else None,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=self._resolve_address(address),
        )
        self._remember_address(result.address)
        return result

    def print_compose(
        self,
        text: str,
        image_path: str | PathLike[str],
        *,
        layout: str | None = None,
        font_size: int | None = None,
        min_font_size: int | None = None,
        font_fit: str | None = None,
        mode: str | None = None,
        conversion: str | None = None,
        feed_mm: float | None = None,
        dry_run: bool = False,
        allow_paper_use: bool = False,
        address: str | None = None,
    ) -> PrintResult:
        resolved_conversion = None
        if mode is not None or conversion is not None:
            resolved_conversion = resolve_image_conversion(mode=mode, conversion=conversion)
        result = self._driver.print_compose(
            text,
            Path(image_path),
            layout=layout.lower() if layout else None,
            font_size=font_size,
            min_font_size=min_font_size,
            font_fit=font_fit,
            mode=mode.lower() if mode else None,
            conversion=resolved_conversion,
            feed_mm=feed_mm,
            allow_paper_use=allow_paper_use,
            dry_run=dry_run,
            address=self._resolve_address(address),
        )
        self._remember_address(result.address)
        return result

    def print_self_test(
        self,
        *,
        dry_run: bool = False,
        allow_large_paper_use: bool = False,
        address: str | None = None,
    ) -> PrintResult:
        result = self._driver.self_test(
            allow_large_paper_use=allow_large_paper_use,
            dry_run=dry_run,
            address=self._resolve_address(address),
        )
        self._remember_address(result.address)
        return result

    def _resolve_address(self, address: str | None) -> str | None:
        return address or self._connected_address or self.settings.macaddress or None

    def _remember_address(self, address: str | None) -> None:
        if address and address != "unknown":
            self._connected_address = address


def _load_api_settings(
    config_path: str | PathLike[str] | None,
) -> tuple[PaperangCliConfig, Path | None, bool]:
    if config_path is None:
        return PaperangCliConfig.from_mapping({"model": "paperang_p2"}), None, False

    settings, resolved_path, config_exists = load_config(config_path)
    return settings, resolved_path, config_exists


def _merge_settings(
    base_settings: PaperangCliConfig,
    *,
    address: str | None,
    transport: str | None,
    printer_width: int | None,
    print_density: int | None,
    post_print_feed_mm: float | None,
    discovery_names: list[str] | None,
) -> PaperangCliConfig:
    merged = base_settings.to_dict()
    merged["model"] = "paperang_p2"
    if address is not None:
        merged["macaddress"] = address
    if transport is not None:
        merged["transport"] = transport
    if printer_width is not None:
        merged["printerwidth"] = printer_width
    if print_density is not None:
        merged["print_density"] = print_density
    if post_print_feed_mm is not None:
        merged["post_print_feed_mm"] = post_print_feed_mm
    if discovery_names is not None:
        merged["discovery_names"] = list(discovery_names)

    return PaperangCliConfig.from_mapping(merged)
