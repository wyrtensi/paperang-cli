"""Configuration loading for the standalone paperang-cli project."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from paperang_cli.errors import ConfigError

DEFAULT_DISCOVERY_NAMES = ["MiaoMiaoJi", "Paperang", "Paperang_P2S"]
VALID_FONT_FAMILIES = {"sans", "mono", "serif"}
VALID_ORIENTATIONS = {"normal", "rotate-90-cw", "rotate-90-ccw"}
VALID_IMAGE_MODES = {"sticker", "photo"}
VALID_IMAGE_CONVERSIONS = {"threshold", "edge", "dither"}
VALID_COMPOSE_LAYOUTS = {"text-above", "image-above"}


@dataclass(slots=True)
class TextPrintDefaults:
    font_family: str = "sans"
    font_size: int | None = None
    min_font_size: int | None = None
    autofit: bool = False
    orientation: str = "normal"
    horizontal_padding_px: int | None = None
    vertical_padding_px: int | None = None
    line_spacing_px: int | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "TextPrintDefaults":
        payload = data or {}
        return cls(
            font_family=_normalize_string_choice(payload.get("font_family", "sans"), default="sans"),
            font_size=_optional_int(payload.get("font_size")),
            min_font_size=_optional_int(payload.get("min_font_size")),
            autofit=bool(payload.get("autofit", False)),
            orientation=_normalize_string_choice(payload.get("orientation", "normal"), default="normal"),
            horizontal_padding_px=_optional_int(payload.get("horizontal_padding_px")),
            vertical_padding_px=_optional_int(payload.get("vertical_padding_px")),
            line_spacing_px=_optional_int(payload.get("line_spacing_px")),
        )

    def validate(self, *, label: str) -> None:
        if self.font_family not in VALID_FONT_FAMILIES:
            raise ConfigError(f"{label}.font_family must be one of: {', '.join(sorted(VALID_FONT_FAMILIES))}")
        if self.orientation not in VALID_ORIENTATIONS:
            raise ConfigError(f"{label}.orientation must be one of: {', '.join(sorted(VALID_ORIENTATIONS))}")

        _validate_optional_positive_int(self.font_size, f"{label}.font_size")
        _validate_optional_positive_int(self.min_font_size, f"{label}.min_font_size")
        _validate_optional_non_negative_int(self.horizontal_padding_px, f"{label}.horizontal_padding_px")
        _validate_optional_non_negative_int(self.vertical_padding_px, f"{label}.vertical_padding_px")
        _validate_optional_non_negative_int(self.line_spacing_px, f"{label}.line_spacing_px")

        if self.font_size is not None and self.min_font_size is not None and self.min_font_size > self.font_size:
            raise ConfigError(f"{label}.min_font_size must be less than or equal to {label}.font_size")


@dataclass(slots=True)
class ImagePrintDefaults:
    mode: str = "sticker"
    conversion: str | None = None
    orientation: str = "normal"

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "ImagePrintDefaults":
        payload = data or {}
        conversion_value = payload.get("conversion")
        return cls(
            mode=_normalize_string_choice(payload.get("mode", "sticker"), default="sticker"),
            conversion=_normalize_string_choice(conversion_value) if conversion_value is not None else None,
            orientation=_normalize_string_choice(payload.get("orientation", "normal"), default="normal"),
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


@dataclass(slots=True)
class ComposePrintDefaults:
    font_family: str = "sans"
    font_size: int | None = None
    horizontal_padding_px: int | None = None
    vertical_padding_px: int | None = None
    line_spacing_px: int | None = None
    layout: str = "text-above"
    spacer_height_px: int | None = None
    image_mode: str = "sticker"
    image_conversion: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "ComposePrintDefaults":
        payload = data or {}
        image_conversion = payload.get("image_conversion")
        return cls(
            font_family=_normalize_string_choice(payload.get("font_family", "sans"), default="sans"),
            font_size=_optional_int(payload.get("font_size")),
            horizontal_padding_px=_optional_int(payload.get("horizontal_padding_px")),
            vertical_padding_px=_optional_int(payload.get("vertical_padding_px")),
            line_spacing_px=_optional_int(payload.get("line_spacing_px")),
            layout=_normalize_string_choice(payload.get("layout", "text-above"), default="text-above"),
            spacer_height_px=_optional_int(payload.get("spacer_height_px")),
            image_mode=_normalize_string_choice(payload.get("image_mode", "sticker"), default="sticker"),
            image_conversion=_normalize_string_choice(image_conversion) if image_conversion is not None else None,
        )

    def validate(self, *, label: str) -> None:
        if self.font_family not in VALID_FONT_FAMILIES:
            raise ConfigError(f"{label}.font_family must be one of: {', '.join(sorted(VALID_FONT_FAMILIES))}")
        if self.layout not in VALID_COMPOSE_LAYOUTS:
            raise ConfigError(f"{label}.layout must be one of: {', '.join(sorted(VALID_COMPOSE_LAYOUTS))}")
        if self.image_mode not in VALID_IMAGE_MODES:
            raise ConfigError(f"{label}.image_mode must be one of: {', '.join(sorted(VALID_IMAGE_MODES))}")
        if self.image_conversion is not None and self.image_conversion not in VALID_IMAGE_CONVERSIONS:
            raise ConfigError(
                f"{label}.image_conversion must be one of: {', '.join(sorted(VALID_IMAGE_CONVERSIONS))}"
            )

        _validate_optional_positive_int(self.font_size, f"{label}.font_size")
        _validate_optional_non_negative_int(self.horizontal_padding_px, f"{label}.horizontal_padding_px")
        _validate_optional_non_negative_int(self.vertical_padding_px, f"{label}.vertical_padding_px")
        _validate_optional_non_negative_int(self.line_spacing_px, f"{label}.line_spacing_px")
        _validate_optional_non_negative_int(self.spacer_height_px, f"{label}.spacer_height_px")


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
            text=TextPrintDefaults.from_mapping(_optional_mapping(payload.get("text"), "print_defaults.text")),
            paragraph=TextPrintDefaults.from_mapping(
                _optional_mapping(payload.get("paragraph"), "print_defaults.paragraph")
            ),
            image=ImagePrintDefaults.from_mapping(_optional_mapping(payload.get("image"), "print_defaults.image")),
            compose=ComposePrintDefaults.from_mapping(
                _optional_mapping(payload.get("compose"), "print_defaults.compose")
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


def _normalize_string_choice(value: Any, *, default: str | None = None) -> str:
    if value is None:
        if default is None:
            raise ConfigError("Expected a string value")
        return default
    return str(value).strip().lower()


def _validate_optional_positive_int(value: int | None, field_name: str) -> None:
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


@dataclass(slots=True)
class PaperangCliConfig:
    model: str = "paperang_p1"
    macaddress: str = ""
    printerwidth: int = 384
    print_density: int = 75
    post_print_feed_mm: float = 5.0
    discovery_names: list[str] = field(default_factory=lambda: list(DEFAULT_DISCOVERY_NAMES))
    print_defaults: PrintDefaults = field(default_factory=PrintDefaults)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "PaperangCliConfig":
        defaults = cls()
        config = cls(
            model=str(data.get("model", defaults.model)),
            macaddress=str(data.get("macaddress", defaults.macaddress)),
            printerwidth=int(data.get("printerwidth", defaults.printerwidth)),
            print_density=int(data.get("print_density", defaults.print_density)),
            post_print_feed_mm=float(data.get("post_print_feed_mm", defaults.post_print_feed_mm)),
            discovery_names=list(data.get("discovery_names", DEFAULT_DISCOVERY_NAMES)),
            print_defaults=PrintDefaults.from_mapping(_optional_mapping(data.get("print_defaults"), "print_defaults")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.printerwidth <= 0:
            raise ConfigError("printerwidth must be greater than zero")
        if self.print_density < 0 or self.print_density > 255:
            raise ConfigError("print_density must be between 0 and 255")
        if self.post_print_feed_mm < 0:
            raise ConfigError("post_print_feed_mm must be zero or greater")
        if not self.discovery_names:
            raise ConfigError("discovery_names must contain at least one candidate")
        self.print_defaults.validate()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    if sys.platform == "win32":
        config_home = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
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


def load_config(explicit_path: str | os.PathLike[str] | None = None) -> tuple[PaperangCliConfig, Path, bool]:
    path, source = resolve_config_path(explicit_path)
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Failed to parse config file {path}: {exc}") from exc
        return PaperangCliConfig.from_mapping(raw), path, True

    if source in {"explicit", "environment"}:
        raise ConfigError(f"Config file does not exist: {path}")

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
