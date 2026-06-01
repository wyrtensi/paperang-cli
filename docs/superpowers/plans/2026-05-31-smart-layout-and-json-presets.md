# Smart Layout and JSON Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JSON-controlled scenario presets, measurable dry-run length reporting, generalized text autofit, and optional image length budgeting for `paperang_p1`.

**Architecture:** Extend config with calibration and layout-budget fields, add a preset catalog plus a style-resolution layer, teach the render pipeline to measure and enforce length constraints, then surface the resolved layout through CLI, Python API, docs, and contracts. The new operator control path is JSON-first: per-invocation JSON selects presets and carries structured overrides.

**Tech Stack:** Python 3.10+, Click, dataclasses, Pillow, pytest, Markdown, JSON

---

### Task 1: Config schema and built-in preset catalog

**Files:**
- Create: `src/paperang_cli/presets.py`
- Modify: `src/paperang_cli/config.py`
- Modify: `paperang-cli.config.example.json`
- Test: `tests/test_config.py`
- Test: `tests/test_presets.py`

- [ ] **Step 1: Write the failing config and preset tests**

Add tests like these:

```python
from paperang_cli.config import PaperangCliConfig
from paperang_cli.presets import get_builtin_presets


def test_config_accepts_calibration_and_text_length_budget():
    settings = PaperangCliConfig.from_mapping(
        {
            "calibration": {"printable_width_mm": 44.0, "advance_mm_per_px": 0.1217},
            "print_defaults": {
                "text": {
                    "max_length_mm": 72.0,
                    "overflow_policy": "shrink-to-fit",
                    "break_long_words": True,
                },
                "image": {"fit_mode": "fit-width"},
                "compose": {"overflow_policy": "report-only"},
            },
        }
    )

    assert settings.calibration.printable_width_mm == 44.0
    assert settings.calibration.advance_mm_per_px == 0.1217
    assert settings.print_defaults.text.max_length_mm == 72.0
    assert settings.print_defaults.text.overflow_policy == "shrink-to-fit"
    assert settings.print_defaults.text.break_long_words is True
    assert settings.print_defaults.image.fit_mode == "fit-width"
    assert settings.print_defaults.compose.overflow_policy == "report-only"


def test_builtin_presets_include_address_label_and_logo_strip():
    presets = get_builtin_presets()

    assert presets["address-label"]["target"] == "paragraph"
    assert presets["address-label"]["paragraph"]["orientation"] == "rotate-90-cw"
    assert presets["logo-strip"]["target"] == "image"
    assert presets["logo-strip"]["image"]["orientation"] == "rotate-90-cw"
```

- [ ] **Step 2: Run the tests to confirm the schema and catalog are missing**

Run:

```powershell
python -m pytest -q tests/test_config.py tests/test_presets.py -v
```

Expected: FAIL with missing attributes such as `calibration`, missing validation fields such as `fit_mode`, and `ModuleNotFoundError` for `paperang_cli.presets`.

- [ ] **Step 3: Implement the new config dataclasses and built-in preset module**

Add the config types and fields in `src/paperang_cli/config.py` and create `src/paperang_cli/presets.py`.

Core additions should look like this:

```python
@dataclass(slots=True)
class CalibrationSettings:
    printable_width_mm: float = 44.0
    advance_mm_per_px: float = 0.1217

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None = None) -> "CalibrationSettings":
        payload = data or {}
        return cls(
            printable_width_mm=float(payload.get("printable_width_mm", 44.0)),
            advance_mm_per_px=float(payload.get("advance_mm_per_px", 0.1217)),
        )

    def validate(self) -> None:
        if self.printable_width_mm <= 0:
            raise ConfigError("calibration.printable_width_mm must be greater than zero")
        if self.advance_mm_per_px <= 0:
            raise ConfigError("calibration.advance_mm_per_px must be greater than zero")


BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "receipt-note": {
        "target": "paragraph",
        "description": "Short receipt-style note or checklist.",
        "paragraph": {
            "font_family": "sans",
            "font_size": 24,
            "autofit": True,
            "max_length_mm": 80.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": True,
        },
    },
    "address-label": {
        "target": "paragraph",
        "description": "Long address-style label printed along the paper path.",
        "paragraph": {
            "font_family": "mono",
            "font_size": 30,
            "min_font_size": 14,
            "autofit": True,
            "orientation": "rotate-90-cw",
            "max_length_mm": 90.0,
            "overflow_policy": "shrink-to-fit",
            "break_long_words": True,
        },
    },
}


def get_builtin_presets() -> dict[str, dict[str, Any]]:
    return deepcopy(BUILTIN_PRESETS)
```

