from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrintResult, PrinterDevice, PrinterStatus


class FakeDriver:
    def __init__(self):
        self.calls = []

    def discover(self):
        self.calls.append(("discover", {}))
        return [PrinterDevice(name="Paperang", address="AA:BB:CC:DD:EE:FF", rssi=-42)]

    def status(self, address=None):
        self.calls.append(("status", {"address": address}))
        return PrinterStatus(
            model="paperang_p1",
            address=address or "AA:BB:CC:DD:EE:FF",
            transport="ble",
            connected=True,
            battery_percent=88,
            serial_number="P100TEST",
            firmware_version="010203",
            hardware_info="00010203",
            density=75,
            power_off_time=88,
        )

    def battery(self, address=None):
        self.calls.append(("battery", {"address": address}))
        return BatteryStatus(
            model="paperang_p1",
            address=address or "AA:BB:CC:DD:EE:FF",
            transport="ble",
            connected=True,
            battery_percent=88,
        )

    def bluetooth_mac(self, address=None):
        self.calls.append(("bluetooth_mac", {"address": address}))
        return BluetoothMacStatus(
            model="paperang_p1",
            address=address or "AA:BB:CC:DD:EE:FF",
            transport="ble",
            connected=True,
            bluetooth_mac="AA:BB:CC:DD:EE:FF",
        )

    def print_text(self, text, **kwargs):
        self.calls.append(("print_text", {"text": text, **kwargs}))
        return PrintResult(
            model="paperang_p1",
            address=kwargs.get("address") or "AA:BB:CC:DD:EE:FF",
            operation="paragraph" if kwargs["paragraph"] else "text",
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"] if kwargs["feed_mm"] is not None else 5.0,
            feed_units=280,
            font_size=kwargs["font_size"] or 36,
            bytes_sent=1024,
            paragraph=kwargs["paragraph"],
            battery_after=87,
        )

    def print_image(self, image_path, **kwargs):
        self.calls.append(("print_image", {"image_path": str(image_path), **kwargs}))
        return PrintResult(
            model="paperang_p1",
            address=kwargs.get("address") or "AA:BB:CC:DD:EE:FF",
            operation="image",
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"] if kwargs["feed_mm"] is not None else 5.0,
            feed_units=280,
            bytes_sent=2048,
            source_path=str(image_path),
            conversion=kwargs["conversion"],
            battery_after=87,
            warning="Image printing is more experimental than text printing; conversion quality and physical output still need manual validation on real hardware.",
        )

    def print_compose(self, text, image_path, **kwargs):
        self.calls.append(("print_compose", {"text": text, "image_path": str(image_path), **kwargs}))
        return PrintResult(
            model="paperang_p1",
            address=kwargs.get("address") or "AA:BB:CC:DD:EE:FF",
            operation="compose",
            dry_run=kwargs["dry_run"],
            feed_mm=kwargs["feed_mm"] if kwargs["feed_mm"] is not None else 5.0,
            feed_units=280,
            font_size=kwargs["font_size"] or 28,
            bytes_sent=3072,
            source_path=str(image_path),
            conversion=kwargs["conversion"],
            layout=kwargs["layout"],
            battery_after=87,
            warning="Combined text-and-image printing uses the same image conversion path as image printing; validate physical output on real hardware before relying on the layout.",
        )

    def self_test(self, **kwargs):
        self.calls.append(("self_test", kwargs))
        return PrintResult(
            model="paperang_p1",
            address=kwargs.get("address") or "AA:BB:CC:DD:EE:FF",
            operation="self-test",
            dry_run=kwargs["dry_run"],
            warning="The built-in self-test consumes substantially more paper than normal text or image prints.",
        )


@pytest.fixture
def fake_driver():
    return FakeDriver()