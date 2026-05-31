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


@dataclass(slots=True)
class PaperangCliConfig:
    model: str = "paperang_p1"
    macaddress: str = ""
    printerwidth: int = 384
    print_density: int = 75
    post_print_feed_mm: float = 5.0
    discovery_names: list[str] = field(default_factory=lambda: list(DEFAULT_DISCOVERY_NAMES))

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "PaperangCliConfig":
        config = cls(
            model=str(data.get("model", cls.model)),
            macaddress=str(data.get("macaddress", cls.macaddress)),
            printerwidth=int(data.get("printerwidth", cls.printerwidth)),
            print_density=int(data.get("print_density", cls.print_density)),
            post_print_feed_mm=float(data.get("post_print_feed_mm", cls.post_print_feed_mm)),
            discovery_names=list(data.get("discovery_names", DEFAULT_DISCOVERY_NAMES)),
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