Also extend the example config with `calibration`, the new `print_defaults` fields, and an example `presets.address-label` entry.

- [ ] **Step 4: Re-run the config and preset tests**

Run:

```powershell
python -m pytest -q tests/test_config.py tests/test_presets.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the schema baseline**

Run:

```powershell
git add src/paperang_cli/config.py src/paperang_cli/presets.py paperang-cli.config.example.json tests/test_config.py tests/test_presets.py
git commit -m "feat: add layout calibration and preset schema"
```

### Task 2: Style resolution and one-shot JSON overrides

**Files:**
- Create: `src/paperang_cli/style_resolution.py`
- Test: `tests/test_style_resolution.py`
- Modify: `src/paperang_cli/presets.py`

- [ ] **Step 1: Write the failing style-resolution tests**

Add tests like these:

```python
from paperang_cli.style_resolution import resolve_operation_style


def test_style_resolution_merges_defaults_preset_json_and_cli():
    resolved = resolve_operation_style(
        operation="paragraph",
        print_defaults={
            "font_family": "sans",
            "font_size": 24,
            "max_length_mm": None,
        },
        presets={
            "address-label": {
                "paragraph": {
                    "font_family": "mono",
                    "font_size": 30,
                    "orientation": "rotate-90-cw",
                    "max_length_mm": 90.0,
                }
            }
        },
        style_json_payload={"preset": "address-label", "paragraph": {"max_length_mm": 75.0}},
        cli_overrides={"font_size": 28},
    )

    assert resolved["font_family"] == "mono"
    assert resolved["font_size"] == 28
    assert resolved["orientation"] == "rotate-90-cw"
    assert resolved["max_length_mm"] == 75.0


def test_style_resolution_rejects_unknown_preset():
    with pytest.raises(ValueError, match="Unknown preset"):
        resolve_operation_style(
            operation="text",
            print_defaults={},
            presets={},
            style_json_payload={"preset": "missing"},
            cli_overrides={},
        )
```

- [ ] **Step 2: Run the style-resolution tests and confirm the missing module**

Run:

```powershell
python -m pytest -q tests/test_style_resolution.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'paperang_cli.style_resolution'`.

- [ ] **Step 3: Implement deterministic style merging and JSON loading**

Create `src/paperang_cli/style_resolution.py` with helpers that keep precedence in one place.

Use a structure like this:

```python
def resolve_operation_style(
    *,
    operation: str,
    print_defaults: dict[str, Any],
    presets: dict[str, dict[str, Any]],
    style_json_payload: dict[str, Any] | None,
    cli_overrides: dict[str, Any],
) -> dict[str, Any]:
    resolved = dict(print_defaults)

    inherited_preset = style_json_payload.get("preset") if style_json_payload else None

    if inherited_preset:
        try:
            resolved.update(presets[inherited_preset].get(operation, {}))
        except KeyError as exc:
            raise ValueError(f"Unknown preset: {inherited_preset}") from exc

    if style_json_payload:
        resolved.update(style_json_payload.get(operation, {}))

    resolved.update({key: value for key, value in cli_overrides.items() if value is not None})
    return resolved
```

Keep file loading separate from merging so the same resolution logic works for CLI and Python API.

- [ ] **Step 4: Re-run the style-resolution tests**

Run:

```powershell
python -m pytest -q tests/test_style_resolution.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the resolution layer**

Run:

```powershell
git add src/paperang_cli/style_resolution.py src/paperang_cli/presets.py tests/test_style_resolution.py
git commit -m "feat: add preset and style json resolution"
```

### Task 3: Text wrapping, fit loop, and physical length estimation

