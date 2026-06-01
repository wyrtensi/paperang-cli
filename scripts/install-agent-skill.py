#!/usr/bin/env python3
"""Install the paperang-cli Agent Skill for common agent clients."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


SKILL_NAME = "paperang-cli"
SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "examples/address-label.json",
    "examples/fridge-note.json",
    "examples/chore-list.json",
    "examples/pantry-label.json",
    "examples/cable-tag.json",
    "examples/storage-bin.json",
    "examples/receipt-note.json",
    "examples/logo-strip.json",
    "examples/product-style.json",
    "references/cli-contract.md",
    "references/cli-contract.json",
)
TARGET_PATHS = {
    "codex": Path(".codex") / "skills" / SKILL_NAME,
    "claude": Path(".claude") / "skills" / SKILL_NAME,
    "copilot": Path(".copilot") / "skills" / SKILL_NAME,
    "cursor": Path(".cursor") / "skills" / SKILL_NAME,
    "antigravity": Path(".gemini") / "antigravity" / "skills" / SKILL_NAME,
    "agents": Path(".agents") / "skills" / SKILL_NAME,
}
DEFAULT_REF = "main"
RAW_BASE_URL = "https://raw.githubusercontent.com/wyrtensi/paperang-cli"


def target_directories(home: Path, target: str) -> list[Path]:
    """Return personal skill destinations for a selected client target."""
    targets = TARGET_PATHS if target == "all" else {target: TARGET_PATHS[target]}
    return [home / relative_path for relative_path in targets.values()]


def install_skill(source: Path, home: Path, target: str, force: bool) -> list[Path]:
    """Copy a materialized skill directory into selected personal locations."""
    source = source.resolve()
    destinations = target_directories(home.expanduser().resolve(), target)

    for destination in destinations:
        if destination.exists() and not force:
            raise FileExistsError(f"{destination} already exists; pass --force to replace it")

    for destination in destinations:
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)

    return destinations


def download_remote_skill(destination: Path, base_url: str) -> Path:
    """Download the fixed skill file allowlist into a temporary directory."""
    destination.mkdir(parents=True, exist_ok=True)
    base_url = base_url.rstrip("/")

    for relative_path in SKILL_FILES:
        output_path = destination / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"{base_url}/{quote(relative_path)}"
        with urlopen(url, timeout=30) as response:
            output_path.write_bytes(response.read())

    return destination


def local_skill_path(repo_root: Path) -> Path:
    """Return the distributable skill directory inside a repository checkout."""
    return repo_root / "skills" / SKILL_NAME


def github_skill_url(ref: str) -> str:
    """Return the raw GitHub URL for the distributable skill directory."""
    return f"{RAW_BASE_URL}/{quote(ref, safe='')}/skills/{SKILL_NAME}"


def default_repo_root() -> Path:
    """Return a useful checkout root even when running a piped stdin script."""
    script_file = globals().get("__file__")
    if not script_file or script_file == "<stdin>":
        return Path.cwd()
    return Path(script_file).resolve().parents[1]


def resolve_source(source: str, repo_root: Path, ref: str, temporary_root: Path) -> Path:
    """Materialize the selected source and return its local directory."""
    local_source = local_skill_path(repo_root)

    if source in {"auto", "local"} and (local_source / "SKILL.md").is_file():
        return local_source

    if source == "local":
        raise FileNotFoundError(f"Local skill not found at {local_source}")

    return download_remote_skill(temporary_root / SKILL_NAME, github_skill_url(ref))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=(*TARGET_PATHS, "all"),
        default="all",
        help="Personal skill location to install. Default: all.",
    )
    parser.add_argument(
        "--source",
        choices=("auto", "local", "github"),
        default="auto",
        help="Prefer a local checkout or download from GitHub. Default: auto.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="Repository checkout root for local installation.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Override the home directory used for personal skill locations.",
    )
    parser.add_argument("--ref", default=DEFAULT_REF, help="GitHub branch, tag, or commit for downloads.")
    parser.add_argument("--force", action="store_true", help="Replace existing installed copies.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with tempfile.TemporaryDirectory(prefix="paperang-cli-skill-") as temporary_directory:
        source = resolve_source(args.source, args.repo_root.resolve(), args.ref, Path(temporary_directory))
        destinations = install_skill(source, args.home, args.target, args.force)

    for destination in destinations:
        print(f"Installed {SKILL_NAME}: {destination}")

    print("Restart your agent client to pick up the installed skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
