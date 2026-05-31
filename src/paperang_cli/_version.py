"""Version helpers sourced from the package version manifest."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

VERSION_MANIFEST_FILE = Path(__file__).with_name("version-manifest.json")


@lru_cache(maxsize=1)
def load_version_manifest() -> dict[str, Any]:
    """Load the package version manifest shipped with paperang-cli."""

    return json.loads(VERSION_MANIFEST_FILE.read_text(encoding="utf-8"))


def get_version() -> str:
    """Return the canonical package version."""

    return str(load_version_manifest()["version"])


__version__ = get_version()