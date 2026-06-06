"""Paperang P2 FF00 BLE profile support."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import struct
import zlib

from bleak import BleakClient, BleakScanner

from ..errors import DriverError
from .hardware_bleak import prepare_bleak_windows_thread

FF00_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
FF00_WRITE_CHAR_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
FF00_NOTIFY_CHAR_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
FF00_STATUS_NOTIFY_CHAR_UUID = "0000ff03-0000-1000-8000-00805f9b34fb"
GAP_DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"

UNSUPPORTED_SELF_TEST_MESSAGE = (
    "This Paperang P2 exposes the FF00 BLE profile, not the upstream NUS BLE profile. "
    "Discovery, diagnostics, and raster printing are implemented for FF00/A5, but the built-in self-test command "
    "is not yet mapped for this profile."
)

A5_CRC_SEED = 0x35769521
A5_PREFIX = bytes([0xA5, 0x01])
A5_SUFFIX = 0x5A
A5_START_RASTER_PAYLOAD = bytes([0x05, 0x19, 0x01, 0x00, 0x00])
A5_STATUS_PAYLOAD = bytes([0x05, 0x0F, 0x01, 0x00, 0x00, 0x00])
A5_MAX_FRAME_SIZE = 237
A5_PRINT_DATA_FRAME_OVERHEAD = 26
A5_RASTER_WRITE_PAUSE_SECONDS = 0.01


class PaperangP2Ff00:
    """Adapter for P2 devices exposing the FF00 BLE profile."""

    profile_name = "ff00"

    def __init__(self, address: str | None = None, *, name: str = "Paperang_P2"):
        self.address = address
        self.name = name
        self.connected = False
        self._client: BleakClient | None = None
        self._device_name: str | None = None
        self._last_notifications: list[bytes] = []
        self._a5_supported = False
        self._last_a5_response: A5Frame | None = None
        self._version: str | None = None
        self._sn: str | None = None
        self._capability_text: str | None = None
        self._last_width_bytes = 72

    def connect(self) -> bool:
        return self._run_async(self._connect())

    def disconnect(self) -> None:
        self._run_async(self._disconnect())

    def get_version(self) -> str | None:
        if self._version is None:
            self._version = self._run_async(self._query_a5_text(0x01, 0x15))
        return self._version

    def get_sn(self) -> str | None:
        if self._sn is None:
            self._sn = self._run_async(self._query_a5_text(0x01, 0x02))
        return self._sn

    def get_battery(self) -> int | None:
        response = self._run_async(self._query_a5(0x01, 0x0B))
        if response is None:
            return None
        values = parse_a5_tlv_args(response.args)
        raw_value = values.get(0x01)
        if raw_value is None or len(raw_value) < 2:
            return None
        return int(struct.unpack("<H", raw_value[:2])[0] / 10)

    def get_hw_info(self) -> str:
        protocol = "a5" if self._a5_supported else "unknown"
        parts = [
            "BLE profile ff00 service=0000ff00 write=ff02 notify=ff01 status_notify=ff03 "
            f"protocol={protocol}"
        ]
        version = self.get_version() if self._a5_supported else None
        sn = self.get_sn() if self._a5_supported else None
        if version:
            parts.append(f"version={version}")
        if sn:
            parts.append(f"sn={sn}")
        return " ".join(parts)

    def get_heat_density(self) -> int | None:
        return None

    def get_power_down_time(self) -> int | None:
        return None

    def get_model(self) -> str:
        if self._capability_text is None and self._a5_supported:
            self._capability_text = self._run_async(self._query_a5_text(0x01, 0x01))
        if self._capability_text:
            name = _json_string_value(self._capability_text, "DevName")
            if name:
                return name
        return self._device_name or self.name or "Paperang_P2"

    def get_bt_mac(self) -> str | None:
        return None

    def set_paper_type(self, _paper_type: int) -> None:
        paper_type = max(0, min(255, int(_paper_type)))
        self._run_async(self._send_a5_payload(bytes([0x05, 0x2F, 0x01, 0x00, 0x00])))
        self._run_async(self._send_a5_payload(bytes([0x05, 0x20, 0x03, 0x02, 0x00, paper_type, 0x00])))

    def set_heat_density(self, _density: int) -> None:
        density = max(0, min(100, int(_density)))
        self._run_async(self._send_a5_payload(bytes([0x05, 0x11, 0x03, 0x02, 0x00, density, 0x00])))

    def print_bitmap(self, bitmap_data: bytes, width_bytes: int = 72) -> None:
        if width_bytes <= 0:
            raise DriverError("Paperang P2 FF00/A5 width_bytes must be greater than zero")
        if len(bitmap_data) % width_bytes != 0:
            raise DriverError("Paperang P2 FF00/A5 bitmap length must be a whole number of rows")
        if not bitmap_data:
            return

        self._last_width_bytes = width_bytes
        self._run_async(self._print_bitmap(bitmap_data, width_bytes=width_bytes))

    def feed(self, feed_units: int) -> None:
        rows = a5_feed_rows_from_units(feed_units)
        if rows <= 0:
            return
        self._run_async(self._print_bitmap(bytes(rows * self._last_width_bytes), width_bytes=self._last_width_bytes))

    def print_test_page(self) -> None:
        raise DriverError(UNSUPPORTED_SELF_TEST_MESSAGE)

    async def _connect(self) -> bool:
        prepare_bleak_windows_thread()
        if self.address is None:
            self.address = await self._scan_for_address()
        if self.address is None:
            return False

        client = BleakClient(self.address, timeout=20.0)
        await client.connect()
        if not client.is_connected:
            return False

        service = client.services.get_service(FF00_SERVICE_UUID)
        if service is None:
            await client.disconnect()
            return False

        self._client = client
        self.connected = True
        self._device_name = await self._read_device_name()
        await self._start_notify_if_available(FF00_NOTIFY_CHAR_UUID)
        await self._start_notify_if_available(FF00_STATUS_NOTIFY_CHAR_UUID)
        await asyncio.sleep(0.2)
        await self._probe_a5_protocol()
        return True

    async def _disconnect(self) -> None:
        client = self._client
        self._client = None
        self.connected = False
        if client and client.is_connected:
            try:
                await client.stop_notify(FF00_NOTIFY_CHAR_UUID)
            except Exception:
                pass
            try:
                await client.stop_notify(FF00_STATUS_NOTIFY_CHAR_UUID)
            except Exception:
                pass
            await client.disconnect()

    async def _scan_for_address(self) -> str | None:
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            if device.name == self.name:
                return device.address
        return None

    async def _read_device_name(self) -> str | None:
        if not self._client:
            return None
        try:
            value = await self._client.read_gatt_char(GAP_DEVICE_NAME_UUID)
        except Exception:
            return None
        decoded = bytes(value).decode("ascii", errors="ignore").strip("\x00").strip()
        return decoded or None

    async def _start_notify_if_available(self, uuid: str) -> None:
        if not self._client:
            return
        try:
            await self._client.start_notify(uuid, self._notification_handler)
        except Exception:
            pass

    def _notification_handler(self, _sender, data: bytearray) -> None:
        self._last_notifications.append(bytes(data))

    async def _query(self, command: bytes) -> bytes | None:
        if not self._client or not self._client.is_connected:
            return None
        self._last_notifications.clear()
        await self._client.write_gatt_char(FF00_WRITE_CHAR_UUID, command, response=False)
        await asyncio.sleep(0.6)
        for item in reversed(self._last_notifications):
            if item not in (b"\x01\x01", b"\x01\x04", b"\x02\xaa\x00"):
                return item
        return None

    async def _probe_a5_protocol(self) -> None:
        command = await self._query_a5(0x05, 0x19)
        if command is None or not is_a5_success_response(command):
            return
        self._a5_supported = True

    async def _query_a5_text(self, domain: int, command: int, args: bytes = b"") -> str | None:
        response = await self._query_a5(domain, command, args)
        if response is None:
            return None
        return first_a5_text_value(response.args)

    async def _query_a5(self, domain: int, command: int, args: bytes = b"") -> "A5Payload | None":
        payload = build_a5_payload(domain, command, args)
        response = await self._query(pack_a5_frame(payload))
        if response is None:
            return None
        frame = parse_a5_frame(response)
        if frame is None:
            return None
        self._last_a5_response = frame
        command_response = parse_a5_payload(frame.payload)
        if command_response is None:
            return None
        return command_response

    async def _send_a5_ack(self, domain: int, command: int, args: bytes = b"") -> None:
        response = await self._query_a5(domain, command, args)
        if response is None or not is_a5_success_response(response):
            raise DriverError(f"Paperang P2 FF00/A5 command 0x{domain:02x}/0x{command:02x} did not acknowledge")

    async def _send_a5_payload(self, payload: bytes, *, delay: float = 0.25) -> bytes | None:
        response = await self._query(pack_a5_frame(payload))
        if response is not None:
            return response
        await asyncio.sleep(delay)
        return None

    async def _write_a5_payload(self, payload: bytes, *, pause: float = A5_RASTER_WRITE_PAUSE_SECONDS) -> None:
        if not self._client or not self._client.is_connected:
            raise DriverError("Paperang P2 FF00/A5 printer is not connected")
        await self._client.write_gatt_char(FF00_WRITE_CHAR_UUID, pack_a5_frame(payload), response=False)
        if pause > 0:
            await asyncio.sleep(pause)

    async def _wait_ready(self) -> None:
        await self._send_a5_payload(A5_STATUS_PAYLOAD, delay=0.4)

    async def _print_bitmap(self, bitmap_data: bytes, *, width_bytes: int) -> None:
        await self._wait_ready()
        await self._send_a5_payload(A5_START_RASTER_PAYLOAD)
        chunk_number = 1
        chunk_size = a5_print_chunk_size(width_bytes)
        for offset in range(0, len(bitmap_data), chunk_size):
            chunk = bitmap_data[offset : offset + chunk_size]
            is_final = offset + chunk_size >= len(bitmap_data)
            await self._write_a5_payload(
                build_a5_print_data_payload(
                    chunk,
                    chunk_number=chunk_number,
                    width_bytes=width_bytes,
                    final=is_final,
                ),
            )
            chunk_number += 1
        await self._send_a5_payload(build_a5_finish_payload(), delay=0.8)

    @staticmethod
    def _run_async(coroutine):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)


@dataclass(frozen=True)
class A5Frame:
    """Parsed Paperang P2 A5 protocol frame."""

    payload: bytes
    crc: int


@dataclass(frozen=True)
class A5Payload:
    """Parsed Paperang P2 A5 command payload."""

    domain: int
    command: int
    kind: int
    args: bytes


def pack_a5_frame(payload: bytes) -> bytes:
    """Pack an A5/5A Paperang P2 protocol frame."""

    crc = zlib.crc32(payload, A5_CRC_SEED) & 0xFFFFFFFF
    return A5_PREFIX + struct.pack("<H", len(payload)) + payload + struct.pack("<I", crc) + bytes([A5_SUFFIX])


def build_a5_payload(domain: int, command: int, args: bytes = b"", *, kind: int = 0x01) -> bytes:
    """Build the inner Paperang P2 A5 command payload."""

    return bytes([domain & 0xFF, command & 0xFF, kind & 0xFF]) + struct.pack("<H", len(args)) + bytes(args)


def build_a5_print_data_payload(
    data: bytes,
    *,
    chunk_number: int,
    width_bytes: int,
    final: bool,
) -> bytes:
    """Build a RawBT-style Paperang P2 A5 raster data payload."""

    chunk = bytes(data)
    args = (
        struct.pack("<H", chunk_number)
        + struct.pack("<H", len(chunk) + 8)
        + bytes([0x01, width_bytes & 0xFF, 0x00, 0x00, 0x00, 0x00])
        + struct.pack("<H", len(chunk))
        + chunk
    )
    return build_a5_payload(0x05, 0x1B, args, kind=0x03 if final else 0x01)


def a5_print_chunk_size(width_bytes: int) -> int:
    """Return a row-aligned raster chunk size that fits a single BLE write."""

    if width_bytes <= 0:
        raise ValueError("width_bytes must be greater than zero")
    max_data = A5_MAX_FRAME_SIZE - A5_PRINT_DATA_FRAME_OVERHEAD
    rows_per_chunk = max(1, max_data // width_bytes)
    return rows_per_chunk * width_bytes


def a5_feed_rows_from_units(feed_units: int) -> int:
    """Convert calibrated CLI feed units into approximate P2 raster feed rows."""

    return max(0, int(round(feed_units / 7)))


def build_a5_finish_payload() -> bytes:
    """Build the RawBT-style Paperang P2 A5 print finish payload."""

    return bytes([0x05, 0x22, 0x01, 0x02, 0x00, 0x00, 0x00])


def parse_a5_frame(packet: bytes) -> A5Frame | None:
    """Parse and verify an A5/5A Paperang P2 protocol frame."""

    if len(packet) < 9:
        return None
    if not packet.startswith(A5_PREFIX) or packet[-1] != A5_SUFFIX:
        return None
    payload_length = struct.unpack("<H", packet[2:4])[0]
    expected_length = 2 + 2 + payload_length + 4 + 1
    if len(packet) != expected_length:
        return None
    payload_start = 4
    payload_end = payload_start + payload_length
    payload = packet[payload_start:payload_end]
    packet_crc = struct.unpack("<I", packet[payload_end : payload_end + 4])[0]
    computed_crc = zlib.crc32(payload, A5_CRC_SEED) & 0xFFFFFFFF
    if packet_crc != computed_crc:
        return None
    return A5Frame(payload=payload, crc=packet_crc)


def parse_a5_payload(payload: bytes) -> A5Payload | None:
    """Parse the inner Paperang P2 A5 command payload."""

    if len(payload) < 5:
        return None
    args_length = struct.unpack("<H", payload[3:5])[0]
    if len(payload) != 5 + args_length:
        return None
    return A5Payload(domain=payload[0], command=payload[1], kind=payload[2], args=payload[5:])


def parse_a5_tlv_args(args: bytes) -> dict[int, bytes]:
    """Parse simple type/length/value fields used by A5 diagnostic responses."""

    values: dict[int, bytes] = {}
    offset = 0
    while offset + 3 <= len(args):
        tag = args[offset]
        length = struct.unpack("<H", args[offset + 1 : offset + 3])[0]
        value_start = offset + 3
        value_end = value_start + length
        if value_end > len(args):
            break
        values[tag] = args[value_start:value_end]
        offset = value_end
    return values


def first_a5_text_value(args: bytes) -> str | None:
    """Return the first printable text value from A5 TLV response arguments."""

    for value in parse_a5_tlv_args(args).values():
        decoded = value.decode("utf-8", errors="ignore").strip("\x00").strip()
        if decoded:
            return decoded
    return None


def is_a5_success_response(response: A5Payload) -> bool:
    """Return true for the success ACK TLV used by FF00/A5 control commands."""

    return response.kind == 0x02 and parse_a5_tlv_args(response.args).get(0x01) == b""


def _json_string_value(text: str, key: str) -> str | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, str) and value else None
