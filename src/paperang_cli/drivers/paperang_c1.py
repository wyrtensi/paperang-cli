"""C1 BLE driver using the existing rendering and paper-use gates."""
import asyncio
import math

from paperang_cli.drivers.paperang_p1 import PaperangP1Driver
from paperang_cli.errors import DriverError
from paperang_cli.models import BatteryStatus, BluetoothMacStatus, PrinterDevice, PrinterStatus, PrintResult
from paperang_cli.protocol.c1_ble import C1Client, discover_c1


def run(coro):
    try:
        return asyncio.run(asyncio.wait_for(coro, 180))
    except Exception as exc:
        raise DriverError(str(exc) or type(exc).__name__) from exc


class PaperangC1Driver(PaperangP1Driver):
    model_id = 'paperang_c1'

    def __init__(self, settings):
        super().__init__(settings)
        settings.validate()
        if settings.printerwidth != 1248:
            raise DriverError('C1 requires 1248-dot rendering')

    def local_transport_note(self):
        return 'C1 supports BLE only; USB, CUPS and AirPrint are not implemented.'

    def discover(self):
        return [PrinterDevice(name=d.name or a.local_name, address=d.address, rssi=a.rssi)
                for d, a in run(discover_c1())]

    async def _query(self, address, names):
        async with C1Client(address or self.settings.macaddress or None) as client:
            values = {name: await client.query(name) for name in names}
            return client.device.address, values

    def status(self, address=None):
        actual, values = run(self._query(address, ['status', 'firmware', 'serial',
                            'battery_percent', 'heat_density', 'power_down_seconds']))
        fw = values['firmware']
        firmware = f'{fw[2]}.{fw[1]:02d}.{fw[0]:02d}' if len(fw) == 3 else fw.hex()
        return PrinterStatus(model=self.model_id, address=actual, transport='ble', connected=True,
            battery_percent=int.from_bytes(values['battery_percent'], 'little'),
            serial_number=values['serial'].decode('ascii', errors='replace'), firmware_version=firmware,
            density=int.from_bytes(values['heat_density'], 'little'),
            power_off_time=int.from_bytes(values['power_down_seconds'], 'little'),
            raw={'status': values['status'].hex()})

    def battery(self, address=None):
        actual, values = run(self._query(address, ['battery_percent']))
        return BatteryStatus(self.model_id, actual, 'ble', True,
                             int.from_bytes(values['battery_percent'], 'little'))

    def bluetooth_mac(self, address=None):
        actual, values = run(self._query(address, ['bluetooth_id']))
        raw = values['bluetooth_id'].decode('ascii').strip('\x00').replace(':', '').upper()
        if len(raw) != 12 or any(c not in '0123456789ABCDEF' for c in raw):
            raise DriverError('Unexpected C1 Bluetooth ID response')
        return BluetoothMacStatus(self.model_id, actual, 'ble', True,
                                  ':'.join(raw[i:i+2] for i in range(0, 12, 2)))

    def self_test(self, **kwargs):
        raise DriverError('C1 built-in self-test is unverified and unsupported, including dry-run')

    def _build_printer(self, address):
        raise DriverError('C1 must use its own BLE transport')

    async def _print(self, address, bitstream, feed):
        async with C1Client(address or self.settings.macaddress or None) as client:
            if await client.query('status') != b'\x00\x00':
                raise DriverError('C1 is not ready')
            await client.print_bitmap(bitstream, width=1248, feed=feed)
            if await client.query('status') != b'\x00\x00':
                raise DriverError('C1 status changed after printing; do not retry automatically')
            return client.device.address

    def _send_bitstream_job(self, *, bitstream, operation, feed_mm, dry_run, address, **metadata):
        if not bitstream or len(bitstream) % 156 or len(bitstream) > 156 * 3600:
            raise DriverError('C1 jobs must contain complete 1248-dot rows, at most 3600 rows')
        if not math.isfinite(feed_mm) or not 0 <= feed_mm <= 50:
            raise DriverError('C1 feed must be 0..50 mm (nominal calibration)')
        feed = round(feed_mm * 12)
        actual = address or self.settings.macaddress or None
        if not dry_run:
            actual = run(self._print(address, bitstream, feed))
        return PrintResult(model=self.model_id, address=actual, operation=operation,
                           dry_run=dry_run, feed_mm=feed_mm, feed_units=feed,
                           bytes_sent=len(bitstream), **metadata)
