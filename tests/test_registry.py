from __future__ import annotations

import pytest
from PIL import Image

from paperang_cli.config import PaperangCliConfig
from paperang_cli.drivers.paperang_p1 import PaperangP1Driver
from paperang_cli.drivers import paperang_p2
from paperang_cli.drivers.paperang_p2 import PaperangP2Driver
from paperang_cli.drivers.registry import get_driver, supported_models
from paperang_cli.errors import ConfigError, DriverError
from paperang_cli.render import RenderedBitstream, RenderStyling


def test_get_driver_returns_p1_driver():
    driver = get_driver(PaperangCliConfig(model="paperang_p1"))
    assert isinstance(driver, PaperangP1Driver)


def test_get_driver_returns_p2_driver():
    driver = get_driver(PaperangCliConfig(model="paperang_p2"))
    assert isinstance(driver, PaperangP2Driver)


def test_p2_driver_prefers_paperang_ble_name_prefix():
    driver = PaperangP2Driver(PaperangCliConfig.from_mapping({"model": "paperang_p2", "transport": "ble"}))

    assert driver._ble_scan_name() == "Paperang"


def test_p2_driver_prefers_p2_name_for_ff00_ble_profile():
    driver = PaperangP2Driver(PaperangCliConfig.from_mapping({"model": "paperang_p2", "transport": "ble"}))

    assert driver._ff00_ble_scan_name() == "Paperang_P2"


def test_p2_usb_discover_reports_missing_libusb_backend(monkeypatch):
    class FakePrinter:
        def connect(self):
            import usb.core

            raise usb.core.NoBackendError("No backend available")

        def disconnect(self):
            pass

    driver = PaperangP2Driver(PaperangCliConfig(model="paperang_p2", transport="usb"))
    monkeypatch.setattr(driver, "_build_printer", lambda address: FakePrinter())

    with pytest.raises(DriverError) as excinfo:
        driver.discover()

    assert "libusb" in str(excinfo.value).lower()


def test_p2_connect_printer_creates_event_loop_for_ble_transport(monkeypatch):
    calls = []

    class FakePrinter:
        def connect(self):
            calls.append("connect")
            return True

    driver = PaperangP2Driver(PaperangCliConfig(model="paperang_p2", transport="ble"))
    monkeypatch.setattr(driver, "_build_printer", lambda address: FakePrinter())
    monkeypatch.setattr(paperang_p2, "_ensure_current_event_loop", lambda: calls.append("ensure_loop"))

    printer = driver._connect_printer("01:54:8D:17:B3:F2")

    assert printer is not None
    assert calls == ["ensure_loop", "connect"]


def test_p2_connect_printer_falls_back_to_ff00_ble_profile(monkeypatch):
    calls = []

    class FakeNusPrinter:
        def connect(self):
            calls.append("nus_connect")
            raise RuntimeError("Characteristic 6E400003-B5A3-F393-E0A9-E50E24DCCA9E was not found")

        def disconnect(self):
            calls.append("nus_disconnect")

    class FakeFf00Printer:
        def connect(self):
            calls.append("ff00_connect")
            return True

    driver = PaperangP2Driver(PaperangCliConfig(model="paperang_p2", transport="ble"))
    monkeypatch.setattr(driver, "_build_nus_printer", lambda address: FakeNusPrinter())
    monkeypatch.setattr(driver, "_build_ff00_printer", lambda address: FakeFf00Printer())
    monkeypatch.setattr(paperang_p2, "_ensure_current_event_loop", lambda: calls.append("ensure_loop"))

    printer = driver._connect_printer("01:54:8D:17:B3:F2")

    assert isinstance(printer._active_printer, FakeFf00Printer)
    assert calls == ["ensure_loop", "nus_connect", "nus_disconnect", "ff00_connect"]


def test_p2_text_render_uses_binary_text_for_crisper_ff00_output(monkeypatch):
    captured: dict[str, object] = {}

    def fake_render_text_job(*args, **kwargs):
        captured.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 72,
            width=576,
            height=1,
            styling=RenderStyling(font_size=32),
            estimated_length_mm=0.08472,
        )

    driver = PaperangP2Driver(PaperangCliConfig(model="paperang_p2", transport="ble"))
    monkeypatch.setattr(paperang_p2, "render_text_job", fake_render_text_job)

    driver.print_text(
        "P2",
        paragraph=False,
        font_size=32,
        font_family=None,
        min_font_size=None,
        autofit=None,
        orientation=None,
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )

    assert captured["binary_text"] is True


