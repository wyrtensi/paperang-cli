from __future__ import annotations

import pytest

from paperang_cli.config import PaperangCliConfig
from paperang_cli.drivers.paperang_p1 import PaperangP1Driver
from paperang_cli.drivers.registry import get_driver, supported_models
from paperang_cli.errors import ConfigError


def test_get_driver_returns_p1_driver():
    driver = get_driver(PaperangCliConfig(model="paperang_p1"))
    assert isinstance(driver, PaperangP1Driver)


def test_get_driver_rejects_unknown_model():
    with pytest.raises(ConfigError):
        get_driver(PaperangCliConfig(model="unknown_model"))


def test_supported_models_contains_p1():
    assert supported_models() == ["paperang_p1"]