**Files:**
- Modify: `src/paperang_cli/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing render tests for wrapping and measurement**

Add tests like these:

```python
def test_render_text_job_preserves_hard_breaks(monkeypatch):
    rendered = render_text_job(
        "Line one\nLine two",
        printer_width=384,
        font_size=24,
        max_length_mm=80.0,
        break_long_words=True,
    )

    assert rendered.render_height_px > 0
    assert rendered.estimated_length_mm > 0
    assert rendered.fits_length_budget is True


def test_render_text_job_breaks_long_words_when_enabled():
    rendered = render_text_job(
        "SUPERCALIFRAGILISTICEXPIALIDOCIOUS",
        printer_width=384,
        font_size=24,
        break_long_words=True,
    )

    assert rendered.width == 384


def test_render_text_job_shrinks_until_length_budget_fits(monkeypatch):
    monkeypatch.setattr(
        "paperang_cli.render._render_text_canvas",
        lambda *args, font_size, **kwargs: Image.new("L", (200, font_size * 8), 255),
    )

    rendered = render_text_job(
        "long label",
        printer_width=384,
        font_size=32,
        min_font_size=10,
        autofit=True,
        max_length_mm=24.0,
        overflow_policy="shrink-to-fit",
        advance_mm_per_px=0.1217,
    )

    assert rendered.styling.font_size < 32
    assert rendered.fits_length_budget is True
    assert rendered.estimated_length_mm <= 24.0
```

- [ ] **Step 2: Run the render tests and confirm the new arguments and fields are missing**

Run:

```powershell
python -m pytest -q tests/test_render.py -v
```

Expected: FAIL with unexpected keyword arguments such as `max_length_mm` or missing attributes such as `estimated_length_mm`.

- [ ] **Step 3: Implement hard-line wrapping, length estimation, and the generalized fit loop**

Update `src/paperang_cli/render.py` so `RenderedBitstream` includes measured metadata and `render_text_job` uses a real fit loop for both normal and rotated text.

The key additions should look like this:

```python
@dataclass(slots=True)
class RenderedBitstream:
    bitstream: bytes
    width: int
    height: int
    styling: RenderStyling
    render_height_px: int
    estimated_length_mm: float | None
    max_length_mm: float | None
    fits_length_budget: bool | None


def estimate_length_mm(*, rendered_height_px: int, advance_mm_per_px: float) -> float:
    return rendered_height_px * advance_mm_per_px


def _length_fits(estimated_length_mm: float | None, max_length_mm: float | None) -> bool:
    return max_length_mm is None or (estimated_length_mm is not None and estimated_length_mm <= max_length_mm)
```

Keep the fit loop simple and deterministic: render, orient, measure, accept or decrement font size.

- [ ] **Step 4: Re-run the render tests**

Run:

```powershell
python -m pytest -q tests/test_render.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the text render behavior**

Run:

```powershell
git add src/paperang_cli/render.py tests/test_render.py
git commit -m "feat: add text fit loop and length estimation"
```

### Task 4: Image fit-within-length and compose length reporting

**Files:**
- Modify: `src/paperang_cli/render.py`
- Modify: `src/paperang_cli/models.py`
- Modify: `src/paperang_cli/drivers/paperang_p1.py`
- Test: `tests/test_render.py`
- Test: `tests/test_driver_styles.py`

- [ ] **Step 1: Write the failing image and compose tests**

Add tests like these:

```python
def test_render_image_job_can_scale_down_to_fit_length(tmp_path):
    image_path = tmp_path / "tall.png"
    Image.new("RGB", (32, 256), "black").save(image_path)

    rendered = render_image_job(
        image_path,
        printer_width=384,
        conversion="threshold",
        fit_mode="fit-within-length",
        max_length_mm=20.0,
        advance_mm_per_px=0.1217,
    )

    assert rendered.estimated_length_mm <= 20.0
    assert rendered.fits_length_budget is True


def test_driver_compose_reports_length_budget_failure(monkeypatch, tmp_path):
    image_path = tmp_path / "compose.png"
    Image.new("RGB", (32, 32), "white").save(image_path)

    with pytest.raises(ValueError, match="length budget"):
        render_composed_bitstream(
            "very long composed label",
            image_path,
            printer_width=384,
            max_length_mm=10.0,
            overflow_policy="error",
            advance_mm_per_px=0.1217,
        )
```

