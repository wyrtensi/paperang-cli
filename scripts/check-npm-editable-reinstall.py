#!/usr/bin/env python3
"""Verify that the npm wrapper install flow replaces editable Python installs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_MANIFEST_PATH = REPO_ROOT / "src" / "paperang_cli" / "version-manifest.json"


def load_package_version() -> str:
    manifest = json.loads(VERSION_MANIFEST_PATH.read_text(encoding="utf-8"))
    return str(manifest["version"])


def run(command: list[str], *, capture_output: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=capture_output,
        env={**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
        text=True,
    )
    return result.stdout.strip() if result.stdout is not None else ""


def get_python_path(venv_path: Path) -> Path:
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    return venv_path / scripts_dir / executable


def verify_editable_reinstall(package_version: str) -> None:
    package_spec = f"paperang-cli=={package_version}"

    with tempfile.TemporaryDirectory(prefix="paperang-cli-editable-reinstall-") as temp_dir:
        venv_path = Path(temp_dir) / "venv"
        run([os.sys.executable, "-m", "venv", str(venv_path)])
        python = get_python_path(venv_path)

        run([str(python), "-m", "pip", "install", "--no-deps", "-e", str(REPO_ROOT)])
        editable_freeze = run([str(python), "-m", "pip", "freeze"], capture_output=True)
        if "-e " not in editable_freeze:
            raise RuntimeError("Editable paperang-cli installation was not created.")

        run([str(python), "-m", "pip", "install", "--upgrade", package_spec])
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                "--no-deps",
                package_spec,
            ]
        )

        installed_freeze = run([str(python), "-m", "pip", "freeze"], capture_output=True)
        if "-e " in installed_freeze:
            raise RuntimeError("Editable paperang-cli installation is still active.")

        module_path = Path(
            run(
                [
                    str(python),
                    "-c",
                    "import paperang_cli; print(paperang_cli.__file__)",
                ],
                capture_output=True,
            )
        ).resolve()
        if not module_path.is_relative_to(venv_path.resolve()):
            raise RuntimeError(f"paperang_cli imported outside the virtual environment: {module_path}")

        run([str(python), "-m", "pip", "check"])
        print(f"Verified {package_spec}: {module_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package-version",
        default=load_package_version(),
        help="Published PyPI version to reinstall. Defaults to the repository manifest version.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_editable_reinstall(args.package_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
