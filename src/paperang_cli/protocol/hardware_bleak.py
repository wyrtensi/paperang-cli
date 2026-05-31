#!/usr/bin/python3
# -*-coding:utf-8-*-

import struct
import zlib
import logging
import asyncio
import codecs
import sys
from platform import system
from bleak import BleakClient, BleakScanner
from paperang_cli.protocol.const import BtCommandByte

try:
    from bleak.backends.winrt.util import uninitialize_sta
except ImportError:
    uninitialize_sta = None

# Paperang Service and Characteristic UUIDs
PAPERANG_SERVICE_UUID = "49535343-FE7D-4AE5-8FA9-9FAFD205E455"
PAPERANG_WRITE_CHAR_UUID = "49535343-8841-43F4-A8D4-ECBE34729BB3"
PAPERANG_NOTIFY_CHAR_UUID = "49535343-1E4D-4BD9-BA61-23C647249616"
DEFAULT_DEVICE_NAMES = ["MiaoMiaoJi", "Paperang", "Paperang_P2S"]


def prepare_bleak_windows_thread():
    if sys.platform != "win32" or uninitialize_sta is None:
        return

    try:
        uninitialize_sta()
    except Exception:
        # If the current thread is already in a usable state, keep going.
        pass


async def async_discover_paperang_devices(valid_names=None):
    prepare_bleak_windows_thread()
    names = valid_names or DEFAULT_DEVICE_NAMES
    devices = await BleakScanner.discover()
    return [device for device in devices if device.name in names]


def discover_paperang_devices(valid_names=None):
    return asyncio.run(async_discover_paperang_devices(valid_names=valid_names))

