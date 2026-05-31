"""Shared data models for CLI and drivers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PrinterDevice:
    name: str
    address: str
    rssi: int | None = None
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PrinterStatus:
    model: str
    address: str
    transport: str
    connected: bool
    battery_percent: int | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
    hardware_info: str | None = None
    density: int | None = None
    power_off_time: int | None = None
    raw: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BatteryStatus:
    model: str
    address: str
    transport: str
    connected: bool
    battery_percent: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BluetoothMacStatus:
    model: str
    address: str
    transport: str
    connected: bool
    bluetooth_mac: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProbeResult:
    model: str
    address: str
    transport: str
    connected: bool
    battery_percent: int | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
    hardware_info: str | None = None
    density: int | None = None
    power_off_time: int | None = None
    bluetooth_mac: str | None = None
    local_transport_supported: bool = False
    local_transport_note: str | None = None
    raw: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PrintResult:
    model: str
    address: str | None
    operation: str
    dry_run: bool
    feed_mm: float | None = None
    feed_units: int | None = None
    font_size: int | None = None
    bytes_sent: int | None = None
    paragraph: bool | None = None
    source_path: str | None = None
    conversion: str | None = None
    layout: str | None = None
    battery_after: int | None = None
    warning: str | None = None
    styling: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)