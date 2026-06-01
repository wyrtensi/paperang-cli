"""High-level Python API for Paperang P1."""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from paperang_cli.config import PaperangCliConfig, load_config
from paperang_cli.drivers import registry
from paperang_cli.drivers.base import PrinterDriver
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus
from paperang_cli.render import resolve_image_conversion


class PaperangP1:
    """High-level Paperang P1 facade.

    This public API intentionally delegates to the existing driver layer so that
    printer behavior, rendering, BLE handshake, and print sequencing remain
    unchanged.
    """

    def __init__(
        self,
        *,
        address: str | None = None,
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
        """Return the cached or configured printer address."""

        return self._connected_address or self.settings.macaddress or None

    @property
    def connected(self) -> bool:
        """Return whether this facade currently has a cached ready address."""

        return self._connected_address is not None

    def discover(self) -> list[PrinterDevice]:
        """Discover nearby supported Paperang BLE devices."""

        return self._driver.discover()

    def connect(self, address: str | None = None) -> "PaperangP1":
        """Perform a non-printing readiness check and cache the resolved address."""

        battery = self.get_battery(address=address)
        self._remember_address(battery.address)
        return self

    def disconnect(self) -> None:
        """Clear the cached address used for follow-up API calls.

        Real printer communication remains managed by the driver per operation.
        """

        self._connected_address = None

    def get_status(self, *, address: str | None = None) -> PrinterStatus:
        """Query printer status without printing."""

        status = self._driver.status(address=self._resolve_address(address))
        self._remember_address(status.address)
        return status

    def get_battery(self, *, address: str | None = None) -> BatteryStatus:
        """Query battery percentage without printing."""

        battery = self._driver.battery(address=self._resolve_address(address))
        self._remember_address(battery.address)
        return battery

    def get_bluetooth_mac(self, *, address: str | None = None) -> BluetoothMacStatus:
        """Query the printer-reported Bluetooth MAC address."""

        bluetooth_mac = self._driver.bluetooth_mac(address=self._resolve_address(address))
        self._remember_address(bluetooth_mac.address)
        return bluetooth_mac

    def get_bt_mac(self, *, address: str | None = None) -> BluetoothMacStatus:
        """Compatibility alias for get_bluetooth_mac()."""

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
        """Print a short text block."""

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
        """Print wrapped text using the paragraph render path."""

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
        """Print a local image file."""

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
        """Print wrapped text and an image in one job."""

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
        """Run the printer self-test with the existing large-paper safety gate."""

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
        return PaperangCliConfig(), None, False

    settings, resolved_path, config_exists = load_config(config_path)
    return settings, resolved_path, config_exists


def _merge_settings(
    base_settings: PaperangCliConfig,
    *,
    address: str | None,
    printer_width: int | None,
    print_density: int | None,
    post_print_feed_mm: float | None,
    discovery_names: list[str] | None,
) -> PaperangCliConfig:
    merged = base_settings.to_dict()
    if address is not None:
        merged["macaddress"] = address
    if printer_width is not None:
        merged["printerwidth"] = printer_width
    if print_density is not None:
        merged["print_density"] = print_density
    if post_print_feed_mm is not None:
        merged["post_print_feed_mm"] = post_print_feed_mm
    if discovery_names is not None:
        merged["discovery_names"] = list(discovery_names)

    return PaperangCliConfig.from_mapping(merged)