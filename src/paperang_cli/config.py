"""Configuration loading for the standalone paperang-cli project."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from paperang_cli.errors import ConfigError

DEFAULT_DISCOVERY_NAMES = ["MiaoMiaoJi", "Paperang", "Paperang_P2", "Paperang_P2S"]
MODEL_DEFAULT_PRINTER_WIDTHS = {
    "paperang_p1": 384,
    "paperang_p2": 576,
}
MODEL_DEFAULT_PRINT_DENSITIES = {
    "paperang_p1": 75,
    "paperang_p2": 95,
}
MODEL_DEFAULT_POST_PRINT_FEEDS = {
    "paperang_p1": 5.0,
    "paperang_p2": 12.0,
}
MODEL_DEFAULT_CALIBRATIONS = {
    "paperang_p1": {"printable_width_mm": 44.0, "advance_mm_per_px": 0.1217},
    "paperang_p2": {"printable_width_mm": 44.0, "advance_mm_per_px": 0.08472},
}
VALID_TRANSPORTS = {"ble", "usb"}
VALID_FONT_FAMILIES = {"sans", "mono", "serif"}
VALID_ORIENTATIONS = {"normal", "rotate-90-cw", "rotate-90-ccw"}
VALID_IMAGE_MODES = {"sticker", "photo"}
VALID_IMAGE_CONVERSIONS = {"threshold", "edge", "dither"}
VALID_COMPOSE_LAYOUTS = {"text-above", "image-above"}
VALID_TEXT_OVERFLOW_POLICIES = {"error", "shrink-to-fit"}
VALID_COMPOSE_OVERFLOW_POLICIES = {"error", "report-only"}
VALID_IMAGE_FIT_MODES = {"fit-width", "fit-within-length"}
VALID_FONT_FIT_MODES = {"manual", "largest-fitting"}


@dataclass(slots=True)
class CalibrationSettings:
    printable_width_mm: float = 44.0
    advance_mm_per_px: float = 0.1217

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any] | None = None,
        *,
        defaults: "CalibrationSettings | None" = None,
    ) -> "CalibrationSettings":
        payload = data or {}
        fallback = defaults or cls()
        return cls(
            printable_width_mm=_optional_float(payload.get("printable_width_mm"), default=fallback.printable_width_mm),
            advance_mm_per_px=_optional_float(payload.get("advance_mm_per_px"), default=fallback.advance_mm_per_px),
        )

    def validate(self) -> None:
        if self.printable_width_mm <= 0:
            raise ConfigError("calibration.printable_width_mm must be greater than zero")
        if self.advance_mm_per_px <= 0:
            raise ConfigError("calibration.advance_mm_per_px must be greater than zero")


@dataclass(slots=True)
class TextPrintDefaults:
    font_family: str = "sans"
    font_size: int | None = None
    min_font_size: int | None = None
    font_fit: str = "manual"
    autofit: bool = False
    orientation: str = "normal"
    horizontal_padding_px: int | None = None
    vertical_padding_px: int | None = None
    line_spacing_px: int | None = None
    max_length_mm: float | None = None
    overflow_policy: str = "shrink-to-fit"
    break_long_words: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None, *, label: str = "print_defaults.text") -> "TextPrintDefaults":
        payload = data or {}
        return cls(
            font_family=_normalize_string_choice(payload.get("font_family", "sans"), default="sans"),
            font_size=_optional_int(payload.get("font_size")),
            min_font_size=_optional_int(payload.get("min_font_size")),
            font_fit=_normalize_string_choice(payload.get("font_fit", "manual"), default="manual"),
            autofit=_optional_bool(payload.get("autofit"), f"{label}.autofit", default=False),
            orientation=_normalize_string_choice(payload.get("orientation", "normal"), default="normal"),
            horizontal_padding_px=_optional_int(payload.get("horizontal_padding_px")),
            vertical_padding_px=_optional_int(payload.get("vertical_padding_px")),
            line_spacing_px=_optional_int(payload.get("line_spacing_px")),
            max_length_mm=_optional_float(payload.get("max_length_mm")),
            overflow_policy=_normalize_string_choice(payload.get("overflow_policy", "shrink-to-fit"), default="shrink-to-fit"),
            break_long_words=_optional_bool(payload.get("break_long_words"), f"{label}.break_long_words", default=False),
        )

    def validate(self, *, label: str) -> None:
        if self.font_family not in VALID_FONT_FAMILIES:
            raise ConfigError(f"{label}.font_family must be one of: {', '.join(sorted(VALID_FONT_FAMILIES))}")
        if self.orientation not in VALID_ORIENTATIONS:
            raise ConfigError(f"{label}.orientation must be one of: {', '.join(sorted(VALID_ORIENTATIONS))}")
        if self.font_fit not in VALID_FONT_FIT_MODES:
            raise ConfigError(f"{label}.font_fit must be one of: {', '.join(sorted(VALID_FONT_FIT_MODES))}")
        if self.overflow_policy not in VALID_TEXT_OVERFLOW_POLICIES:
            raise ConfigError(
                f"{label}.overflow_policy must be one of: {', '.join(sorted(VALID_TEXT_OVERFLOW_POLICIES))}"
            )

        _validate_optional_positive_int(self.font_size, f"{label}.font_size")
        _validate_optional_positive_int(self.min_font_size, f"{label}.min_font_size")
        _validate_optional_non_negative_int(self.horizontal_padding_px, f"{label}.horizontal_padding_px")
        _validate_optional_non_negative_int(self.vertical_padding_px, f"{label}.vertical_padding_px")
        _validate_optional_non_negative_int(self.line_spacing_px, f"{label}.line_spacing_px")
        _validate_optional_positive_float(self.max_length_mm, f"{label}.max_length_mm")

        if self.font_size is not None and self.min_font_size is not None and self.min_font_size > self.font_size:
            raise ConfigError(f"{label}.min_font_size must be less than or equal to {label}.font_size")


@dataclass(slots=True)
class ImagePrintDefaults:
    mode: str = "sticker"
    conversion: str | None = None
    orientation: str = "normal"
    max_length_mm: float | None = None
    fit_mode: str = "fit-width"

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "ImagePrintDefaults":
        payload = data or {}
        conversion_value = payload.get("conversion")
        return cls(
            mode=_normalize_string_choice(payload.get("mode", "sticker"), default="sticker"),
            conversion=_normalize_string_choice(conversion_value) if conversion_value is not None else None,
            orientation=_normalize_string_choice(payload.get("orientation", "normal"), default="normal"),
            max_length_mm=_optional_float(payload.get("max_length_mm")),
            fit_mode=_normalize_string_choice(payload.get("fit_mode", "fit-width"), default="fit-width"),
        )

    def validate(self, *, label: str) -> None:
        if self.mode not in VALID_IMAGE_MODES:
            raise ConfigError(f"{label}.mode must be one of: {', '.join(sorted(VALID_IMAGE_MODES))}")
        if self.conversion is not None and self.conversion not in VALID_IMAGE_CONVERSIONS:
            raise ConfigError(
                f"{label}.conversion must be one of: {', '.join(sorted(VALID_IMAGE_CONVERSIONS))}"
            )
        if self.orientation not in VALID_ORIENTATIONS:
            raise ConfigError(f"{label}.orientation must be one of: {', '.join(sorted(VALID_ORIENTATIONS))}")
        if self.fit_mode not in VALID_IMAGE_FIT_MODES:
            raise ConfigError(f"{label}.fit_mode must be one of: {', '.join(sorted(VALID_IMAGE_FIT_MODES))}")

        _validate_optional_positive_float(self.max_length_mm, f"{label}.max_length_mm")


@dataclass(slots=True)
class ComposePrintDefaults:
    font_family: str = "sans"
    font_size: int | None = None
    min_font_size: int | None = None
    font_fit: str = "manual"
    horizontal_padding_px: int | None = None
    vertical_padding_px: int | None = None
    line_spacing_px: int | None = None
    layout: str = "text-above"
    spacer_height_px: int | None = None
    image_mode: str = "sticker"
    image_conversion: str | None = None
    max_length_mm: float | None = None
    overflow_policy: str = "report-only"
    break_long_words: bool = False

    @classmethod
    def from_mapping(
        cls, data: dict[str, Any] | None = None, *, label: str = "print_defaults.compose"
    ) -> "ComposePrintDefaults":
        payload = data or {}
        image_conversion = payload.get("image_conversion")
        return cls(
            font_family=_normalize_string_choice(payload.get("font_family", "sans"), default="sans"),
            font_size=_optional_int(payload.get("font_size")),
            min_font_size=_optional_int(payload.get("min_font_size")),
            font_fit=_normalize_string_choice(payload.get("font_fit", "manual"), default="manual"),
            horizontal_padding_px=_optional_int(payload.get("horizontal_padding_px")),
            vertical_padding_px=_optional_int(payload.get("vertical_padding_px")),
            line_spacing_px=_optional_int(payload.get("line_spacing_px")),
            layout=_normalize_string_choice(payload.get("layout", "text-above"), default="text-above"),
            spacer_height_px=_optional_int(payload.get("spacer_height_px")),
            image_mode=_normalize_string_choice(payload.get("image_mode", "sticker"), default="sticker"),
            image_conversion=_normalize_string_choice(image_conversion) if image_conversion is not None else None,
            max_length_mm=_optional_float(payload.get("max_length_mm")),
            overflow_policy=_normalize_string_choice(payload.get("overflow_policy", "report-only"), default="report-only"),
            break_long_words=_optional_bool(payload.get("break_long_words"), f"{label}.break_long_words", default=False),
        )

    def validate(self, *, label: str) -> None:
        if self.font_family not in VALID_FONT_FAMILIES:
            raise ConfigError(f"{label}.font_family must be one of: {', '.join(sorted(VALID_FONT_FAMILIES))}")
        if self.layout not in VALID_COMPOSE_LAYOUTS:
            raise ConfigError(f"{label}.layout must be one of: {', '.join(sorted(VALID_COMPOSE_LAYOUTS))}")
        if self.image_mode not in VALID_IMAGE_MODES:
            raise ConfigError(f"{label}.image_mode must be one of: {', '.join(sorted(VALID_IMAGE_MODES))}")
        if self.font_fit not in VALID_FONT_FIT_MODES:
            raise ConfigError(f"{label}.font_fit must be one of: {', '.join(sorted(VALID_FONT_FIT_MODES))}")
        if self.overflow_policy not in VALID_COMPOSE_OVERFLOW_POLICIES:
            raise ConfigError(
                f"{label}.overflow_policy must be one of: {', '.join(sorted(VALID_COMPOSE_OVERFLOW_POLICIES))}"
            )
        if self.image_conversion is not None and self.image_conversion not in VALID_IMAGE_CONVERSIONS:
            raise ConfigError(
                f"{label}.image_conversion must be one of: {', '.join(sorted(VALID_IMAGE_CONVERSIONS))}"
            )

        _validate_optional_positive_int(self.font_size, f"{label}.font_size")
        _validate_optional_positive_int(self.min_font_size, f"{label}.min_font_size")
        _validate_optional_non_negative_int(self.horizontal_padding_px, f"{label}.horizontal_padding_px")
        _validate_optional_non_negative_int(self.vertical_padding_px, f"{label}.vertical_padding_px")
        _validate_optional_non_negative_int(self.line_spacing_px, f"{label}.line_spacing_px")
        _validate_optional_non_negative_int(self.spacer_height_px, f"{label}.spacer_height_px")
        _validate_optional_positive_float(self.max_length_mm, f"{label}.max_length_mm")

        if self.font_size is not None and self.min_font_size is not None and self.min_font_size > self.font_size:
            raise ConfigError(f"{label}.min_font_size must be less than or equal to {label}.font_size")


@dataclass(slots=True)
class PrintDefaults:
    text: TextPrintDefaults = field(default_factory=TextPrintDefaults)
    paragraph: TextPrintDefaults = field(default_factory=TextPrintDefaults)
    image: ImagePrintDefaults = field(default_factory=ImagePrintDefaults)
    compose: ComposePrintDefaults = field(default_factory=ComposePrintDefaults)

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "PrintDefaults":
        payload = data or {}
        _require_mapping(payload, "print_defaults")
        return cls(
            text=TextPrintDefaults.from_mapping(
                _optional_mapping(payload.get("text"), "print_defaults.text"),
                label="print_defaults.text",
            ),
            paragraph=TextPrintDefaults.from_mapping(
                _optional_mapping(payload.get("paragraph"), "print_defaults.paragraph"),
                label="print_defaults.paragraph",
            ),
            image=ImagePrintDefaults.from_mapping(_optional_mapping(payload.get("image"), "print_defaults.image")),
            compose=ComposePrintDefaults.from_mapping(
                _optional_mapping(payload.get("compose"), "print_defaults.compose"),
                label="print_defaults.compose",
            ),
        )

    def validate(self) -> None:
        self.text.validate(label="print_defaults.text")
        self.paragraph.validate(label="print_defaults.paragraph")
        self.image.validate(label="print_defaults.image")
        self.compose.validate(label="print_defaults.compose")


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any, *, default: float | None = None) -> float | None:
    if value is None:
        return default
    return float(value)


def _optional_bool(value: Any, field_name: str, *, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{field_name} must be a boolean")


def _normalize_string_choice(value: Any, *, default: str | None = None) -> str:
    if value is None:
        if default is None:
            raise ConfigError("Expected a string value")
        return default
    return str(value).strip().lower()


def _validate_optional_positive_int(value: int | None, field_name: str) -> None:
    if value is not None and value <= 0:
        raise ConfigError(f"{field_name} must be greater than zero")


def _validate_optional_positive_float(value: float | None, field_name: str) -> None:
    if value is not None and value <= 0:
        raise ConfigError(f"{field_name} must be greater than zero")


def _validate_optional_non_negative_int(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ConfigError(f"{field_name} must be zero or greater")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"{field_name} must be an object mapping")


def _optional_mapping(value: Any, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    _require_mapping(value, field_name)
    return value


def _select_printer_mapping(
    data: dict[str, Any],
    printer_name: str | None,
) -> tuple[dict[str, Any], str | None, str | None, dict[str, dict[str, Any]]]:
    printers_payload = data.get("printers")
    if not printers_payload:
        if printer_name:
            raise ConfigError(f"Printer profile '{printer_name}' was requested, but this config has no printers map")
        return data, None, None, {}

    _require_mapping(printers_payload, "printers")
    printers: dict[str, dict[str, Any]] = {}
    for raw_name, raw_profile in printers_payload.items():
        name = str(raw_name).strip()
        if not name:
            raise ConfigError("printers contains an empty profile name")
        profile = _optional_mapping(raw_profile, f"printers.{name}") or {}
        if "model" not in profile:
            raise ConfigError(f"printers.{name}.model is required")
        printers[name] = dict(profile)

    default_printer = str(data.get("default_printer") or next(iter(printers))).strip()
    if default_printer not in printers:
        raise ConfigError(f"default_printer '{default_printer}' is not defined in printers")

    active_printer = str(printer_name or default_printer).strip()
    if active_printer not in printers:
        available = ", ".join(sorted(printers))
        raise ConfigError(f"Unknown printer profile '{active_printer}'. Available profiles: {available}")

    shared = {
        key: data[key]
        for key in ("post_print_feed_mm", "discovery_names", "print_defaults", "presets")
        if key in data
    }
    selected = {**shared, **printers[active_printer]}

    for name, profile in printers.items():
        validation_payload = {**shared, **profile}
        PaperangCliConfig._from_selected_mapping(
            validation_payload,
            active_printer=name,
            default_printer=default_printer,
            printers=printers,
        )

    return selected, active_printer, default_printer, printers


@dataclass(slots=True)
class PaperangCliConfig:
    active_printer: str | None = None
    default_printer: str | None = None
    printers: dict[str, dict[str, Any]] = field(default_factory=dict)
    model: str = "paperang_p1"
    transport: str | None = None
    macaddress: str = ""
    printerwidth: int = 384
    print_density: int = 75
    post_print_feed_mm: float = 5.0
    discovery_names: list[str] = field(default_factory=lambda: list(DEFAULT_DISCOVERY_NAMES))
    calibration: CalibrationSettings = field(default_factory=CalibrationSettings)
    print_defaults: PrintDefaults = field(default_factory=PrintDefaults)
    presets: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, printer_name: str | None = None) -> "PaperangCliConfig":
        selected_data, active_printer, default_printer, printers = _select_printer_mapping(data, printer_name)
        return cls._from_selected_mapping(
            selected_data,
            active_printer=active_printer,
            default_printer=default_printer,
            printers=printers,
        )

    @classmethod
    def _from_selected_mapping(
        cls,
        data: dict[str, Any],
        *,
        active_printer: str | None = None,
        default_printer: str | None = None,
        printers: dict[str, dict[str, Any]] | None = None,
    ) -> "PaperangCliConfig":
        defaults = cls()
        model = str(data.get("model", defaults.model))
        default_printer_width = MODEL_DEFAULT_PRINTER_WIDTHS.get(model, defaults.printerwidth)
        default_print_density = MODEL_DEFAULT_PRINT_DENSITIES.get(model, defaults.print_density)
        default_post_print_feed_mm = MODEL_DEFAULT_POST_PRINT_FEEDS.get(model, defaults.post_print_feed_mm)
        default_calibration = CalibrationSettings.from_mapping(MODEL_DEFAULT_CALIBRATIONS.get(model))
        config = cls(
            active_printer=active_printer,
            default_printer=default_printer,
            printers=dict(printers or {}),
            model=model,
            transport=_normalize_string_choice(data.get("transport")) if data.get("transport") is not None else None,
            macaddress=str(data.get("macaddress", defaults.macaddress)),
            printerwidth=int(data.get("printerwidth", default_printer_width)),
            print_density=int(data.get("print_density", default_print_density)),
            post_print_feed_mm=float(data.get("post_print_feed_mm", default_post_print_feed_mm)),
            discovery_names=list(data.get("discovery_names", DEFAULT_DISCOVERY_NAMES)),
            calibration=CalibrationSettings.from_mapping(
                _optional_mapping(data.get("calibration"), "calibration"),
                defaults=default_calibration,
            ),
            print_defaults=PrintDefaults.from_mapping(_optional_mapping(data.get("print_defaults"), "print_defaults")),
            presets=dict(_optional_mapping(data.get("presets"), "presets") or {}),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.transport is not None and self.transport not in VALID_TRANSPORTS:
            raise ConfigError(f"transport must be one of: {', '.join(sorted(VALID_TRANSPORTS))}")
        if self.model == "paperang_p1" and self.transport == "usb":
            raise ConfigError("Unsupported transport 'usb' for model 'paperang_p1'")
        if self.printerwidth <= 0:
            raise ConfigError("printerwidth must be greater than zero")
        if self.print_density < 0 or self.print_density > 255:
            raise ConfigError("print_density must be between 0 and 255")
        if self.post_print_feed_mm < 0:
            raise ConfigError("post_print_feed_mm must be zero or greater")
        if not self.discovery_names:
            raise ConfigError("discovery_names must contain at least one candidate")
        self.calibration.validate()
        self.print_defaults.validate()
        for name, preset in self.presets.items():
            _require_mapping(preset, f"presets.{name}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    if sys.platform == "win32":
        config_home = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        config_home = Path.home() / "Library" / "Application Support"
    else:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return config_home / "paperang-cli" / "paperang-cli.config.json"


def example_config_path() -> Path:
    return project_root() / "paperang-cli.config.example.json"


def resolve_config_path(explicit_path: str | os.PathLike[str] | None = None) -> tuple[Path, str]:
    if explicit_path:
        return Path(explicit_path).expanduser(), "explicit"

    env_path = os.environ.get("PAPERANG_CLI_CONFIG")
    if env_path:
        return Path(env_path).expanduser(), "environment"

    return default_config_path(), "default"


def load_config(
    explicit_path: str | os.PathLike[str] | None = None,
    *,
    printer_name: str | None = None,
) -> tuple[PaperangCliConfig, Path, bool]:
    path, source = resolve_config_path(explicit_path)
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Failed to parse config file {path}: {exc}") from exc
        return PaperangCliConfig.from_mapping(raw, printer_name=printer_name), path, True

    if source in {"explicit", "environment"}:
        raise ConfigError(f"Config file does not exist: {path}")
    if printer_name:
        raise ConfigError(f"Printer profile '{printer_name}' was requested, but no config file exists at {path}")

    return PaperangCliConfig(), path, False


def write_example_config(destination: Path, overwrite: bool = False) -> Path:
    destination = destination.expanduser()
    if destination.exists() and not overwrite:
        raise ConfigError(f"Refusing to overwrite existing config: {destination}")

    example = example_config_path()
    if example.exists():
        content = example.read_text(encoding="utf-8")
    else:
        content = json.dumps(PaperangCliConfig().to_dict(), indent=2)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")
    return destination
