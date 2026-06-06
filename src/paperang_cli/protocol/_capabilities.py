"""Cross-platform capability detection for paperang-cli."""
from __future__ import annotations

import importlib
import importlib.util
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Literal

Layer = Literal["python", "system", "permission", "package"]


@dataclass(frozen=True)
class Capability:
    name: str
    available: bool
    detail: str
    layer: Layer

    def to_dict(self) -> dict:
        return asdict(self)


def bleak_imported() -> Capability:
    spec = importlib.util.find_spec("bleak")
    if spec is None:
        return Capability("bleak.imported", False, "bleak not installed", "package")
    try:
        return Capability("bleak.imported", True, f"bleak {importlib.metadata.version('bleak')}", "package")
    except Exception:
        return Capability("bleak.imported", True, "bleak (version unknown)", "package")


def bleak_backends() -> Capability:
    if sys.platform == "win32":
        return Capability("bleak.backend", True, "WinRT (Windows)", "system")
    if sys.platform == "darwin":
        return Capability("bleak.backend", True, "CoreBluetooth (macOS) — requires user permission", "permission")
    return Capability("bleak.backend", True, "BlueZ DBus (Linux) — requires bluez service + dbus", "system")


def bleak_can_scan() -> Capability:
    if sys.platform == "darwin":
        return Capability("bleak.scan", True, "May require Info.plist NSBluetoothAlwaysUsageDescription or first-run prompt", "permission")
    if sys.platform.startswith("linux"):
        bluez = shutil.which("bluetoothd") or shutil.which("bluetooth")
        if not bluez:
            return Capability("bleak.scan", False, "bluez not found in PATH", "system")
        return Capability("bleak.scan", True, "bluez detected; user must be in 'bluetooth' group", "system")
    return bleak_backends()


def paperang_p2_lib_version() -> Capability:
    try:
        v = importlib.metadata.version("paperang-p2-lib")
        parts = v.split(".")
        if len(parts) < 2 or "rc" in v:
            return Capability("paperang-p2-lib", True, f"v{v} (USB + BLE)", "package")
        minor = int(parts[1])
        if minor >= 4 or "rc" in v:
            return Capability("paperang-p2-lib", True, f"v{v} (USB + BLE)", "package")
        return Capability("paperang-p2-lib", True, f"v{v} (USB only — P2 BLE unavailable, upgrade: pip install --pre -U paperang-p2-lib)", "package")
    except importlib.metadata.PackageNotFoundError:
        return Capability("paperang-p2-lib", False, "Not installed; pip install paperang-p2-lib", "package")
    except Exception:
        return Capability("paperang-p2-lib", False, "Installed but version could not be determined", "package")


def usb_p2_available() -> Capability:
    if importlib.util.find_spec("usb") is None:
        return Capability("p2.usb", False, "pyusb not installed", "package")
    backend, backend_detail = _pyusb_libusb1_backend()
    if backend is None:
        return Capability("p2.usb", False, backend_detail, "system")
    if sys.platform.startswith("linux"):
        return Capability("p2.usb", True, "libusb backend loaded; may require udev rules (see docs/installation.md#linux)", "permission")
    if sys.platform == "darwin":
        return Capability("p2.usb", True, "libusb backend loaded; may require user USB permission", "system")
    return Capability("p2.usb", True, "libusb backend loaded; device may still require WinUSB/Zadig driver", "system")


def _pyusb_libusb1_backend():
    try:
        if importlib.util.find_spec("libusb_package") is not None:
            try:
                libusb_package = importlib.import_module("libusb_package")
                backend = libusb_package.get_libusb1_backend()
                if backend is not None:
                    return backend, "libusb backend loaded from libusb-package"
            except Exception:
                pass

        libusb1 = importlib.import_module("usb.backend.libusb1")
        backend = libusb1.get_backend()
    except Exception as exc:
        return None, f"PyUSB is installed but libusb backend check failed: {exc}"

    if backend is None:
        return None, "PyUSB is installed but no libusb-1.0 backend is available"
    return backend, "libusb backend loaded"


def report() -> list[dict]:
    """Return all capability checks as a list of dicts (JSON-serializable)."""
    checks = [
        bleak_imported,
        bleak_backends,
        bleak_can_scan,
        paperang_p2_lib_version,
        usb_p2_available,
    ]
    results: list[dict] = []
    for check in checks:
        try:
            results.append(check().to_dict())
        except Exception as exc:
            results.append({
                "name": check.__name__,
                "available": False,
                "detail": f"check failed: {exc}",
                "layer": "system",
            })
    return results
