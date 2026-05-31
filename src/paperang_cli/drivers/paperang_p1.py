"""Paperang P1 driver implementation."""

from __future__ import annotations

from pathlib import Path

from paperang_cli.drivers.base import PrinterDriver
from paperang_cli.errors import DriverError, PrinterNotFoundError, SafetyError
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus
from paperang_cli.render import (
    DEFAULT_COMPOSE_FONT_SIZE,
    DEFAULT_PARAGRAPH_FONT_SIZE,
    DEFAULT_TEXT_FONT_SIZE,
    feed_units_from_mm,
    render_composed_bitstream,
    render_image_bitstream,
    render_text_bitstream,
)

SELF_TEST_WARNING = "The built-in self-test consumes substantially more paper than normal text or image prints."
IMAGE_PRINT_WARNING = "Image printing is more experimental than text printing; conversion quality and physical output still need manual validation on real hardware."
COMPOSE_PRINT_WARNING = "Combined text-and-image printing uses the same image conversion path as image printing; validate physical output on real hardware before relying on the layout."


class PaperangP1Driver(PrinterDriver):
    model_id = "paperang_p1"
    transport = "ble"

    def discover(self) -> list[PrinterDevice]:
        from paperang_cli.protocol.hardware_bleak import discover_paperang_devices

        devices = discover_paperang_devices(self.settings.discovery_names)
        return [
            PrinterDevice(
                name=device.name or "Unknown",
                address=device.address,
                rssi=getattr(device, "rssi", None),
                details=str(getattr(device, "details", "")) or None,
            )
            for device in devices
        ]

    def status(self, address: str | None = None) -> PrinterStatus:
        printer = self._build_printer(address)
        if not printer.connected:
            raise PrinterNotFoundError("Unable to connect to a supported Paperang P1 printer")

        resolved_address = self._resolved_address(printer, address)
        try:
            firmware = self._payload_text(printer.queryVersionFromBt())
            serial = self._payload_text(printer.querySNFromBt())
            battery = self._payload_int(printer.queryBatteryStatus())
            hardware = self._payload_hex(printer.queryHardwareInfo())
            density = self._payload_int(printer.queryDensity())
            power_off = self._payload_int(printer.queryPowerOffTime())

            return PrinterStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self.transport,
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
                },
            )
        finally:
            printer.disconnect()

    def battery(self, address: str | None = None) -> BatteryStatus:
        printer = self._build_printer(address)
        if not printer.connected:
            raise PrinterNotFoundError("Unable to connect to a supported Paperang P1 printer")

        resolved_address = self._resolved_address(printer, address)
        try:
            battery = self._payload_int(printer.queryBatteryStatus())
            return BatteryStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self.transport,
                connected=True,
                battery_percent=battery,
            )
        finally:
            printer.disconnect()

    def bluetooth_mac(self, address: str | None = None) -> BluetoothMacStatus:
        printer = self._build_printer(address)
        if not printer.connected:
            raise PrinterNotFoundError("Unable to connect to a supported Paperang P1 printer")

        resolved_address = self._resolved_address(printer, address)
        try:
            bluetooth_mac = self._payload_mac(printer.queryBluetoothMac())
            return BluetoothMacStatus(
                model=self.model_id,
                address=resolved_address,
                transport=self.transport,
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
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        if not text:
            raise DriverError("Text content must not be empty")

        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)

        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        resolved_font_size = font_size
        if resolved_font_size is None:
            resolved_font_size = DEFAULT_PARAGRAPH_FONT_SIZE if paragraph else DEFAULT_TEXT_FONT_SIZE

        bitstream = render_text_bitstream(
            text,
            printer_width=self.settings.printerwidth,
            paragraph=paragraph,
            font_size=resolved_font_size,
        )
        return self._send_bitstream_job(
            bitstream=bitstream,
            operation="paragraph" if paragraph else "text",
            paragraph=paragraph,
            font_size=resolved_font_size,
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
        )

    def print_image(
        self,
        image_path: Path,
        *,
        conversion: str,
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)
        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        bitstream = render_image_bitstream(
            image_path,
            printer_width=self.settings.printerwidth,
            conversion=conversion,
        )
        return self._send_bitstream_job(
            bitstream=bitstream,
            operation="image",
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
            source_path=str(image_path),
            conversion=conversion,
            warning=IMAGE_PRINT_WARNING,
        )

    def print_compose(
        self,
        text: str,
        image_path: Path,
        *,
        layout: str,
        font_size: int | None,
        conversion: str,
        feed_mm: float | None,
        allow_paper_use: bool,
        dry_run: bool,
        address: str | None = None,
    ) -> PrintResult:
        if not text:
            raise DriverError("Text content must not be empty")

        self._require_paper_use(allow_paper_use=allow_paper_use, dry_run=dry_run)
        resolved_feed_mm = self.settings.post_print_feed_mm if feed_mm is None else feed_mm
        resolved_font_size = font_size or DEFAULT_COMPOSE_FONT_SIZE
        bitstream = render_composed_bitstream(
            text,
            image_path,
            printer_width=self.settings.printerwidth,
            font_size=resolved_font_size,
            conversion=conversion,
            layout=layout,
        )
        return self._send_bitstream_job(
            bitstream=bitstream,
            operation="compose",
            feed_mm=resolved_feed_mm,
            dry_run=dry_run,
            address=address,
            font_size=resolved_font_size,
            source_path=str(image_path),
            conversion=conversion,
            layout=layout,
            warning=COMPOSE_PRINT_WARNING,
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
                address=address or self.settings.macaddress or None,
                operation="self-test",
                dry_run=True,
                warning=SELF_TEST_WARNING,
            )

        if not allow_large_paper_use:
            raise SafetyError("Self-test consumes substantially more paper and requires --allow-large-paper-use")

        printer = self._build_printer(address)
        if not printer.connected:
            raise PrinterNotFoundError("Unable to connect to a supported Paperang P1 printer")

        resolved_address = self._resolved_address(printer, address)
        try:
            printer.sendSelfTestToBt()
            return PrintResult(
                model=self.model_id,
                address=resolved_address,
                operation="self-test",
                dry_run=False,
                warning=SELF_TEST_WARNING,
            )
        finally:
            printer.disconnect()

    def _build_printer(self, address: str | None):
        from paperang_cli.protocol.hardware_bleak import Paperang

        return Paperang(
            address or self.settings.macaddress or None,
            print_density=self.settings.print_density,
            post_print_feed_mm=self.settings.post_print_feed_mm,
            valid_names=self.settings.discovery_names,
        )

    @staticmethod
    def _resolved_address(printer, requested_address: str | None) -> str:
        return getattr(getattr(printer, "bleak_printer", None), "address", None) or requested_address or "unknown"

    def _require_paper_use(self, *, allow_paper_use: bool, dry_run: bool) -> None:
        if not dry_run and not allow_paper_use:
            raise SafetyError("Real printing requires --allow-paper-use")

    def _send_bitstream_job(
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
        warning: str | None = None,
    ) -> PrintResult:
        feed_units = feed_units_from_mm(feed_mm)

        if dry_run:
            return PrintResult(
                model=self.model_id,
                address=address or self.settings.macaddress or None,
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
                warning=warning,
            )

        printer = self._build_printer(address)
        if not printer.connected:
            raise PrinterNotFoundError("Unable to connect to a supported Paperang P1 printer")

        resolved_address = self._resolved_address(printer, address)
        try:
            result = printer.sendImageToBt(bitstream, feed_lines=feed_units)
            battery_after = self._payload_int(result)
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
                warning=warning,
            )
        finally:
            printer.disconnect()

    @staticmethod
    def _payload(result):
        if not result:
            return b""
        _, parsed_packets = result
        if not parsed_packets:
            return b""
        return bytes(parsed_packets[0].payload)

    @classmethod
    def _payload_int(cls, result):
        payload = cls._payload(result)
        if not payload:
            return None
        return int(payload[0])

    @classmethod
    def _payload_text(cls, result):
        payload = cls._payload(result)
        if not payload:
            return None
        decoded = payload.decode("ascii", errors="ignore").strip("\x00")
        if decoded and all(31 < ord(char) < 127 for char in decoded):
            return decoded
        return payload.hex()

    @classmethod
    def _payload_hex(cls, result):
        payload = cls._payload(result)
        if not payload:
            return None
        return payload.hex()

    @classmethod
    def _payload_mac(cls, result):
        payload = cls._payload(result)
        if not payload:
            return None

        decoded = payload.decode("ascii", errors="ignore").strip("\x00").strip()
        normalized = decoded.replace("-", ":").upper()
        if normalized:
            if len(normalized) == 12 and all(char in "0123456789ABCDEF" for char in normalized):
                return ":".join(normalized[index:index + 2] for index in range(0, 12, 2))
            if len(normalized) == 17 and all(char in "0123456789ABCDEF:" for char in normalized):
                return normalized

        if len(payload) == 6:
            return ":".join(f"{byte:02X}" for byte in payload)

        return payload.hex()