class PaperangBleak:
    standardKey = 0x35769521
    padding_line = 300
    max_send_msg_length = 1536
    max_recv_msg_length = 1024
    feed_units_per_mm = 56

    def __init__(self, address=None, print_density=75, post_print_feed_mm=5.0, valid_names=None):
        self.address = address
        self.print_density = print_density
        self.post_print_feed_mm = post_print_feed_mm
        self.valid_names = valid_names or list(DEFAULT_DEVICE_NAMES)
        self.crckeyset = False
        self.client = None
        self.connected = False
        self.response_data = bytearray()
        self.notification_event = asyncio.Event()

    async def ensure_connected(self, force_reconnect=False):
        if not force_reconnect and self.client and self.client.is_connected and self.connected:
            return True

        if force_reconnect:
            await self.disconnect()

        if self.client and self.client.is_connected:
            self.connected = True
            return True

        return await self.connect()

    async def connect(self):
        """Connect to the Paperang device"""
        try:
            prepare_bleak_windows_thread()
            if self.address is None:
                await self.scan_devices()
                if self.address is None:
                    logging.error("Could not find a Paperang device")
                    return False

            logging.info(f"Connecting to Paperang at {self.address}...")
            self.crckeyset = False
            self.response_data.clear()
            self.notification_event.clear()
            self.client = BleakClient(self.address)
            await self.client.connect()
            self.connected = self.client.is_connected

            if self.connected:
                logging.info("Connected successfully")

                # Set up notification handler
                await self.client.start_notify(
                    PAPERANG_NOTIFY_CHAR_UUID,
                    self.notification_handler
                )

                # On Windows/Bleak the notification callback can lag slightly
                # behind start_notify(), so give the stack a brief moment before
                # the first command/response handshake.
                await asyncio.sleep(0.2)

                # Register CRC key
                await self.registerCrcKeyToBt()
                await self.initializeAfterConnect()
                return True
            else:
                logging.error("Failed to connect")
                return False

        except Exception as e:
            logging.error(f"Error connecting to device: {str(e)}")
            return False

    def notification_handler(self, sender, data):
        """Handle notifications from the Paperang device"""
        logging.info(f"Received notification: {data.hex()}")
        self.response_data.extend(data)
        self.notification_event.set()

    async def disconnect(self):
        """Disconnect from the Paperang device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self.connected = False
        self.client = None
        self.crckeyset = False
        self.response_data.clear()
        self.notification_event.clear()
        logging.info("Disconnected from device")

    async def scan_devices(self):
        """Scan for Paperang devices"""
        logging.info("Scanning for Paperang devices...")

        devices = await BleakScanner.discover()
        for device in devices:
            if device.name in self.valid_names:
                logging.info(f"Found Paperang device: {device.name} [{device.address}]")
                self.address = device.address
                return True

        logging.error(f"No Paperang devices found. Looking for devices named: {', '.join(self.valid_names)}")
        return False

    def crc32(self, content):
        """Calculate CRC32 value"""
        return zlib.crc32(content, self.crcKey if self.crckeyset else self.standardKey) & 0xffffffff

    def packPerBytes(self, data_bytes, control_command, i):
        """Package bytes for sending to the printer"""
        result = struct.pack('<BBB', 2, control_command, i)
        result += struct.pack('<H', len(data_bytes))
        result += data_bytes
        result += struct.pack('<I', self.crc32(data_bytes))
        result += struct.pack('<B', 3)
        return result

    def addBytesToList(self, data_bytes):
        """Split data into chunks of max_send_msg_length"""
        length = self.max_send_msg_length
        result = [data_bytes[i:i + length] for i in range(0, len(data_bytes), length)]
        return result

    async def sendToBt(self, data_bytes, control_command, need_reply=True):
        """Send data to the Paperang device"""
        if not await self.ensure_connected():
            logging.error("Not connected to device")
            return None

        bytes_list = self.addBytesToList(data_bytes)
        for i, byte_chunk in enumerate(bytes_list):
            packet = self.packPerBytes(byte_chunk, control_command, i)
            for attempt in range(2):
                try:
                    # Clear any previous data
                    self.response_data.clear()
                    self.notification_event.clear()

                    # Send data
                    await self.client.write_gatt_char(PAPERANG_WRITE_CHAR_UUID, packet)
                    logging.info(f"Sent packet {i+1}/{len(bytes_list)} with length {len(packet)}")

                    # Wait for response if needed
                    if need_reply:
                        try:
                            # Wait for notification or timeout
                            await asyncio.wait_for(self.notification_event.wait(), timeout=2.0)

                            # Parse the response
                            if self.response_data:
                                parsed = self.resultParser(bytes(self.response_data))
                                logging.info(f"Received {len(parsed)} packets")
                                return bytes(self.response_data), parsed
                        except asyncio.TimeoutError:
                            logging.warning("No response received (timeout)")
                    break

                except Exception as e:
                    if attempt == 0:
                        logging.warning(f"Error sending data, trying one reconnect: {str(e)}")
                        if await self.ensure_connected(force_reconnect=True):
                            continue
                    logging.error(f"Error sending data: {str(e)}")
                    return None

        return None

    def resultParser(self, data):
        """Parse the response from the Paperang device"""
        base = 0
        res = []

        while base < len(data) and data[base] == 2:  # 0x02 is STX (Start of Text)
            class Info(object):
                def __str__(self):
                    return "\nControl command: %s(%s)\nPayload length: %d\nPayload(hex): %s" % (
                        self.command, BtCommandByte.findCommand(self.command)
                        , self.payload_length, codecs.encode(self.payload, "hex_codec")
                    )

            info = Info()
            _, info.command, _, info.payload_length = struct.unpack('<BBBH', data[base:base + 5])
            info.payload = data[base + 5: base + 5 + info.payload_length]
            info.crc32 = data[base + 5 + info.payload_length: base + 9 + info.payload_length]
            base += 10 + info.payload_length
            res.append(info)

        return res

    async def registerCrcKeyToBt(self, key=0x6968634 ^ 0x2e696d):
        """Register CRC key with the Paperang device"""
        logging.info("Setting CRC32 key...")
        msg = struct.pack('<I', int(key ^ self.standardKey))
        await self.sendToBt(msg, BtCommandByte.PRT_SET_CRC_KEY)
        self.crcKey = key
        self.crckeyset = True
        logging.info("CRC32 key set.")

    async def initializeAfterConnect(self):
        """Warm up printer state after connect similarly to the Android app"""
        logging.info("Running post-connect initialization...")
        await self.queryVersionFromBt()
        await self.querySNFromBt()
        await self.sendDensityToBt(int(self.print_density))
        await self.queryPowerOffTime()
        await self.queryBatteryStatus()
        await self.queryHardwareInfo()

    async def queryVersionFromBt(self):
        """Query firmware version"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_VERSION)

    async def sendPaperTypeToBt(self, paperType=0):
        """Set paper type"""
        msg = struct.pack('<B', paperType)
        return await self.sendToBt(msg, BtCommandByte.PRT_SET_PAPER_TYPE)

    async def sendDefaultParametersToBt(self):
        """Reset printer print parameters to defaults"""
        msg = struct.pack('<B', 0)
        return await self.sendToBt(msg, BtCommandByte.PRT_PRINT_DEFAULT_PARA)

    def defaultFeedLines(self):
        """Return the default post-print feed length in printer feed units."""
        return max(0, int(round(float(self.post_print_feed_mm) * self.feed_units_per_mm)))

    async def sendPrintEndCommand(self, paperType=0, feed_lines=None):
        """Finalize a print job similarly to the original app pipeline"""
        await self.sendPaperTypeToBt(paperType)
        if feed_lines is None:
            feed_lines = self.defaultFeedLines()
        return await self.sendFeedLineToBt(feed_lines)

    async def sendImageToBt(self, binary_img, feed_lines=None):
        """Send image data to the printer"""
        await self.sendDefaultParametersToBt()
        await self.sendPaperTypeToBt()
        msg = b"".join(map(lambda x: struct.pack("<c", x.to_bytes(1, byteorder="little")), binary_img))
        await self.sendToBt(msg, BtCommandByte.PRT_PRINT_DATA, need_reply=False)
        if feed_lines is None:
            feed_lines = self.defaultFeedLines()
        await self.sendPrintEndCommand(feed_lines=feed_lines)
        return await self.queryBatteryStatus()

    async def sendSelfTestToBt(self):
        """Send self-test command"""
        msg = struct.pack('<B', 0)
        return await self.sendToBt(msg, BtCommandByte.PRT_PRINT_TEST_PAGE)

    async def sendDensityToBt(self, density):
        """Set print density"""
        msg = struct.pack('<B', density)
        return await self.sendToBt(msg, BtCommandByte.PRT_SET_HEAT_DENSITY)

    async def sendFeedLineToBt(self, length):
        """Feed paper by specified lines"""
        msg = struct.pack('<H', length)
        return await self.sendToBt(msg, BtCommandByte.PRT_FEED_LINE)

    async def queryBatteryStatus(self):
        """Query battery status"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_BAT_STATUS)

    async def queryBluetoothMac(self):
        """Query Bluetooth MAC address reported by the printer."""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_BT_MAC)

    async def queryDensity(self):
        """Query print density"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_HEAT_DENSITY)

    async def sendFeedToHeadLineToBt(self, length):
        """Feed to head line"""
        msg = struct.pack('<H', length)
        return await self.sendToBt(msg, BtCommandByte.PRT_FEED_TO_HEAD_LINE)

    async def queryPowerOffTime(self):
        """Query auto power-off time"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_POWER_DOWN_TIME)

    async def querySNFromBt(self):
        """Query serial number"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_SN)

    async def queryHardwareInfo(self):
        """Query hardware information"""
        msg = struct.pack('<B', 1)
        return await self.sendToBt(msg, BtCommandByte.PRT_GET_HW_INFO)


