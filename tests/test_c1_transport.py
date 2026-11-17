import struct
import unittest
import zlib
from types import SimpleNamespace
from PIL import Image
from paperang_cli.protocol.c1_ble import C1Client, FrameParser


def response(command, payload):
    return struct.pack('<BBBH', 2, command, 0, len(payload)) + payload + struct.pack('<I', zlib.crc32(payload)) + b'\x03'


class Peer:
    def __init__(self, owner, reject=False):
        self.owner, self.reject = owner, reject
        self.parser = FrameParser()
        self.printed, self.feeds, self.fragments = [], [], []
        self.services = SimpleNamespace(get_characteristic=lambda uuid: SimpleNamespace(
            properties=['write-without-response'], max_write_without_response_size=117))

    async def write_gatt_char(self, uuid, data, response=True):
        self.fragments.append(len(data))
        for frame in self.parser.feed(data):
            cmd, payload = frame['command'], frame['payload']
            if cmd == 0:
                self.printed.append(payload)
                if self.reject:
                    self.owner._notification(None, globals()['response'](0, b'\x03'))
            elif cmd == 12:
                self.owner._notification(None, globals()['response'](13, b'\x00\x00') + globals()['response'](12, b'\x00'))
            elif cmd == 26:
                self.feeds.append(int.from_bytes(payload, 'little'))
                self.owner._notification(None, globals()['response'](26, b'\x00'))


class PrintingTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_multiframe_print_preserves_every_row(self):
        p = C1Client('aabbccddeeff')
        peer = Peer(p)
        p.client = peer
        bitmap = bytes(i % 256 for i in range(156 * 13))
        result = await p.print_bitmap(bitmap, speed='normal')
        self.assertEqual(b''.join(peer.printed), bitmap)
        self.assertEqual([len(v) for v in peer.printed], [936, 936, 156])
        self.assertLessEqual(max(peer.fragments), 100)
        self.assertEqual(peer.feeds, [180])
        self.assertEqual(result['sent_packets'], 3)
        self.assertEqual(result['status_checks'], 3)

    async def test_rejected_print_is_not_retried_or_followed_by_feed(self):
        p = C1Client('aabbccddeeff')
        peer = Peer(p, reject=True)
        p.client = peer
        with self.assertRaises(RuntimeError):
            await p.print_bitmap(bytes(156 * 12))
        self.assertEqual(len(peer.printed), 1)
        self.assertEqual(peer.feeds, [])

    async def test_fast_mode_keeps_order_and_checks_last_partial_batch(self):
        p = C1Client('aabbccddeeff')
        peer = Peer(p)
        p.client = peer
        bitmap = bytes(i % 251 for i in range(156 * 31))
        result = await p.print_bitmap(bitmap, speed='fast')
        self.assertEqual(b''.join(peer.printed), bitmap)
        self.assertEqual(result['sent_packets'], 6)
        self.assertEqual(result['status_checks'], 2)
        self.assertLessEqual(max(peer.fragments), 117)
        self.assertEqual(peer.feeds, [180])

    async def test_fast_mode_obeys_smaller_negotiated_write_size(self):
        p = C1Client('aabbccddeeff')
        peer = Peer(p)
        peer.services = SimpleNamespace(get_characteristic=lambda uuid: SimpleNamespace(
            properties=['write-without-response'], max_write_without_response_size=20))
        p.client = peer
        bitmap = bytes(156)
        await p.print_bitmap(bitmap, speed='fast')
        self.assertEqual(b''.join(peer.printed), bitmap)
        self.assertLessEqual(max(peer.fragments), 20)