def test_p2_text_render_scales_default_font_and_padding_for_576_dot_head(monkeypatch):
    captured: dict[str, object] = {}

    def fake_render_text_job(*args, **kwargs):
        captured.update(kwargs)
        return RenderedBitstream(
            bitstream=b"\x00" * 72,
            width=576,
            height=1,
            styling=RenderStyling(font_size=54, horizontal_padding_px=24, vertical_padding_px=18),
            estimated_length_mm=0.08472,
        )

    driver = PaperangP2Driver(PaperangCliConfig.from_mapping({"model": "paperang_p2", "transport": "ble"}))
    monkeypatch.setattr(paperang_p2, "render_text_job", fake_render_text_job)

    driver.print_text(
        "P2",
        paragraph=False,
        font_size=None,
        font_family=None,
        min_font_size=None,
        autofit=None,
        orientation=None,
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )

    assert captured["printer_width"] == 576
    assert captured["font_size"] == 54
    assert captured["horizontal_padding_px"] == 24
    assert captured["vertical_padding_px"] == 18


def test_p2_ff00_bitmap_job_passes_feed_in_millimeters(monkeypatch):
    captured: dict[str, object] = {}

    class FakeFf00Printer:
        def connect(self):
            return True

        def disconnect(self):
            captured["disconnect"] = True

        def set_paper_type(self, value):
            captured["paper_type"] = value

        def set_heat_density(self, value):
            captured["heat_density"] = value

        def print_bitmap_with_feed(self, bitmap_data, *, width_bytes, feed_mm):
            captured["bitmap_data"] = bitmap_data
            captured["width_bytes"] = width_bytes
            captured["feed_mm"] = feed_mm

        def get_battery(self):
            return 77

    driver = PaperangP2Driver(PaperangCliConfig.from_mapping({"model": "paperang_p2", "transport": "ble"}))
    monkeypatch.setattr(driver, "_build_printer", lambda address: FakeFf00Printer())
    monkeypatch.setattr(paperang_p2, "_ensure_current_event_loop", lambda: None)

    result = driver._send_bitmap_job(
        bitstream=b"\xFF" * 72,
        operation="text",
        feed_mm=5.0,
        dry_run=False,
        address="01:54:8D:17:B3:F2",
    )

    assert captured["width_bytes"] == 72
    assert captured["feed_mm"] == 5.0
    assert result.feed_units == 280
    assert result.battery_after == 77


def test_p2_dry_run_print_operations_and_sideways_rendering(tmp_path):
    driver = PaperangP2Driver(PaperangCliConfig.from_mapping({"model": "paperang_p2", "transport": "ble"}))
    image_path = tmp_path / "p2-wide-source.png"
    Image.new("RGB", (96, 32), "white").save(image_path)

    text = driver.print_text(
        "P2 sideways",
        paragraph=False,
        font_size=36,
        font_family=None,
        min_font_size=None,
        autofit=None,
        orientation="rotate-90-cw",
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )
    paragraph = driver.print_text(
        "P2 paragraph sideways",
        paragraph=True,
        font_size=24,
        font_family=None,
        min_font_size=None,
        autofit=True,
        orientation="rotate-90-ccw",
        horizontal_padding_px=None,
        vertical_padding_px=None,
        line_spacing_px=None,
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )
    image = driver.print_image(
        image_path,
        mode="sticker",
        conversion=None,
        orientation="rotate-90-cw",
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )
    compose = driver.print_compose(
        "P2 compose",
        image_path,
        layout="image-above",
        font_size=28,
        min_font_size=None,
        font_fit=None,
        mode="sticker",
        conversion=None,
        feed_mm=0,
        allow_paper_use=False,
        dry_run=True,
    )

    assert text.dry_run is True
    assert text.styling["orientation"] == "rotate-90-cw"
    assert paragraph.styling["orientation"] == "rotate-90-ccw"
    assert image.styling["orientation"] == "rotate-90-cw"
    assert compose.layout == "image-above"
    assert {text.model, paragraph.model, image.model, compose.model} == {"paperang_p2"}
    assert all(result.bytes_sent and result.bytes_sent % 72 == 0 for result in (text, paragraph, image, compose))


def test_get_driver_rejects_unknown_model():
    with pytest.raises(ConfigError):
        get_driver(PaperangCliConfig(model="unknown_model"))


def test_supported_models_contains_p1_and_p2():
    assert supported_models() == ["paperang_p1", "paperang_p2"]