# This is a synchronous wrapper class that makes the async implementation compatible with the original API
class Paperang:
    def __init__(self, address=None, print_density=75, post_print_feed_mm=5.0, valid_names=None):
        self.bleak_printer = PaperangBleak(
            address,
            print_density=print_density,
            post_print_feed_mm=post_print_feed_mm,
            valid_names=valid_names,
        )
        self.connected = self._run_async(self.bleak_printer.connect())

    def _run_async(self, coroutine):
        """Run an async coroutine synchronously"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coroutine)

    def disconnect(self):
        """Disconnect from the device"""
        self._run_async(self.bleak_printer.disconnect())

    def sendImageToBt(self, binary_img, feed_lines=None):
        """Send image to the printer"""
        return self._run_async(self.bleak_printer.sendImageToBt(binary_img, feed_lines=feed_lines))

    def sendDefaultParametersToBt(self):
        """Reset print parameters to defaults"""
        return self._run_async(self.bleak_printer.sendDefaultParametersToBt())

    def queryVersionFromBt(self):
        """Query firmware version"""
        return self._run_async(self.bleak_printer.queryVersionFromBt())

    def sendPrintEndCommand(self, paperType=0, feed_lines=None):
        """Finalize a print job"""
        return self._run_async(self.bleak_printer.sendPrintEndCommand(paperType=paperType, feed_lines=feed_lines))

    def sendSelfTestToBt(self):
        """Send self test command"""
        return self._run_async(self.bleak_printer.sendSelfTestToBt())

    def sendDensityToBt(self, density):
        """Set print density"""
        return self._run_async(self.bleak_printer.sendDensityToBt(density))

    def sendFeedLineToBt(self, length):
        """Feed paper by lines"""
        return self._run_async(self.bleak_printer.sendFeedLineToBt(length))

    def queryBatteryStatus(self):
        """Query battery status"""
        return self._run_async(self.bleak_printer.queryBatteryStatus())

    def queryBluetoothMac(self):
        """Query Bluetooth MAC address"""
        return self._run_async(self.bleak_printer.queryBluetoothMac())

    def queryDensity(self):
        """Query print density"""
        return self._run_async(self.bleak_printer.queryDensity())

    def sendFeedToHeadLineToBt(self, length):
        """Feed to head line"""
        return self._run_async(self.bleak_printer.sendFeedToHeadLineToBt(length))

    def queryPowerOffTime(self):
        """Query auto power-off time"""
        return self._run_async(self.bleak_printer.queryPowerOffTime())

    def querySNFromBt(self):
        """Query serial number"""
        return self._run_async(self.bleak_printer.querySNFromBt())

    def queryHardwareInfo(self):
        """Query hardware info"""
        return self._run_async(self.bleak_printer.queryHardwareInfo())