- [ ] **Step 2: Run the render and driver-style tests to confirm missing behavior**

Run:

```powershell
python -m pytest -q tests/test_render.py tests/test_driver_styles.py -v
```

Expected: FAIL with missing `fit_mode`, missing compose length logic, or missing `PrintResult` fields.

- [ ] **Step 3: Implement image length fitting and compose overflow reporting**

Update image rendering and the P1 driver to propagate new length metrics.

Extend `PrintResult` like this:

```python
@dataclass(slots=True)
class PrintResult:
    model: str
    address: str | None
    operation: str
    dry_run: bool
    feed_mm: float | None = None
    feed_units: int | None = None
    font_size: int | None = None
    bytes_sent: int | None = None
    paragraph: bool | None = None
    source_path: str | None = None
    conversion: str | None = None
    layout: str | None = None
    battery_after: int | None = None
    warning: str | None = None
    styling: dict[str, Any] | None = None
    applied_preset: str | None = None
    render_height_px: int | None = None
    estimated_length_mm: float | None = None
    max_length_mm: float | None = None
    fits_length_budget: bool | None = None
    printable_width_mm: float | None = None
    advance_mm_per_px: float | None = None
```

Compose should report or fail when over budget, but it should not attempt full automatic compose rebalancing in this task.

- [ ] **Step 4: Re-run the render and driver-style tests**

Run:

```powershell
python -m pytest -q tests/test_render.py tests/test_driver_styles.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the image and compose metrics**

Run:

```powershell
git add src/paperang_cli/render.py src/paperang_cli/models.py src/paperang_cli/drivers/paperang_p1.py tests/test_render.py tests/test_driver_styles.py
git commit -m "feat: add image and compose length metrics"
```

### Task 5: CLI and Python API integration

**Files:**
- Modify: `src/paperang_cli/commands/print_cmd.py`
- Modify: `src/paperang_cli/api/p1.py`
- Modify: `src/paperang_cli/drivers/paperang_p1.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing CLI and API tests**

Add tests like these:

```python
def test_print_text_dry_run_accepts_preset_and_style_json(monkeypatch, fake_driver, tmp_path):
    style_path = tmp_path / "style.json"
    style_path.write_text('{"preset": "address-label", "paragraph": {"max_length_mm": 75.0}}', encoding="utf-8")

    runner = CliRunner()
    monkeypatch.setattr(registry, "get_driver", lambda settings: fake_driver)

    result = runner.invoke(
        cli,
        [
            "--json",
            "print",
            "paragraph",
            "Shipping label",
            "--dry-run",
            "--style-json",
            str(style_path),
        ],
    )

    assert result.exit_code == 0
    assert '"applied_preset": "address-label"' in result.output
    assert '"max_length_mm": 75.0' in result.output


def test_api_print_text_accepts_style_payload(fake_driver):
    printer = PaperangP1(driver=fake_driver)

    printer.print_text("Badge", style={"preset": "name-badge"}, dry_run=True)

    assert fake_driver.calls[-1][1]["style"]["preset"] == "name-badge"
```

- [ ] **Step 2: Run the CLI and API tests to confirm the new flags are missing**

Run:

```powershell
python -m pytest -q tests/test_cli.py tests/test_api.py -v
```

Expected: FAIL with unknown CLI option `--style-json`, and Python API signature failures.

- [ ] **Step 3: Implement preset and style-json plumbing for CLI and API**

Add `--style-json` to the print commands and pass the parsed JSON payload to the driver or style-resolution layer.

The CLI surface should look like this:

```python
@click.option("--style-json", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
```

Update `_emit_print_result` to include the new metrics in human output:

```python
if result.applied_preset:
    human_lines.append(f"Preset: {result.applied_preset}")
if result.estimated_length_mm is not None:
    human_lines.append(f"Estimated length mm: {result.estimated_length_mm:.2f}")
if result.max_length_mm is not None:
    human_lines.append(f"Max length mm: {result.max_length_mm:.2f}")
if result.fits_length_budget is not None:
    human_lines.append(f"Fits length budget: {result.fits_length_budget}")
```

Keep precedence identical between CLI and Python API.

- [ ] **Step 4: Re-run the CLI and API tests**

Run:

```powershell
python -m pytest -q tests/test_cli.py tests/test_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the public surface changes**

Run:

```powershell
git add src/paperang_cli/commands/print_cmd.py src/paperang_cli/api/p1.py src/paperang_cli/drivers/paperang_p1.py tests/test_cli.py tests/test_api.py
git commit -m "feat: add style json print controls"
```

### Task 6: Public contract, docs, and calibration guidance

**Files:**
- Modify: `src/paperang_cli/api/contract.py`
- Modify: `docs/agents/cli-contract.md`
- Modify: `docs/agents/cli-contract.json`
- Modify: `skills/paperang-cli/references/cli-contract.md`
- Modify: `skills/paperang-cli/references/cli-contract.json`
- Modify: `docs/usage/commands.md`
- Modify: `docs/usage/configuration.md`
- Modify: `paperang-cli.config.example.json`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing public-contract expectations**

Add or extend tests like these:

```python
def test_api_p1_json_mentions_presets_and_length_metrics():
    runner = CliRunner()

    result = runner.invoke(cli, ["--json", "api", "p1"])

    assert result.exit_code == 0
    assert '"preset_support": true' in result.output
    assert '"style_json_support": true' in result.output
    assert '"length_metrics": [' in result.output
```

- [ ] **Step 2: Run the contract-facing tests to confirm missing API documentation**

Run:

```powershell
python -m pytest -q tests/test_cli.py::test_api_p1_json_mentions_presets_and_length_metrics -v
```

Expected: FAIL because the API contract summary does not mention presets, style JSON, or length metrics yet.

- [ ] **Step 3: Update the contract, docs, and config examples**

Document the JSON control flow, preset catalog, and manual calibration workflow.

Key documentation snippets should include examples like these:

```powershell
paperang --json print paragraph "Shipping label" --dry-run --style-json .\address-label.json
paperang --json print image .\banner.png --dry-run --style-json .\logo-strip.json
paperang --json print compose "Product" .\badge.png --dry-run --style-json .\product-override.json
```

```json
{
    "preset": "planner-strip",
    "paragraph": {
        "font_size": 22,
        "max_length_mm": 25.0,
        "overflow_policy": "shrink-to-fit",
        "break_long_words": true
  }
}
```

Document the manual calibration strip workflow explicitly with two generated full-width image strips:

```text
measure full black-line width -> printable_width_mm = measured_width_mm
measure marker-to-marker advance -> advance_mm_per_px = measured_advance_mm / marker_distance_px
```

Also synchronize both skill reference copies with `docs/agents/`.

- [ ] **Step 4: Re-run the contract-facing tests and the skill sync check**

Run:

```powershell
python -m pytest -q tests/test_cli.py -v
python scripts/check-agent-skill.py
```

Expected: PASS for both commands.

- [ ] **Step 5: Commit the documentation and contract updates**

Run:

```powershell
git add src/paperang_cli/api/contract.py docs/agents/cli-contract.md docs/agents/cli-contract.json skills/paperang-cli/references/cli-contract.md skills/paperang-cli/references/cli-contract.json docs/usage/commands.md docs/usage/configuration.md paperang-cli.config.example.json tests/test_cli.py
git commit -m "docs: document smart layout presets and calibration"
```

### Task 7: Final verification

**Files:**
- Modify: none

- [ ] **Step 1: Run the focused Python verification suite**

Run:

```powershell
python -m pytest -q tests/test_config.py tests/test_presets.py tests/test_style_resolution.py tests/test_render.py tests/test_driver_styles.py tests/test_api.py tests/test_cli.py
```

Expected: PASS.

- [ ] **Step 2: Run the complete repository Python suite**

Run:

```powershell
python -m pytest -q tests
```

Expected: PASS.

- [ ] **Step 3: Run the repository validation helpers**

Run:

```powershell
python scripts/check-agent-skill.py
```

Expected: PASS.

- [ ] **Step 4: Run the npm wrapper verification**

Run:

```powershell
Set-Location npm
npm test
npm pack --dry-run
```

Expected: PASS.

- [ ] **Step 5: Commit the verified branch state**

Run:

```powershell
git status --short
git add -A
git commit -m "feat: add smart layout presets and length-aware rendering"
```