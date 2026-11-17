"""C1 ISSC BLE transport; firmware 1.00.09, CRC32 seed zero. No automatic retries."""
import asyncio
import struct
import time
import zlib

WRITE_UUID = '49535343-6daa-4d02-abf6-19569aca69fe'
NOTIFY_UUID = '49535343-1e4d-4bd9-ba61-23c647249616'
FAST_WRITE_UUID = '49535343-8841-43f4-a8d4-ecbe34729bb3'
PRINT_PROFILES = {
    'normal': {'fragment': 100, 'response': True, 'delay': 0, 'packet_pause': 0.1, 'check_every': 1},
    'fast': {'fragment': 117, 'response': False, 'delay': 0.01, 'packet_pause': 0, 'check_every': 4},
}
QUERIES = {'model': 0x06, 'firmware': 0x04, 'serial': 0x0A,
           'bluetooth_id': 0x08, 'status': 0x0C, 'battery_percent': 0x10,
           'heat_density': 0x1C, 'power_down_seconds': 0x1F}


def pack_query(command):
    if command not in QUERIES.values():
        raise ValueError('Only documented read-only queries are allowed')
    payload = b'\x01'
    return struct.pack('<BBBH', 2, command, 0, len(payload)) + payload + struct.pack('<I', zlib.crc32(payload)) + b'\x03'


class FrameParser:
    """Handle fragmented notifications and multiple frames in one notification."""
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        frames = []
        while self.buffer:
            if self.buffer[0] != 2:
                del self.buffer[0]
                continue
            if len(self.buffer) < 5:
                break
            length = int.from_bytes(self.buffer[3:5], 'little')
            if length > 4096:
                self.buffer.clear()
                raise ValueError('Unexpected frame length')
            size = length + 10
            if len(self.buffer) < size:
                break
            packet = bytes(self.buffer[:size])
            del self.buffer[:size]
            payload = packet[5:5 + length]
            crc = int.from_bytes(packet[5 + length:9 + length], 'little')
            if packet[-1] != 3 or crc != zlib.crc32(payload):
                raise ValueError('Invalid response frame or CRC32')
            frames.append({'command': packet[1], 'sequence': packet[2], 'payload': payload})
        return frames


async def discover_c1(timeout=10):
    from bleak import BleakScanner
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    return [(device, adv) for device, adv in devices.values()
            if (adv.local_name or device.name or '') == 'Paperang_C1']


def select_device(devices, address=None):
    if address:
        normalized = address.replace(':', '').lower()
        devices = [(d, a) for d, a in devices if d.address.lower() == address.lower()
                   or any(v.hex() == normalized for v in a.manufacturer_data.values())]
    if len(devices) != 1:
        raise RuntimeError('Expected exactly one C1; use discover and specify --address')
    return devices[0][0]


