import unittest
from paperang_cli.protocol.c1_ble import FrameParser, pack_query

# Actual C1 notification: model response followed by success acknowledgement.
MODEL = bytes.fromhex('02070002004331030e53cb030206000100008def02d203')
BATTERY = bytes.fromhex('021100010064cc4add98030210000100008def02d203')

class ProtocolTests(unittest.TestCase):
    def test_every_fragment_boundary(self):
        for split in range(len(MODEL) + 1):
            parser = FrameParser()
            frames = parser.feed(MODEL[:split]) + parser.feed(MODEL[split:])
            self.assertEqual([(f['command'], f['payload']) for f in frames], [(7, b'C1'), (6, b'\x00')])

    def test_coalesced_notifications(self):
        frames = FrameParser().feed(MODEL + BATTERY)
        self.assertEqual(len(frames), 4)
        self.assertEqual(frames[2]['payload'], b'\x64')

    def test_corrupted_response_rejected(self):
        data = bytearray(BATTERY)
        data[5] ^= 1
        with self.assertRaises(ValueError):
            FrameParser().feed(data)

    def test_query_matches_successful_hardware_packet(self):
        self.assertEqual(pack_query(6).hex(), '0206000100011bdf05a503')

    def test_write_commands_are_not_exposed(self):
        for cmd in (0, 2, 3, 20, 24, 25, 26, 27):
            with self.assertRaises(ValueError):
                pack_query(cmd)

if __name__ == '__main__':
    unittest.main()
