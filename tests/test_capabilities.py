"""Tests for cross-platform capability detection."""
from __future__ import annotations

import importlib.metadata
from unittest.mock import patch

import pytest

from paperang_cli.protocol import _capabilities as caps


def test_bleak_imported_missing():
    with patch("paperang_cli.protocol._capabilities.importlib.util.find_spec", return_value=None):
        cap = caps.bleak_imported()
    assert cap.available is False
    assert cap.layer == "package"


def test_bleak_imported_present():
    with patch("paperang_cli.protocol._capabilities.importlib.util.find_spec", return_value=True), \
         patch("paperang_cli.protocol._capabilities.importlib.metadata.version", return_value="0.22.0"):
        cap = caps.bleak_imported()
    assert cap.available is True
    assert "0.22.0" in cap.detail


def test_paperang_p2_lib_missing():
    with patch("paperang_cli.protocol._capabilities.importlib.metadata.version",
               side_effect=importlib.metadata.PackageNotFoundError):
        cap = caps.paperang_p2_lib_version()
    assert cap.available is False
    assert "Not installed" in cap.detail


def test_paperang_p2_lib_usb_only():
    with patch("paperang_cli.protocol._capabilities.importlib.metadata.version", return_value="0.3.7"):
        cap = caps.paperang_p2_lib_version()
    assert cap.available is True
    assert "USB only" in cap.detail


def test_paperang_p2_lib_full():
    with patch("paperang_cli.protocol._capabilities.importlib.metadata.version", return_value="0.4.0rc3"):
        cap = caps.paperang_p2_lib_version()
    assert "USB + BLE" in cap.detail


def test_usb_p2_missing_pyusb():
    with patch("paperang_cli.protocol._capabilities.importlib.util.find_spec", return_value=None):
        cap = caps.usb_p2_available()
    assert cap.available is False


def test_bleak_backends_windows():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys:
        mock_sys.platform = "win32"
        cap = caps.bleak_backends()
    assert "WinRT" in cap.detail


def test_bleak_backends_macos():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys:
        mock_sys.platform = "darwin"
        cap = caps.bleak_backends()
    assert "CoreBluetooth" in cap.detail


def test_bleak_backends_linux():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys:
        mock_sys.platform = "linux"
        cap = caps.bleak_backends()
    assert "BlueZ" in cap.detail


def test_bleak_can_scan_linux_no_bluez():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys, \
         patch("paperang_cli.protocol._capabilities.shutil.which", return_value=None):
        mock_sys.platform = "linux"
        cap = caps.bleak_can_scan()
    assert cap.available is False
    assert "bluez not found" in cap.detail


def test_bleak_can_scan_linux_with_bluez():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys, \
         patch("paperang_cli.protocol._capabilities.shutil.which", return_value="/usr/bin/bluetoothd"):
        mock_sys.platform = "linux"
        cap = caps.bleak_can_scan()
    assert cap.available is True
    assert "bluetooth" in cap.detail.lower()


def test_bleak_can_scan_darwin():
    with patch("paperang_cli.protocol._capabilities.sys") as mock_sys:
        mock_sys.platform = "darwin"
        cap = caps.bleak_can_scan()
    assert "Info.plist" in cap.detail


def test_report_returns_list_of_dicts():
    result = caps.report()
    assert isinstance(result, list)
    assert len(result) == 5
    for item in result:
        assert "name" in item
        assert "available" in item
        assert "detail" in item
        assert "layer" in item


def test_capability_to_dict():
    cap = caps.Capability("test", True, "detail", "package")
    d = cap.to_dict()
    assert d == {"name": "test", "available": True, "detail": "detail", "layer": "package"}
