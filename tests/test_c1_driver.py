import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from PIL import Image

from paperang_cli.cli import cli
from paperang_cli.config import PaperangCliConfig
from paperang_cli.drivers.paperang_c1 import PaperangC1Driver
from paperang_cli.drivers.registry import get_driver
from paperang_cli.errors import ConfigError, DriverError
from paperang_cli.protocol.c1_ble import select_device


def test_selection_rejects_ambiguous_and_matches_uuid_or_qr_id():
    a = SimpleNamespace(address='example-uuid')
    adv = SimpleNamespace(manufacturer_data={0: bytes.fromhex('aabbccddeeff')})
    devices = [(a, adv)]
    assert select_device(devices, 'example-uuid') is a
    assert select_device(devices, 'AA:BB:CC:DD:EE:FF') is a
    assert select_device(devices) is a
    for entries, address in [(devices * 2, None), ([], None), (devices, 'other')]:
        with pytest.raises(RuntimeError):
            select_device(entries, address)


def test_config_and_registry():
    config = PaperangCliConfig.from_mapping({'model': 'paperang_c1'})
    assert config.printerwidth == 1248
    assert config.discovery_names == ['Paperang_C1']
    assert isinstance(get_driver(config), PaperangC1Driver)
    for change in [{'transport': 'usb'}, {'printerwidth': 576}, {'print_density': 60}]:
        with pytest.raises(ConfigError):
            PaperangCliConfig.from_mapping({'model': 'paperang_c1', **change})


def test_cli_dry_runs_and_paper_gates(tmp_path, monkeypatch):
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'model': 'paperang_c1'}))
    pic = tmp_path / 'image.png'
    Image.new('RGB', (32, 16), 'white').save(pic)
    def forbidden(*args, **kwargs):
        pytest.fail('Offline operation attempted BLE')
    monkeypatch.setattr('paperang_cli.drivers.paperang_c1.C1Client', forbidden)
    runner = CliRunner()
    for command in [['text', 'C1'], ['paragraph', 'C1 paragraph'], ['image', str(pic)],
                    ['compose', 'C1', str(pic)]]:
        args = ['--config', str(config), '--json', 'print', *command]
        preview = runner.invoke(cli, [*args, '--dry-run'])
        assert preview.exit_code == 0, preview.output
        result = json.loads(preview.output)['result']
        assert result['model'] == 'paperang_c1'
        assert result['bytes_sent'] % 156 == 0
        assert result['feed_units'] == 180
        real = runner.invoke(cli, args)
        assert real.exit_code == 5, real.output
    result = runner.invoke(cli, ['--config', str(config), 'print', 'self-test', '--dry-run'])
    assert result.exit_code == 3


def test_reject_invalid_job_before_connect():
    driver = get_driver(PaperangCliConfig.from_mapping({'model': 'paperang_c1'}))
    for bitmap, feed in [(b'x', 0), (bytes(156 * 3601), 0), (bytes(156), 51)]:
        with pytest.raises(DriverError):
            driver._send_bitstream_job(bitstream=bitmap, feed_mm=feed,
                                      operation='image', dry_run=True, address=None)


def test_queries_and_print_lifecycle(monkeypatch):
    events = []
    values = {'status': b'\x00\x00', 'firmware': b'\x09\x00\x01',
              'serial': b'test-serial', 'battery_percent': b'\x64',
              'heat_density': b'\x5f', 'power_down_seconds': b'\x08\x07',
              'bluetooth_id': b'aabbccddeeff'}
    class Client:
        def __init__(self, address):
            self.device = SimpleNamespace(address=address or 'test-uuid')
        async def __aenter__(self):
            events.append('connect')
            return self
        async def __aexit__(self, *args):
            events.append('disconnect')
        async def query(self, name):
            events.append(name)
            return values[name]
        async def print_bitmap(self, bitmap, width, feed):
            events.append(('print', bitmap, width, feed))
    monkeypatch.setattr('paperang_cli.drivers.paperang_c1.C1Client', Client)
    driver = get_driver(PaperangCliConfig.from_mapping({'model': 'paperang_c1'}))
    status = driver.status()
    assert status.firmware_version == '1.00.09'
    assert status.battery_percent == 100
    assert status.power_off_time == 1800
    assert driver.battery().battery_percent == 100
    assert driver.bluetooth_mac().bluetooth_mac == 'AA:BB:CC:DD:EE:FF'
    result = driver._send_bitstream_job(bitstream=b'\x80' + bytes(155), operation='image',
                                      feed_mm=15, dry_run=False, address='test-uuid')
    assert result.address == 'test-uuid'
    assert ('print', b'\x80' + bytes(155), 1248, 180) in events
    assert events[-1] == 'disconnect'
    events.clear()
    values['status'] = b'\x01\x00'
    with pytest.raises(DriverError):
        driver._send_bitstream_job(bitstream=bytes(156), operation='image',
                                  feed_mm=0, dry_run=False, address=None)
    assert events == ['connect', 'status', 'disconnect']
