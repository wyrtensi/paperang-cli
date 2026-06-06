"""Paperang P2 driver implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path

from paperang_cli.drivers.base import PrinterDriver
from paperang_cli.errors import DriverError, PrinterNotFoundError, SafetyError
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus
from paperang_cli.render import (
    DEFAULT_COMPOSE_FONT_SIZE,
    DEFAULT_PARAGRAPH_FONT_SIZE,
    DEFAULT_TEXT_FONT_SIZE,
    feed_units_from_mm,
    render_compose_job,
    render_image_job,
    render_text_job,
    resolve_image_conversion,
)

SELF_TEST_WARNING = "The built-in self-test consumes substantially more paper than normal text or image prints."
IMAGE_PRINT_WARNING = "Image printing is more experimental than text printing; conversion quality and physical output still need manual validation on real hardware."
COMPOSE_PRINT_WARNING = "Combined text-and-image printing uses the same image conversion path as image printing; validate physical output on real hardware before relying on the layout."
USB_DEVICE_ADDRESS = "usb://paperang_p2"
USB_DEVICE_DETAILS = "USB VID=0x4348 PID=0x5584"
LOCAL_TRANSPORT_NOTE = (
    "Paperang P2 is supported through BLE FF00/A5 when transport='ble'. "
    "USB is available only as an experimental software path."
)
P2_RENDER_SCALE = 576 / 384
P2_DEFAULT_TEXT_FONT_SIZE = round(DEFAULT_TEXT_FONT_SIZE * P2_RENDER_SCALE)
P2_DEFAULT_PARAGRAPH_FONT_SIZE = round(DEFAULT_PARAGRAPH_FONT_SIZE * P2_RENDER_SCALE)
P2_DEFAULT_COMPOSE_FONT_SIZE = round(DEFAULT_COMPOSE_FONT_SIZE * P2_RENDER_SCALE)
P2_DEFAULT_TEXT_HORIZONTAL_PADDING_PX = round(16 * P2_RENDER_SCALE)
P2_DEFAULT_TEXT_VERTICAL_PADDING_PX = round(12 * P2_RENDER_SCALE)
P2_DEFAULT_PARAGRAPH_HORIZONTAL_PADDING_PX = round(12 * P2_RENDER_SCALE)
P2_DEFAULT_PARAGRAPH_VERTICAL_PADDING_PX = round(10 * P2_RENDER_SCALE)
P2_DEFAULT_COMPOSE_HORIZONTAL_PADDING_PX = round(12 * P2_RENDER_SCALE)
P2_DEFAULT_COMPOSE_VERTICAL_PADDING_PX = round(10 * P2_RENDER_SCALE)
P2_DEFAULT_COMPOSE_SPACER_HEIGHT_PX = round(12 * P2_RENDER_SCALE)


def _resolved_bool_style(effective_style: dict[str, object], key: str, *, default: bool) -> bool:
    value = effective_style.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise DriverError(f"resolved_style.{key} must be a boolean")


class PaperangP2Driver(PrinterDriver):
    model_id = "paperang_p2"
    transport = "multi"

    def local_transport_supported(self) -> bool:
        return True

    def local_transport_note(self) -> str | None:
        return LOCAL_TRANSPORT_NOTE

    def discover(self) -> list[PrinterDevice]:
        if self._resolved_transport() == "ble":
            from paperang_cli.protocol.hardware_bleak import discover_paperang_devices

            devices = discover_paperang_devices(self.settings.discovery_names)
            return [
                PrinterDevice(
                    name=device.name or "Paperang P2",
                    address=device.address,
                    rssi=getattr(device, "rssi", None),
                    details=str(getattr(device, "details", "")) or None,
                )
                for device in devices
            ]

        printer = self._build_printer(None)
        try:
            if not printer.connect():
                return []
        except Exception as exc:
            if _is_usb_backend_error(exc):
                raise DriverError(_p2_usb_backend_error_message()) from exc
            return []
        finally:
            try:
                printer.disconnect()
            except Exception:
                pass

        return [
            PrinterDevice(
                name="Paperang P2",
                address=USB_DEVICE_ADDRESS,
                details=USB_DEVICE_DETAILS,
            )
        ]

    def status(self, address: str | None = None) -> PrinterStatus:
        printer = self._connect_printer(address)
        resolved_address = self._resolved_address(address)
        try:
            firmware = printer.get_version()
            serial = printer.get_sn()
            battery = printer.get_battery()
            hardware = printer.get_hw_info()
            density = printer.get_heat_density()
            power_off = printer.get_power_down_time()
            reported_model = printer.get_model()

            return PrinterStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self._resolved_transport(),
                connected=True,
                battery_percent=battery,
                serial_number=serial,
                firmware_version=firmware,
                hardware_info=hardware,
                density=density,
                power_off_time=power_off,
                raw={
                    "firmware": firmware or "",
                    "serial_number": serial or "",
                    "hardware_info": hardware or "",
                    "reported_model": reported_model or "",
                },
            )
        finally:
            printer.disconnect()

    def battery(self, address: str | None = None) -> BatteryStatus:
        printer = self._connect_printer(address)
        resolved_address = self._resolved_address(address)
        try:
            battery = printer.get_battery()
            return BatteryStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self._resolved_transport(),
                connected=True,
                battery_percent=battery,
            )
        finally:
            printer.disconnect()

    def bluetooth_mac(self, address: str | None = None) -> BluetoothMacStatus:
        printer = self._connect_printer(address)
        resolved_address = self._resolved_address(address)
        try:
            bluetooth_mac = self._normalize_bluetooth_mac(printer.get_bt_mac())
            return BluetoothMacStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self._resolved_transport(),
                connected=True,
                bluetooth_mac=bluetooth_mac,
            )
        finally:
            printer.disconnect()

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
        font_fit: str | None = None,
        resolved_style: dict[str, object] | None = None,
        address: str | None = None,
    ) -> PrintResult:
        if not text:
            raise DriverError("Text content must not be empty")

        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)

        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        style_defaults = self.settings.print_defaults.paragraph if paragraph else self.settings.print_defaults.text
        effective_style = dict(resolved_style or {})
        if not effective_style:
            effective_style = {
                "font_size": font_size if font_size is not None else style_defaults.font_size,
                "font_family": font_family or style_defaults.font_family,
                "min_font_size": min_font_size if min_font_size is not None else style_defaults.min_font_size,
                "font_fit": font_fit or style_defaults.font_fit,
                "autofit": autofit if autofit is not None else style_defaults.autofit,
                "orientation": orientation or style_defaults.orientation,
                "horizontal_padding_px": (
                    horizontal_padding_px if horizontal_padding_px is not None else style_defaults.horizontal_padding_px
                ),
                "vertical_padding_px": (
                    vertical_padding_px if vertical_padding_px is not None else style_defaults.vertical_padding_px
                ),
                "line_spacing_px": line_spacing_px if line_spacing_px is not None else style_defaults.line_spacing_px,
                "max_length_mm": style_defaults.max_length_mm,
                "overflow_policy": style_defaults.overflow_policy,
                "break_long_words": style_defaults.break_long_words,
            }
        _apply_p2_text_render_defaults(effective_style, paragraph=paragraph)
        rendered = render_text_job(
            text,
            printer_width=self.settings.printerwidth,
            paragraph=paragraph,
            font_size=effective_style.get("font_size"),
            font_family=str(effective_style.get("font_family") or style_defaults.font_family),
            min_font_size=effective_style.get("min_font_size"),
            font_fit=str(effective_style.get("font_fit") or style_defaults.font_fit),
            autofit=_resolved_bool_style(effective_style, "autofit", default=style_defaults.autofit),
            orientation=str(effective_style.get("orientation") or style_defaults.orientation),
            horizontal_padding_px=effective_style.get("horizontal_padding_px"),
            vertical_padding_px=effective_style.get("vertical_padding_px"),
            line_spacing_px=effective_style.get("line_spacing_px"),
            max_length_mm=effective_style.get("max_length_mm"),
            overflow_policy=str(effective_style.get("overflow_policy") or style_defaults.overflow_policy),
            break_long_words=_resolved_bool_style(
                effective_style,
                "break_long_words",
                default=style_defaults.break_long_words,
            ),
            advance_mm_per_px=self.settings.calibration.advance_mm_per_px,
            printable_width_mm=self.settings.calibration.printable_width_mm,
            binary_text=True,
        )
        return self._send_bitmap_job(
            bitstream=rendered.bitstream,
            operation="paragraph" if paragraph else "text",
            paragraph=paragraph,
            font_size=rendered.styling.font_size,
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
            estimated_length_mm=rendered.estimated_length_mm,
            max_length_mm=rendered.max_length_mm,
            fits_length_limit=rendered.fits_length_limit,
            styling=rendered.styling.to_dict(),
        )

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
        resolved_style: dict[str, object] | None = None,
        address: str | None = None,
    ) -> PrintResult:
        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)
        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        image_defaults = self.settings.print_defaults.image
        effective_style = dict(resolved_style or {})
        if not effective_style:
            effective_style = {
                "mode": mode or image_defaults.mode,
                "conversion": conversion or image_defaults.conversion,
                "orientation": orientation or image_defaults.orientation,
                "max_length_mm": image_defaults.max_length_mm,
                "fit_mode": image_defaults.fit_mode,
            }
        resolved_mode = str(effective_style.get("mode") or image_defaults.mode)
        resolved_conversion = resolve_image_conversion(
            mode=resolved_mode,
            conversion=effective_style.get("conversion") or image_defaults.conversion,
        )
        rendered = render_image_job(
            image_path,
            printer_width=self.settings.printerwidth,
            conversion=resolved_conversion,
            orientation=str(effective_style.get("orientation") or image_defaults.orientation),
            mode=resolved_mode,
            max_length_mm=effective_style.get("max_length_mm"),
            fit_mode=str(effective_style.get("fit_mode") or image_defaults.fit_mode),
            advance_mm_per_px=self.settings.calibration.advance_mm_per_px,
            printable_width_mm=self.settings.calibration.printable_width_mm,
        )
        return self._send_bitmap_job(
            bitstream=rendered.bitstream,
            operation="image",
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
            source_path=str(image_path),
            conversion=resolved_conversion,
            estimated_length_mm=rendered.estimated_length_mm,
            max_length_mm=rendered.max_length_mm,
            fits_length_limit=rendered.fits_length_limit,
            warning=IMAGE_PRINT_WARNING,
            styling=rendered.styling.to_dict(),
        )

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
        min_font_size: int | None = None,
        font_fit: str | None = None,
        resolved_style: dict[str, object] | None = None,
        address: str | None = None,
    ) -> PrintResult:
        if not text:
            raise DriverError("Text content must not be empty")

        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)
        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        compose_defaults = self.settings.print_defaults.compose
        effective_style = dict(resolved_style or {})
        resolved_layout = str(effective_style.get("layout") or layout or compose_defaults.layout)
        resolved_font_size = effective_style.get("font_size")
        if resolved_font_size is None:
            resolved_font_size = font_size if font_size is not None else (compose_defaults.font_size or P2_DEFAULT_COMPOSE_FONT_SIZE)
        resolved_min_font_size = effective_style.get("min_font_size")
        if resolved_min_font_size is None:
            resolved_min_font_size = min_font_size if min_font_size is not None else compose_defaults.min_font_size
        resolved_font_fit = str(effective_style.get("font_fit") or font_fit or compose_defaults.font_fit)
        resolved_mode = str(effective_style.get("image_mode") or mode or compose_defaults.image_mode)
        resolved_conversion = resolve_image_conversion(
            mode=resolved_mode,
            conversion=effective_style.get("image_conversion") or conversion or compose_defaults.image_conversion,
        )
        rendered = render_compose_job(
            text,
            image_path,
            printer_width=self.settings.printerwidth,
            font_size=resolved_font_size,
            min_font_size=resolved_min_font_size,
            font_fit=resolved_font_fit,
            font_family=str(effective_style.get("font_family") or compose_defaults.font_family),
            horizontal_padding_px=_style_value_with_default(
                effective_style,
                "horizontal_padding_px",
                compose_defaults.horizontal_padding_px,
                P2_DEFAULT_COMPOSE_HORIZONTAL_PADDING_PX,
            ),
            vertical_padding_px=_style_value_with_default(
                effective_style,
                "vertical_padding_px",
                compose_defaults.vertical_padding_px,
                P2_DEFAULT_COMPOSE_VERTICAL_PADDING_PX,
            ),
            line_spacing_px=effective_style.get("line_spacing_px", compose_defaults.line_spacing_px),
            spacer_height_px=_style_value_with_default(
                effective_style,
                "spacer_height_px",
                compose_defaults.spacer_height_px,
                P2_DEFAULT_COMPOSE_SPACER_HEIGHT_PX,
            ),
            conversion=resolved_conversion,
            layout=resolved_layout,
            max_length_mm=effective_style.get("max_length_mm", compose_defaults.max_length_mm),
            overflow_policy=str(effective_style.get("overflow_policy") or compose_defaults.overflow_policy),
            break_long_words=_resolved_bool_style(
                effective_style,
                "break_long_words",
                default=compose_defaults.break_long_words,
            ),
            advance_mm_per_px=self.settings.calibration.advance_mm_per_px,
            mode=resolved_mode,
        )
        return self._send_bitmap_job(
            bitstream=rendered.bitstream,
            operation="compose",
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
            font_size=rendered.styling.font_size,
            source_path=str(image_path),
            conversion=resolved_conversion,
            layout=resolved_layout,
            estimated_length_mm=rendered.estimated_length_mm,
            max_length_mm=rendered.max_length_mm,
            fits_length_limit=rendered.fits_length_limit,
            warning=COMPOSE_PRINT_WARNING,
            styling=rendered.styling.to_dict(),
        )

    def self_test(
        self,
        *,
        allow_large_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        if dry_run:
            return PrintResult(
                model=self.model_id,
                address=self._resolved_address(address),
                operation="self-test",
                dry_run=True,
                warning=SELF_TEST_WARNING,
            )

        if not allow_large_paper_use:
            raise SafetyError("Self-test consumes substantially more paper and requires --allow-large-paper-use")

        printer = self._connect_printer(address)
        resolved_address = self._resolved_address(address)
        try:
            printer.print_test_page()
            return PrintResult(
                model=self.model_id,
                address=resolved_address,
                operation="self-test",
                dry_run=False,
                warning=SELF_TEST_WARNING,
            )
        finally:
            printer.disconnect()

    def _connect_printer(self, address: str | None):
        printer = self._build_printer(address)
        try:
            if self._resolved_transport() == "ble":
                _ensure_current_event_loop()
            connected = printer.connect()
        except Exception as exc:
            if _is_usb_backend_error(exc):
                raise DriverError(_p2_usb_backend_error_message()) from exc
            raise PrinterNotFoundError(
                f"Unable to connect to a supported Paperang P2 printer over {self._resolved_transport()}"
            ) from exc

        if not connected:
            raise PrinterNotFoundError(
                f"Unable to connect to a supported Paperang P2 printer over {self._resolved_transport()}"
            )

        return printer

    def _build_printer(self, address: str | None):
        if self._resolved_transport() == "ble":
            return _AutoBleP2Printer(
                self._build_nus_printer(address),
                self._build_ff00_printer(address),
            )

        try:
            from paperang.printer._printing import PaperangP2
            from paperang.transport._usb import UsbTransport
        except ImportError as exc:
            raise DriverError(
                "Paperang P2 support requires the upstream 'paperang-p2-lib' package to be installed"
            ) from exc

        return PaperangP2(transport=UsbTransport())

    def _build_nus_printer(self, address: str | None):
        try:
            from paperang.printer._printing import PaperangP2
            from paperang.transport._ble import BleTransport
        except ImportError as exc:
            raise DriverError(
                "Paperang P2 support requires the upstream 'paperang-p2-lib' package to be installed"
            ) from exc

        transport = BleTransport(
            address=address or self.settings.macaddress or None,
            name=self._ble_scan_name(),
        )
        return PaperangP2(transport=transport)

    def _build_ff00_printer(self, address: str | None):
        from paperang_cli.protocol.p2_ble_ff00 import PaperangP2Ff00

        return PaperangP2Ff00(
            address or self.settings.macaddress or None,
            name=self._ff00_ble_scan_name(),
        )

    def _ble_scan_name(self) -> str:
        if not self.settings.discovery_names:
            return "Paperang"
        if "Paperang" in self.settings.discovery_names:
            return "Paperang"
        return self.settings.discovery_names[0]

    def _ff00_ble_scan_name(self) -> str:
        if not self.settings.discovery_names:
            return "Paperang_P2"
        for name in ("Paperang_P2", "Paperang_P2S"):
            if name in self.settings.discovery_names:
                return name
        return self._ble_scan_name()

    def _resolved_transport(self) -> str:
        return self.settings.transport or "usb"

    def _resolved_address(self, requested_address: str | None) -> str:
        if self._resolved_transport() == "usb":
            return requested_address or USB_DEVICE_ADDRESS
        return requested_address or self.settings.macaddress or "unknown"

    def _require_paper_use(self, *, allow_paper_use: bool, dry_run: bool) -> None:
        if not dry_run and not allow_paper_use:
            raise SafetyError("Real printing requires --allow-paper-use")

    def _send_bitmap_job(
        self,
        *,
        bitstream: bytes,
        operation: str,
        feed_mm: float,
        dry_run: bool,
        address: str | None,
        paragraph: bool | None = None,
        font_size: int | None = None,
        source_path: str | None = None,
        conversion: str | None = None,
        layout: str | None = None,
        estimated_length_mm: float | None = None,
        max_length_mm: float | None = None,
        fits_length_limit: bool | None = None,
        warning: str | None = None,
        styling: dict | None = None,
    ) -> PrintResult:
        feed_units = feed_units_from_mm(feed_mm)
        resolved_address = self._resolved_address(address)

        if dry_run:
            return PrintResult(
                model=self.model_id,
                address=resolved_address,
                operation=operation,
                dry_run=True,
                feed_mm=feed_mm,
                feed_units=feed_units,
                font_size=font_size,
                bytes_sent=len(bitstream),
                paragraph=paragraph,
                source_path=source_path,
                conversion=conversion,
                layout=layout,
                estimated_length_mm=estimated_length_mm,
                max_length_mm=max_length_mm,
                fits_length_limit=fits_length_limit,
                warning=warning,
                styling=styling,
            )

        printer = self._connect_printer(address)
        try:
            printer.set_paper_type(0)
            printer.set_heat_density(int(self.settings.print_density))
            width_bytes = max(1, self.settings.printerwidth // 8)
            if hasattr(printer, "print_bitmap_with_feed"):
                printer.print_bitmap_with_feed(bitstream, width_bytes=width_bytes, feed_mm=feed_mm)
            else:
                printer.print_bitmap(bitstream, width_bytes=width_bytes)
                if feed_units > 0:
                    printer.feed(feed_units)
            battery_after = printer.get_battery()
            return PrintResult(
                model=self.model_id,
                address=resolved_address,
                operation=operation,
                dry_run=False,
                feed_mm=feed_mm,
                feed_units=feed_units,
                font_size=font_size,
                bytes_sent=len(bitstream),
                paragraph=paragraph,
                source_path=source_path,
                conversion=conversion,
                layout=layout,
                battery_after=battery_after,
                estimated_length_mm=estimated_length_mm,
                max_length_mm=max_length_mm,
                fits_length_limit=fits_length_limit,
                warning=warning,
                styling=styling,
            )
        finally:
            printer.disconnect()

    @staticmethod
    def _normalize_bluetooth_mac(value: str | None) -> str | None:
        if not value:
            return None

        normalized = value.strip().replace("-", ":").upper()
        if len(normalized) == 12 and all(char in "0123456789ABCDEF" for char in normalized):
            return ":".join(normalized[index:index + 2] for index in range(0, 12, 2))
        if len(normalized) == 17 and all(char in "0123456789ABCDEF:" for char in normalized):
            return normalized
        return value


def _is_usb_backend_error(exc: Exception) -> bool:
    return exc.__class__.__name__ == "NoBackendError" or "No backend available" in str(exc)


def _apply_p2_text_render_defaults(effective_style: dict[str, object], *, paragraph: bool) -> None:
    if effective_style.get("font_size") is None:
        effective_style["font_size"] = P2_DEFAULT_PARAGRAPH_FONT_SIZE if paragraph else P2_DEFAULT_TEXT_FONT_SIZE
    if effective_style.get("horizontal_padding_px") is None:
        effective_style["horizontal_padding_px"] = (
            P2_DEFAULT_PARAGRAPH_HORIZONTAL_PADDING_PX if paragraph else P2_DEFAULT_TEXT_HORIZONTAL_PADDING_PX
        )
    if effective_style.get("vertical_padding_px") is None:
        effective_style["vertical_padding_px"] = (
            P2_DEFAULT_PARAGRAPH_VERTICAL_PADDING_PX if paragraph else P2_DEFAULT_TEXT_VERTICAL_PADDING_PX
        )


def _style_value_with_default(
    effective_style: dict[str, object],
    key: str,
    configured_value: object | None,
    default_value: object,
) -> object:
    value = effective_style.get(key)
    if value is not None:
        return value
    if configured_value is not None:
        return configured_value
    return default_value


def _p2_usb_backend_error_message() -> str:
    return (
        "PyUSB cannot load a libusb backend for Paperang P2 USB. "
        "Install libusb-1.0 and a compatible WinUSB/Zadig driver for VID=0x4348 PID=0x5584, "
        "then run `paperang --json capabilities`."
    )


def _ensure_current_event_loop() -> None:
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


class _AutoBleP2Printer:
    def __init__(self, nus_printer, ff00_printer):
        self._nus_printer = nus_printer
        self._ff00_printer = ff00_printer
        self._active_printer = None

    def connect(self) -> bool:
        try:
            if self._nus_printer.connect():
                self._active_printer = self._nus_printer
                return True
        except Exception:
            self._disconnect_nus()

        if self._ff00_printer.connect():
            self._active_printer = self._ff00_printer
            return True
        return False

    def disconnect(self):
        if self._active_printer is not None:
            return self._active_printer.disconnect()
        self._disconnect_nus()
        return self._ff00_printer.disconnect()

    def __getattr__(self, name: str):
        if self._active_printer is None:
            raise AttributeError(name)
        return getattr(self._active_printer, name)

    def _disconnect_nus(self) -> None:
        try:
            self._nus_printer.disconnect()
        except Exception:
            pass