class C1Client:
    def __init__(self, address=None, timeout=20):
        self.address = address
        self.timeout = timeout
        self.client = None
        self.parser = FrameParser()
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.trace = []
        self.device = None
        self.print_error = None

    async def __aenter__(self):
        from bleak import BleakClient
        self.device = select_device(await discover_c1(self.timeout), self.address)
        self.client = BleakClient(self.device, timeout=self.timeout)
        try:
            await self.client.connect()
            await self.client.start_notify(NOTIFY_UUID, self._notification)
            if await self.query('model') != b'C1':
                raise RuntimeError('Connected printer is not a C1')
        except BaseException:
            await self.client.disconnect()
            raise
        return self

    async def __aexit__(self, *_):
        if self.client:
            await self.client.disconnect()

    def _notification(self, _, data):
        self.trace.append({'direction': 'rx', 'hex': bytes(data).hex()})
        try:
            for frame in self.parser.feed(data):
                if frame['command'] == 0x00 and frame['payload'] != b'\x00':
                    self.print_error = RuntimeError(f'Bitmap rejected: {frame["payload"].hex()}')
                self.queue.put_nowait(frame)
        except ValueError as exc:
            self.queue.put_nowait(exc)

    async def query(self, name):
        async with self.lock:
            if self.print_error:
                raise self.print_error
            cmd = QUERIES[name]
            while not self.queue.empty():
                self.queue.get_nowait()
            packet = pack_query(cmd)
            self.trace.append({'direction': 'tx', 'query': name, 'hex': packet.hex()})
            await asyncio.wait_for(self.client.write_gatt_char(WRITE_UUID, packet, response=True), 5)
            result = None
            ack = None
            deadline = asyncio.get_running_loop().time() + 4
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break
                try:
                    frame = await asyncio.wait_for(self.queue.get(), remaining)
                except asyncio.TimeoutError:
                    break
                if isinstance(frame, Exception):
                    raise frame
                if self.print_error:
                    raise self.print_error
                if frame['command'] == cmd + 1:
                    result = frame['payload']
                elif frame['command'] == cmd:
                    ack = frame['payload']
                    if ack != b'\x00':
                        raise RuntimeError(f'{name}: device acknowledgement {ack.hex()}')
                if result is not None and ack is not None:
                    return result
            raise RuntimeError(f'{name}: incomplete response (data={result!r}, acknowledgement={ack!r})')

    async def print_command(self, command, payload, speed='normal'):
        """Send a bitmap or feed command; never retry an uncertain print."""
        if command not in (0x00, 0x1A):
            raise ValueError('Only bitmap and feed commands are supported')
        if speed not in PRINT_PROFILES:
            raise ValueError('Unknown speed profile')
        if not payload or len(payload) > 1000:
            raise ValueError('Print payload must be 1..1000 bytes')
        if command == 0x1A and (len(payload) != 2 or int.from_bytes(payload, 'little') > 600):
            raise ValueError('Feed must be 0..600 lines in uint16LE')
        async with self.lock:
            if self.print_error:
                raise self.print_error
            while not self.queue.empty():
                self.queue.get_nowait()
            packet = struct.pack('<BBBH', 2, command, 0, len(payload)) + payload + struct.pack('<I', zlib.crc32(payload)) + b'\x03'
            self.trace.append({'direction': 'tx', 'command': command, 'hex': packet.hex()})
            profile = PRINT_PROFILES[speed if command == 0 else 'normal']
            uuid = WRITE_UUID if profile['response'] else FAST_WRITE_UUID
            fragment = profile['fragment']
            if not profile['response']:
                characteristic = self.client.services.get_characteristic(uuid)
                if not characteristic or 'write-without-response' not in characteristic.properties:
                    raise RuntimeError('Fast BLE write characteristic unavailable; normal profile is available through the internal transport API')
                fragment = min(fragment, characteristic.max_write_without_response_size)
            for offset in range(0, len(packet), fragment):
                if self.print_error:
                    raise self.print_error
                await asyncio.wait_for(self.client.write_gatt_char(uuid, packet[offset:offset + fragment], response=profile['response']), 5)
                if profile['delay']:
                    await asyncio.sleep(profile['delay'])
            if command == 0x00:
                # Original Paperang implementations do not wait for a bitmap ACK.
                # A separate status query acts as a processing/connection barrier.
                if profile['packet_pause']:
                    await asyncio.sleep(profile['packet_pause'])
                return
            deadline = asyncio.get_running_loop().time() + 10
            while (remaining := deadline - asyncio.get_running_loop().time()) > 0:
                frame = await asyncio.wait_for(self.queue.get(), remaining)
                if isinstance(frame, Exception):
                    raise frame
                if frame['command'] == command:
                    if frame['payload'] != b'\x00':
                        raise RuntimeError(f'Print command {command:02x}: acknowledgement {frame["payload"].hex()}')
                    return
            raise RuntimeError('Print acknowledgement missing; do not resend automatically')

    async def print_bitmap(self, bitmap, width=1248, feed=180, speed='fast'):
        if speed not in PRINT_PROFILES:
            raise ValueError('Unknown speed profile')
        if width <= 0 or width % 8 or width > 1600:
            raise ValueError('Width must be a multiple of 8 up to 1600')
        row_bytes = width // 8
        if not bitmap or len(bitmap) % row_bytes:
            raise ValueError('Bitmap must contain complete rows')
        if len(bitmap) // row_bytes > 3600:
            raise ValueError('Limit each job to 3600 rows')
        if not 0 <= feed <= 600:
            raise ValueError('Feed must be between 0 and 600')
        packet_size = (1000 // row_bytes) * row_bytes
        count = 0
        checks = 0
        started = time.monotonic()
        for offset in range(0, len(bitmap), packet_size):
            await self.print_command(0x00, bitmap[offset:offset + packet_size], speed=speed)
            count += 1
            if count % PRINT_PROFILES[speed]['check_every'] == 0 or offset + packet_size >= len(bitmap):
                status = await self.query('status')
                checks += 1
                if status != b'\x00\x00':
                    raise RuntimeError(f'Printer status changed during printing: {status.hex()}')
        data_seconds = time.monotonic() - started
        if feed:
            await self.print_command(0x1A, struct.pack('<H', feed))
        return {'sent_packets': count, 'status_checks': checks, 'speed': speed,
                'data_send_seconds': round(data_seconds, 3),
                'job_seconds_to_feed_ack': round(time.monotonic() - started, 3), 'width_dots': width,
                'height_rows': len(bitmap) // row_bytes, 'feed_lines': feed,
                'physical_output_verified': False}

