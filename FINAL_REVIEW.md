# FINAL REVIEW: paperang-cli — план перехода на cross-platform

**Проект:** `paperang-cli` (Paperang thermal printer CLI)
**Версия:** 0.1.8 (manifest: `src/paperang_cli/version-manifest.json:2`)
**Путь:** `E:\Users\wyrte.WYRTENSI.000\Desktop\python-paperang-master - Copy\paperang-cli`
**Дата review:** 2026-06-03
**Область:** cross-platform readiness (Windows / macOS / Linux)
**Метод:** синтез 12 отчётов (Этапы 1–3) + эмпирическая верификация на `C:\`-venv

---

## 0. Executive Summary

`paperang-cli` — это standalone Python-пакет и CLI для термопринтеров Paperang P1 (BLE) и P2 (USB + BLE), плюс npm-обёртка. Текущий релиз 0.1.8 **формально заявляет** поддержку трёх ОС через CI-матрицу (`ubuntu-latest` × `macos-latest` × `windows-latest`), но **фактическая валидация** проведена только на Windows (Python 3.14, bleak WinRT-бэкенд).

**Ключевые находки:**

1. **P0-блокер venv**: в локальной `.venv` установлен `paperang-p2-lib==0.3.7` (USB-only, нет модуля `paperang.transport._ble`), тогда как `pyproject.toml:33` требует `>=0.4.0rc3`. Это означает, что локально P2-BLE полностью неработоспособен, несмотря на «зелёный» CI.
2. **P0 capability detection отсутствует**: нигде в `src/paperang_cli/` нет кода, который бы сообщал пользователю «на твоей ОС нет bleak back-end, или нет libusb, или нет udev rules» в дружелюбной форме.
3. **Документация только для Windows**: README содержит 30 блоков ` ```powershell ` против 1 блока ` ```bash `; `docs/installation.md` и `docs/troubleshooting.md` имеют только «Windows Notes». Пользователь macOS/Linux не имеет скопированной команды.
4. **Classifiers заявляют только Windows**: `pyproject.toml:19` содержит `Operating System :: Microsoft :: Windows` без `POSIX :: Linux` и `MacOS`. PyPI не покажет пакет в фильтре «Linux».
5. **CI-матрица неполная**: `ci.yml:24-27` тестирует Python 3.10/3.12/3.14 — пропущены 3.11 и 3.13, которые заявлены в classifiers (`:22, :24`). Системные зависимости (libusb, bluez) не ставятся.

**Главный блокер:** mismatch версии `paperang-p2-lib` в venv vs constraint в `pyproject.toml` (1 команда `pip install --pre -e ".[dev]"` чинит).

**Общая оценка трудозатрат:** **medium** (1–2 спринта для базовой кросс-платформенной готовности при работе одного разработчика; реальная hardware-валидация на macOS/Linux — отдельная задача, требующая физического железа).

---

## 1. Реальное текущее состояние (Этап 3 подтвердил эмпирически)

### 1.1 Что реально работает (✅ подтверждено)

| Артефакт | Файл / источник | Статус |
|---|---|---|
| Версия пакета 0.1.8 | `src/paperang_cli/version-manifest.json:2` | ✅ |
| Python `>=3.10` заявлен | `pyproject.toml:10` | ✅ |
| CLI entry-point `paperang` + `paperang-cli` | `pyproject.toml:57-59` | ✅ |
| CI матрица: 3 ОС × 3 Python версии | `.github/workflows/ci.yml:20-27` | ✅ |
| Package validation job (twine, wheel contents) | `ci.yml:46-110` | ✅ |
| npm-wrapper validation job | `ci.yml:111-160` | ✅ |
| Agent-skill validation job | `ci.yml:162-184` | ✅ |
| 130 unit/integration тестов | `tests/*.py` (см. §1.4) | ✅ (запускаются на 3 ОС) |
| Classifiers включают Python 3.10/3.11/3.12/3.13/3.14 | `pyproject.toml:20-25` | ✅ |
| Default config path с учётом ОС (`%APPDATA%` vs `$XDG_CONFIG_HOME`) | `src/paperang_cli/config.py:360-366` | ✅ |
| `paperang-p2-lib` constraint `>=0.4.0rc3` (с `--pre`) | `pyproject.toml:33` | ✅ в манифесте, ❌ в venv |
| `prepare_bleak_windows_thread()` graceful no-op на non-Windows | `protocol/hardware_bleak.py:26-34` | ✅ |
| Тест `test_default_config_path_uses_xdg_config_home_when_available` параметризован под `linux` | `tests/test_config.py:30-34` | ✅ |

### 1.2 Что реально сломано (❌ подтверждено)

| Проблема | Файл / строка | Эмпирическое подтверждение |
|---|---|---|
| **P0: venv имеет paperang-p2-lib 0.3.7** (нет `_ble.py`), хотя pyproject требует `>=0.4.0rc3` | `pyproject.toml:33` vs `.venv/Lib/site-packages/paperang/transport/` (только `_base.py`, `_usb.py`) | `importlib.metadata.version('paperang-p2-lib') == 0.3.7`; `hasattr(paperang.transport, '_ble') == False` |
| **P0: нет файла `src/paperang_cli/protocol/_capabilities.py`** | — | `Test-Path` == False |
| **P0: нет файла `tests/test_capabilities.py`** | — | `Test-Path` == False |
| README: 30 блоков ` ```powershell ` vs 1 ` ```bash ` | `README.md` (regex count) | Эмпирически подсчитано |
| `docs/installation.md`: 5 powershell блоков, 0 bash; есть только «Windows Notes» | `docs/installation.md:51-56` | Эмпирически |
| `docs/troubleshooting.md`: 5 powershell блоков, 0 bash; текст ссылается на «Windows BLE state» | `docs/troubleshooting.md:18-20` | Эмпирически |
| `pyproject.toml` classifiers: только `Microsoft :: Windows` | `pyproject.toml:19` | Эмпирически |
| `docs/PLATFORMS.md` не существует | — | `Test-Path` == False |
| CI matrix пропускает Python 3.11 и 3.13 | `ci.yml:24-27` | Эмпирически |
| CI не устанавливает системные deps (libusb, bluez) | `ci.yml:40-41` | Эмпирически |
| CI smoke-job отсутствует | `ci.yml` | Эмпирически |
| Тест `test_default_config_path_uses_xdg_config_home_when_available` параметризован только под `linux`, не под `darwin` | `tests/test_config.py:30-31` | Эмпирически |
| Нет команды `paperang --json capabilities` | `src/paperang_cli/cli.py` (нет group/command) | Эмпирически |

### 1.3 Что работает, но не валидировано на реальном железе (⚠️)

- **P1 BLE** — software-реализация через `bleak` (`protocol/hardware_bleak.py`); протестировано на Windows, не подтверждено на macOS/Linux с реальным принтером.
- **P2 USB** — software-реализация через `paperang-p2-lib` (`drivers/paperang_p2.py`); работает в `0.3.7` (USB-only), будет работать в `0.4.0rc3`.
- **P2 BLE** — software-реализация доступна только в `0.4.0rc3+`; **локально заблокирована** venv.
- **macOS / Linux** — unit-тесты зелёные, но реальное железо не подключалось (честно зафиксировано в `README.md:8` бейджем «Hardware tested on Windows» и в `AGENTS.md:89`).

### 1.4 Сводка тестов (эмпирически)

| Файл | Тестов | Назначение |
|---|---|---|
| `test_api.py` | 15 | API contract, P1/P2 facades |
| `test_check_agent_skill.py` | 9 | Skill bundle sync |
| `test_cli.py` | 29 | CLI subcommands, exit codes, JSON output |
| `test_config.py` | 13 | Config loading, XDG/APPDATA paths |
| `test_driver_styles.py` | 4 | Driver style resolution |
| `test_install_agent_skill.py` | 8 | Portable installer |
| `test_presets.py` | 2 | Style presets |
| `test_registry.py` | 5 | Driver registry |
| `test_render.py` | 31 | Render pipeline |
| `test_style_resolution.py` | 8 | Style selector resolution |
| `test_version_manifest.py` | 3 | Version manifest sync |
| **Итого** | **127 тестов** | (в отчёте Этапа 1 упомянуто 130 — расхождение ~3 за счёт параметризации; оба числа валидны) |

---

## 2. Критические находки (P0 — блокеры)

### 2.1 `paperang-p2-lib` version mismatch (КРИТИЧНО)

- **Проблема:** `pyproject.toml:33` объявляет `paperang-p2-lib>=0.4.0rc3`, но в реальной `.venv` стоит `0.3.7`. Для `0.4.0rc3` нужно `pip install --pre`, чего CI и разработчики могут не делать (CI делает `pip install -e ".[dev]"` без `--pre` в `ci.yml:41`).
- **Следствие:** `from paperang.transport._ble import BleTransport` → `ModuleNotFoundError`. Любой код, использующий P2-BLE (даже неявно через driver fallback), упадёт. Локально это маскирует баги, которые CI в `0.3.7` не увидит.
- **Эмпирически подтверждено:**
  - `importlib.metadata.version('paperang-p2-lib')` → `0.3.7`
  - `paperang/transport/` содержит только `_base.py`, `_usb.py`, `__init__.py` (нет `_ble.py`)
- **Блокирует:** любую работу по P2-BLE, любое тестирование capability detection на P2-BLE.
- **Фикс (P0, 5 минут):**
  1. На dev-машине: `pip install --pre -e ".[dev]"`
  2. В CI: добавить `--pre` в `ci.yml:41` (см. §6)
  3. Опционально: добавить `pip install --pre` в `AGENTS.md` и `docs/development/testing.md`
- **Файлы для изменения:** `pyproject.toml:33` (если хотим ослабить constraint), `.github/workflows/ci.yml:41` (добавить `--pre`).

### 2.2 macOS config path (UX-проблема, не блокер)

- **Проблема:** на macOS `default_config_path()` (`src/paperang_cli/config.py:360-366`) возвращает `~/.config/paperang-cli/...` через XDG-fallback, а не идиоматичный `~/Library/Application Support/paperang-cli/...`.
- **Следствие:** не критично, но неожиданно для macOS-пользователей, привыкших к Apple-овской иерархии. Файлы по-прежнему читаются/пишутся, миграция не сломана, но это «не-Mac-feel».
- **Фикс (P1, 30 минут):**
  ```python
  if sys.platform == "win32":
      config_home = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
  elif sys.platform == "darwin":
      config_home = Path.home() / "Library" / "Application Support"
  else:
      config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
  ```
  + параметризовать тест `test_default_config_path_uses_xdg_config_home_when_available` на три платформы (или добавить отдельный `test_default_config_path_uses_library_on_darwin`).
- **Файлы для изменения:** `src/paperang_cli/config.py:360-366`, `tests/test_config.py:30-34`.

### 2.3 Отсутствие capability detection (P0 архитектурный)

- **Проблема:** нет единой точки, которая бы сообщала пользователю и агенту: «какие транспорты доступны прямо сейчас на этой ОС с этим набором пакетов». Сейчас ошибки импорта (`ModuleNotFoundError`, `AttributeError` от bleak) доходят до пользователя в сыром виде.
- **Следствие:** низкая debuggability, плохой UX на macOS/Linux при первом запуске.
- **Фикс (P0, дизайн см. §4):** новый модуль `src/paperang_cli/protocol/_capabilities.py` + команда `paperang --json capabilities` + тесты `tests/test_capabilities.py`.
- **Файлы для создания:** `src/paperang_cli/protocol/_capabilities.py`, `tests/test_capabilities.py`, `src/paperang_cli/commands/capabilities_cmd.py` (новый), `src/paperang_cli/cli.py` (регистрация команды).

---

## 3. Согласованные приоритеты (Этап 3 унифицировал)

### P0 — блокируют, делать немедленно (1–2 часа)

1. **Зафиксировать правильную версию `paperang-p2-lib` в venv** (`pip install --pre -e ".[dev]"`). Дополнительно: добавить `--pre` в `ci.yml:41`. *Эмпирически: сейчас в venv 0.3.7.*
2. **Создать `src/paperang_cli/protocol/_capabilities.py`** (см. §4).
3. **Создать `tests/test_capabilities.py`** (mock `sys.platform`, `importlib.import_module`).
4. **Добавить команду `paperang --json capabilities`** (новая команда `capabilities`).

### P1 — улучшают качество, делать в ближайшие 1–2 дня

1. Обновить `pyproject.toml:16-27`: добавить `Operating System :: POSIX :: Linux` и `Operating System :: MacOS`.
2. Расширить CI matrix (`ci.yml:24-27`): добавить Python 3.11 и 3.13 → итого 3 ОС × 5 Python = 15 jobs.
3. Добавить `smoke` job в `ci.yml`: установка wheel в чистый venv, `paperang --version`, `python -c "from paperang_cli.protocol._capabilities import report; print(report())"`.
4. Параметризовать `test_default_config_path_uses_xdg_config_home_when_available` для `darwin` (и опционально `win32`/`linux`).
5. Добавить macOS-ветку в `src/paperang_cli/config.py:360-366` (см. §2.2).
6. Upstream PR в `paperang-p2-lib` для `/tmp/` paths (вне нашего репо, но инициировать).
7. Bash-альтернативы в README (минимум 10 критичных команд, см. §7).
8. Linux/macOS секции в `docs/installation.md` (см. §7).
9. Linux/macOS секции в `docs/troubleshooting.md` (см. §7).
10. Установить системные deps в CI: `libusb-1.0-0-dev` на Linux, `libusb` через brew на macOS.

### P2 — отложить, обсудить

1. Vendor `paperang-p2-lib` (стратегия B, 3–5 дней).
2. Native reimplementation (стратегия D, 1–2 недели).
3. Cross-platform npm-wrapper tests (`ci.yml:111-160` сейчас только `ubuntu-latest`).
4. Coverage badge в README.
5. `--json capabilities` в skill bundle.

---

## 4. Единый дизайн capability detection (Этап 3 §2)

### Цель

Один модуль, который:
1. Проверяет, доступен ли `bleak` и какой back-end он использует на текущей ОС.
2. Проверяет, установлен ли `paperang-p2-lib` и в какой версии (BLE/USB).
3. Проверяет системные зависимости (libusb, bluez, udev rules) насколько возможно из Python без root.
4. Возвращает структурированный отчёт для CLI/JSON/agent consumption.

### API

**Файл:** `src/paperang_cli/protocol/_capabilities.py`

```python
from __future__ import annotations
from dataclasses import dataclass, asdict
import importlib
import importlib.util
import platform
import shutil
import sys
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
    return Capability("bleak.imported", True, f"bleak {importlib.metadata.version('bleak')}", "package")


def bleak_backends() -> Capability:
    """Best-effort detection of bleak backends per platform."""
    sysname = sys.platform
    if sysname == "win32":
        return Capability("bleak.backend", True, "WinRT (Windows)", "system")
    if sysname == "darwin":
        return Capability("bleak.backend", True, "CoreBluetooth (macOS) — requires user permission", "permission")
    return Capability("bleak.backend", True, "BlueZ DBus (Linux) — requires bluez service + dbus", "system")


def bleak_can_scan() -> Capability:
    """Whether bleak can actually scan on this platform without extra setup."""
    if sys.platform == "darwin":
        return Capability("bleak.scan", True, "May require Info.plist NSBluetoothAlwaysUsageDescription or first-run prompt", "permission")
    if sys.platform.startswith("linux"):
        bluez = shutil.which("bluetoothd") or shutil.which("bluetooth")
        if not bluez:
            return Capability("bleak.scan", False, "bluez not found in PATH", "system")
        return Capability("bleak.scan", True, "bluez detected; user must be in 'bluetooth' group", "system")
    return bleak_backends()  # Windows works out of the box


def paperang_p2_lib_version() -> Capability:
    try:
        v = importlib.metadata.version("paperang-p2-lib")
        # v0.3.x = USB only; v0.4.0rc3+ = USB + BLE
        major, minor, *_ = v.split(".")
        if int(minor) >= 4 or "rc" in v:
            return Capability("paperang-p2-lib", True, f"v{v} (USB + BLE)", "package")
        return Capability("paperang-p2-lib", True, f"v{v} (USB only — P2 BLE unavailable, upgrade: pip install --pre -U paperang-p2-lib)", "package")
    except importlib.metadata.PackageNotFoundError:
        return Capability("paperang-p2-lib", False, "Not installed; pip install paperang-p2-lib", "package")


def usb_p2_available() -> Capability:
    """Whether pyusb + libusb is available."""
    if importlib.util.find_spec("usb") is None:
        return Capability("p2.usb", False, "pyusb not installed", "package")
    if sys.platform.startswith("linux"):
        return Capability("p2.usb", True, "May require udev rules (see docs/installation.md#linux)", "permission")
    if sys.platform == "darwin":
        return Capability("p2.usb", True, "May require libusb via brew install libusb", "system")
    return Capability("p2.usb", True, "libusb via WinUSB / Zadig driver", "system")


def report() -> list[dict]:
    """Return all capability checks as a list of dicts (JSON-serializable)."""
    return [
        bleak_imported().to_dict(),
        bleak_backends().to_dict(),
        bleak_can_scan().to_dict(),
        paperang_p2_lib_version().to_dict(),
        usb_p2_available().to_dict(),
    ]
```

### CLI интеграция

**Новый файл:** `src/paperang_cli/commands/capabilities_cmd.py`

```python
import click
import json as _json
from paperang_cli.protocol._capabilities import report

@click.command("capabilities")
@click.pass_context
def capabilities_command(ctx: click.Context) -> None:
    """Print detected runtime capabilities (transport availability, versions, permissions)."""
    payload = {"status": "ok", "capabilities": report()}
    if ctx.obj.get("json_output"):
        click.echo(_json.dumps(payload, indent=2))
    else:
        for cap in payload["capabilities"]:
            mark = "OK " if cap["available"] else "FAIL"
            click.echo(f"[{mark}] {cap['name']}: {cap['detail']} (layer={cap['layer']})")
```

**Регистрация в `src/paperang_cli/cli.py:12-19`:** добавить импорт и `cli.add_command(capabilities_command)`.

### Тесты

**Новый файл:** `tests/test_capabilities.py`

```python
from unittest.mock import patch
from paperang_cli.protocol import _capabilities as caps


def test_bleak_imported_missing():
    with patch("paperang_cli.protocol._capabilities.importlib.util.find_spec", return_value=None):
        cap = caps.bleak_imported()
    assert cap.available is False
    assert cap.layer == "package"


def test_paperang_p2_lib_usb_only_version():
    with patch("paperang_cli.protocol._capabilities.importlib.metadata.version", return_value="0.3.7"):
        cap = caps.paperang_p2_lib_version()
    assert cap.available is True
    assert "USB only" in cap.detail


def test_paperang_p2_lib_full_version():
    with patch("paperang_cli.protocol._capabilities.importlib.metadata.version", return_value="0.4.0rc3"):
        cap = caps.paperang_p2_lib_version()
    assert "USB + BLE" in cap.detail


@pytest.mark.parametrize("plat,expected_marker", [
    ("darwin", "Info.plist"),
    ("linux", "bluez"),
    ("win32", "WinRT"),
])
def test_bleak_backends_per_platform(plat, expected_marker):
    with patch("paperang_cli.protocol._capabilities.sys.platform", plat):
        cap = caps.bleak_can_scan()
    assert expected_marker in cap.detail or cap.available is True
```

---

## 5. Единый план фикса paperang-p2-lib (Этап 3 §3)

| Шаг | Стратегия | Effort | Риск | Когда | Действие |
|---|---|---|---|---|---|
| 1 | Constraint fix | low (5 мин) | низкий | **P0 сейчас** | `pip install --pre -e ".[dev]"` + добавить `--pre` в `ci.yml:41` |
| 2 | Upstream PR | medium (1–2 дня) | низкий | P1 | PR в `paperang-p2-lib` для использования `tempfile.gettempdir()` вместо `/tmp/` |
| 3 | Vendor | high (3–5 дней) | средний | P2 (если upstream мёртв) | Скопировать `paperang/transport/_ble.py` в `src/paperang_cli/_vendor/`, добавить `# Vendored from paperang-p2-lib 0.4.0rc3` |
| 4 | Native reimpl | very high (1–2 недели) | высокий | P2 (если 3 не поможет) | Написать BLE-транспорт напрямую через `bleak`, без `paperang-p2-lib` |

**Текущая рекомендация:** шаг 1 немедленно, шаг 2 в ближайший спринт, шаги 3–4 — только если появится эвиденс, что upstream заморожен.

---

## 6. Согласованный CI план (Этап 2 §3.3 + Этап 3 §6)

### Расширенный `test` job

**Файл:** `.github/workflows/ci.yml:14-44`

**Изменения:**
1. Добавить Python 3.11 и 3.13 в matrix (`:24-27`).
2. Добавить системные deps для Linux: `sudo apt-get install -y libusb-1.0-0-dev bluez`.
3. Добавить системные deps для macOS: `brew install libusb`.
4. Изменить `pip install -e ".[dev]"` → `pip install --pre -e ".[dev]"` (важно для P2-BLE).
5. Добавить `env: PAPERANG_CLI_SKIP_HARDWARE=1` для всех test-job-ов.

**Результат:** 3 ОС × 5 Python = 15 jobs.

### Новый `smoke` job (после `test`)

```yaml
smoke:
  name: Smoke test on ${{ matrix.os }}
  runs-on: ${{ matrix.os }}
  strategy:
    fail-fast: false
    matrix:
      os: [ubuntu-latest, macos-latest, windows-latest]
  steps:
    - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      with:
        persist-credentials: false
    - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0e869d46889d02405 # v6.2.0
      with:
        python-version: "3.12"
    - name: Install system dependencies (Linux)
      if: matrix.os == 'ubuntu-latest'
      run: sudo apt-get update && sudo apt-get install -y libusb-1.0-0-dev bluez
    - name: Install system dependencies (macOS)
      if: matrix.os == 'macos-latest'
      run: brew install libusb
    - run: python -m pip install --pre .
    - name: Verify CLI entrypoints
      run: |
        paperang --version
        paperang --help
        python -c "import paperang_cli; print('imported OK', paperang_cli.__version__)"
    - name: Verify capability report
      run: |
        paperang --json capabilities
        python -c "from paperang_cli.protocol._capabilities import report; import json; print(json.dumps(report(), indent=2))"
```

**Результат:** 3 jobs (по одному на ОС).

### Расширенный `package` job

**Изменения в `ci.yml:46-110`:**
1. Добавить matrix: `os: [ubuntu-latest, macos-latest, windows-latest]`, `python-version: ["3.12"]`.
2. На каждой ОС: тот же набор шагов (build, twine check, wheel contents, version-manifest sync).

**Результат:** 3 jobs (по одному на ОС) вместо текущего 1.

### Расширенный `npm-wrapper` job

**Изменения в `ci.yml:111-160`:**
1. Добавить matrix: `os: [ubuntu-latest, macos-latest, windows-latest]`.
2. На каждой ОС: `npm ci --ignore-scripts` + `npm test` + `npm pack --dry-run`.

**Результат:** 3 jobs вместо текущего 1.

### Расширенный `agent-skill` job

**Изменения в `ci.yml:162-184`:**
1. Добавить matrix: `os: [ubuntu-latest, macos-latest, windows-latest]`.
2. На каждой ОС: `python scripts/check-agent-skill.py` + `pytest tests/test_install_agent_skill.py tests/test_check_agent_skill.py`.

**Результат:** 3 jobs вместо текущего 1.

### `publish` jobs

- **pypi-publish.yml** — оставить `ubuntu-latest` (OIDC trusted publishing, нечего усложнять).
- **npm-publish.yml** — оставить `ubuntu-latest` по той же причине.

### Итоговый CI budget

| Job | Сейчас | Планируется |
|---|---|---|
| test | 9 (3×3) | 15 (3×5) |
| package | 1 | 3 |
| npm-wrapper | 1 | 3 |
| agent-skill | 1 | 3 |
| smoke | 0 | 3 |
| **Итого** | **12** | **27** |

GitHub Actions free tier для public repos — 2000 мин/мес; 27 jobs × ~3 мин = ~80 мин на PR. Приемлемо.

---

## 7. Согласованный документационный план (Этап 2 §4 + §7)

### 7.1 Новый файл: `docs/PLATFORMS.md` (Single Source of Truth)

```markdown
# Platform Support Matrix

This document is the single source of truth for cross-platform support claims.
Update it whenever validation status changes.

## Per-printer support

| Printer | Transport | Windows | macOS | Linux |
| --- | --- | --- | --- | --- |
| Paperang P1 | BLE | ✅ Tested (Python 3.14) | ⚠️ Untested (software only) | ⚠️ Untested (software only) |
| Paperang P2 | USB | ✅ Software (libusb/WinUSB) | ⚠️ Untested | ⚠️ Untested |
| Paperang P2 | BLE | ⚠️ Requires paperang-p2-lib 0.4.0rc3+ | ⚠️ Untested | ⚠️ Untested |

## Per-OS validation status

| OS | CI runs | Hardware tested | Last validation date |
| --- | --- | --- | --- |
| Windows | ✅ | ✅ Python 3.14 + P1 BLE | 2026-06-01 |
| macOS | ✅ | ❌ (no hardware in CI) | — |
| Linux | ✅ | ❌ (no hardware in CI) | — |

## Versioned history

- 0.1.8: Initial macOS/Linux CI matrix without hardware validation.
```

### 7.2 Обновить `docs/installation.md`

**Изменения:**
- Переименовать «## Windows Notes» → «## Windows» (выше) и добавить «## macOS», «## Linux» (ниже).
- macOS секция: `brew install libusb`, Info.plist permission (для разработчиков GUI-обёрток).
- Linux секция: `apt/dnf install bluez libusb-1.0-0-dev`, udev rules (если есть), `setcap` для USB.
- Troubleshooting table в конце с common pitfalls.

### 7.3 Обновить `docs/troubleshooting.md`

**Изменения:**
- macOS: «Bluetooth permission not granted» (System Settings → Privacy & Security → Bluetooth), «libusb not found» (`brew install libusb`).
- Linux: «bluez not running» (`systemctl status bluetooth`), «user not in 'bluetooth' group» (`sudo usermod -aG bluetooth $USER`), «udev rules missing» (ссылка на template).
- Убрать жёсткие ссылки на «Windows BLE state» (строка 18-20) — заменить на нейтральные формулировки.

### 7.4 Обновить `README.md`

**Изменения:**
- Quick Start в трёх форматах: `### Windows (PowerShell)`, `### macOS / Linux (bash)` (минимум 10 критичных команд).
- Cross-Platform Compatibility таблица (идентична `docs/PLATFORMS.md`).
- Cross-platform note после Quick Start: «CI runs on all 3 OS, but real hardware is tested only on Windows — see [PLATFORMS.md](docs/PLATFORMS.md).»
- Сохранить бейдж `![Hardware tested on Windows]`.

### 7.5 Classifiers (`pyproject.toml:16-27`)

**Изменения:**
```toml
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS",                # NEW
    "Operating System :: POSIX :: Linux",       # NEW
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: System :: Hardware :: Hardware Drivers",
]
```

---

## 8. Сводная таблица решений (Этап 3 §14)

| # | Задача | P | Effort | Файлы | Конкретный шаг |
|---|---|---|---|---|---|
| 1 | Зафиксировать paperang-p2-lib 0.4.0rc3 в venv | P0 | 5 мин | `pip install --pre -e ".[dev]"` | Выполнить команду локально, верифицировать `importlib.metadata.version('paperang-p2-lib') == '0.4.0rc3'` |
| 2 | Добавить `--pre` в CI install | P0 | 1 мин | `.github/workflows/ci.yml:41` | Заменить `python -m pip install -e ".[dev]"` на `python -m pip install --pre -e ".[dev]"` |
| 3 | Создать `protocol/_capabilities.py` | P0 | 1 час | `src/paperang_cli/protocol/_capabilities.py` (новый) | Реализовать API из §4 |
| 4 | Создать `tests/test_capabilities.py` | P0 | 30 мин | `tests/test_capabilities.py` (новый) | Покрыть все 5 функций + параметризация по `sys.platform` |
| 5 | Добавить команду `capabilities` | P0 | 20 мин | `src/paperang_cli/commands/capabilities_cmd.py` (новый), `src/paperang_cli/cli.py:12-19` | Создать файл команды, зарегистрировать в cli.py |
| 6 | Обновить classifiers | P1 | 5 мин | `pyproject.toml:16-27` | Добавить `MacOS` и `POSIX :: Linux` |
| 7 | Расширить CI matrix Python | P1 | 5 мин | `ci.yml:24-27` | Добавить `3.11` и `3.13` |
| 8 | Добавить smoke job | P1 | 30 мин | `ci.yml` (после test job) | Скопировать YAML из §6 |
| 9 | Параметризовать XDG-тест для darwin | P1 | 15 мин | `tests/test_config.py:30-34` | Добавить `test_default_config_path_uses_library_on_darwin` или parametrize |
| 10 | macOS-ветка в config.py | P1 | 15 мин | `src/paperang_cli/config.py:360-366` | Добавить `elif sys.platform == "darwin"` блок |
| 11 | Upstream PR для /tmp/ paths | P1 | 1–2 дня | внешний репо | PR в `paperang-p2-lib` с заменой `/tmp/` на `tempfile.gettempdir()` |
| 12 | Bash-альтернативы в README | P1 | 2 часа | `README.md` | Добавить 10+ bash-блоков (Quick Start, install, dev mode, first safe commands) |
| 13 | Linux/macOS секции в installation.md | P1 | 2 часа | `docs/installation.md:51-56` | Переструктурировать в три секции |
| 14 | Linux/macOS секции в troubleshooting.md | P1 | 1 час | `docs/troubleshooting.md:1-92` | Добавить per-OS секции |
| 15 | Создать `docs/PLATFORMS.md` | P1 | 1 час | `docs/PLATFORMS.md` (новый) | Содержимое из §7.1 |
| 16 | Системные deps в CI (Linux/macOS) | P1 | 30 мин | `ci.yml:40-44` | `apt-get install` / `brew install` шаги |
| 17 | Vendor paperang-p2-lib | P2 | 3–5 дней | `src/paperang_cli/_vendor/` (новый) | Только если upstream мёртв |
| 18 | Native reimpl BLE | P2 | 1–2 недели | новый файл | Только если стратегия 17 не поможет |
| 19 | Cross-platform npm-wrapper tests | P2 | 30 мин | `ci.yml:111-160` | Добавить matrix os |
| 20 | Coverage badge в README | P2 | 30 мин | `README.md`, `ci.yml` | Опционально |

**Сводка по effort:**
- P0: ~2–3 часа (задачи 1–5).
- P1: ~10–12 часов (задачи 6–16).
- P2: 1–3 недели (задачи 17–20, опционально).

---

## 9. Реальные риски и митигации

| # | Риск | Вероятность | Импакт | Митигация |
|---|---|---|---|---|
| 1 | `paperang-p2-lib` upstream заморожен | medium | P2 USB/BLE сломается | P0: constraint fix; P1: upstream PR; P2: vendor/native |
| 2 | macOS Bluetooth permission flow (Info.plist / first-run prompt) | high | discover возвращает 0 устройств | P1: документировать в `docs/installation.md#macos` |
| 3 | Linux bluez/udev/dbus не настроен | high (зависит от дистрибутива) | BLE не работает, USB permission denied | P1: документировать в `docs/installation.md#linux` + capability detection |
| 4 | pyusb на Windows без Zadig/WinUSB | medium | P2 USB не работает | P1: документировать в `docs/installation.md#windows` + capability detection |
| 5 | `paperang-p2-lib 0.4.0` stable breaking changes | low (ещё не вышел) | P2 USB/BLE может сломаться | P1: добавить constraint `<0.5` в `pyproject.toml:33` |
| 6 | Numba/scipy не имеют wheels для Python 3.14 на всех платформах | low | install падает | Уже работает (CI зелёный), но мониторить при апгрейдах |
| 7 | Тесты flaky из-за timing на медленном CI | medium | CI красный ложно | P1: добавить retry, увеличить timeout в `pytest` |
| 8 | npm-wrapper postinstall конфликтует с PEP 668 externally-managed-environment | high (на Linux) | npm install падает | P1: документировать workaround (использовать venv или `--break-system-packages` в dev) |
| 9 | Реальная hardware-валидация macOS/Linux не произойдёт в обозримом | high | пользователи macOS/Linux получают «software-only» статус | Документировать честно, добавить `docs/PLATFORMS.md` (см. §7.1) |
| 10 | pyusb + macOS Sonoma+ требует дополнительной подписи | low | USB на macOS не работает | Мониторить issues, документировать при появлении |

---

## 10. Definition of Done

Кросс-платформенная готовность достигнута, когда выполнены **все** пункты:

### Установка и запуск
- [ ] `pip install paperang-cli` работает на чистых Ubuntu, macOS, Windows (PowerShell).
- [ ] `pip install --pre -e ".[dev]"` устанавливает `paperang-p2-lib>=0.4.0rc3` (verified через `pip show`).
- [ ] `paperang --version` возвращает `0.1.8+` на всех 3 ОС.
- [ ] `paperang --help` показывает subcommands, включая новый `capabilities`.

### Capability detection
- [ ] `paperang --json capabilities` возвращает структурированный отчёт на всех 3 ОС.
- [ ] На macOS отчёт упоминает Info.plist permission.
- [ ] На Linux отчёт упоминает bluez, group membership, udev rules.
- [ ] На Windows отчёт упоминает bleak WinRT и Zadig/WinUSB для P2 USB.

### CI
- [ ] CI зелёный: 3 ОС × 5 Python = 15 jobs (test) + 3 jobs (smoke) + 3 jobs (package) + 3 jobs (npm-wrapper) + 3 jobs (agent-skill) = **27 jobs**.
- [ ] Все jobs ставят системные deps (libusb, bluez).
- [ ] Все jobs используют `pip install --pre`.

### Тесты
- [ ] 127+ существующих тестов проходят на всех 3 ОС.
- [ ] Новые тесты `test_capabilities.py` (≥5) проходят.
- [ ] Параметризованный тест для darwin в `test_config.py` проходит.

### Документация
- [ ] README имеет bash-альтернативы для всех 10+ критичных команд.
- [ ] `docs/installation.md` имеет секции для Windows / macOS / Linux с per-OS install instructions.
- [ ] `docs/troubleshooting.md` имеет per-OS секции.
- [ ] `docs/PLATFORMS.md` существует и является single source of truth для support matrix.
- [ ] `pyproject.toml` classifiers включают `MacOS` и `POSIX :: Linux`.
- [ ] `CHANGELOG.md` имеет «Platform impact» секцию для следующего релиза.

### Честность (критично)
- [ ] Hardware validation: только Windows, явно задокументировано в `docs/PLATFORMS.md`, `README.md`, `AGENTS.md`.
- [ ] Бейдж «Hardware tested on Windows» сохранён.
- [ ] Нет ложных заявлений «fully tested on macOS/Linux».

---

## 11. Заключение

**`paperang-cli` уже кросс-платформенный по архитектуре** (CI бежит на 3 ОС, пакет собирается wheels, тесты зелёные) и **нуждается в финишной косметике + честной документации**, чтобы это стало правдой и для пользователя, а не только для CI-инженера.

**Реалистично за 1 спринт (1 неделя, один разработчик):**
- Закрыть все P0 (2–3 часа): починить `paperang-p2-lib`, добавить capability detection.
- Закрыть 70% P1 (5–6 дней): расширить CI, добавить документацию, обновить classifiers, добавить bash-альтернативы.
- Definition of Done (§10) достижим.

**Реалистично за 2 спринта (2 недели):**
- Все P0 + P1.
- Плюс одна итерация review/правок по фидбеку от тестового пользователя на macOS (без реального принтера, но с `paperang --json capabilities` + `paperang discover`).

**Что потребует значительно больше времени:**
- Реальная hardware-валидация на macOS и Linux (требует физического принтера + ручного тестирования, не автоматизируется).
- Vendor или native reimpl `paperang-p2-lib` (стратегии B/D) — только если upstream заморожен, что пока не подтверждено.

**Чего НЕ ожидать:**
- Полностью автоматической hardware-валидации macOS/Linux в CI — GitHub Actions runners не имеют Bluetooth-адаптеров, подключённых к Paperang-принтерам, и не имеют USB-портов, доступных runner-у в общем случае.
- «Бесплатного» фикса macOS config path без миграции (если есть пользователи с уже созданными `~/.config/paperang-cli/...` — нужно решить, переносить ли их в `~/Library/Application Support/`).
- 100% test coverage нового `capabilities` модуля — достаточно параметризованного теста на 3 платформы × 5 функций = 15 кейсов.

**Главный takeaway:** `paperang-cli` — зрелый проект, который уже работает на трёх ОС на уровне unit/integration тестов и CLI contract. Финальный шаг — дать пользователю **честный ответ** на вопрос «а у меня-то это запустится?», что и есть capability detection + обновлённая документация.
