#!/usr/bin/env python3
"""Cross-platform installation check for paperang-cli.

Run this script to verify your installation is correct:
    python scripts/check-cross-platform.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.
"""
from __future__ import annotations

import importlib
import importlib.util
import platform
import sys


def check(name: str, ok: bool, detail: str) -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")
    return ok


def main() -> int:
    results = []

    # Platform
    results.append(check(
        "platform",
        True,
        f"{platform.system()} {platform.release()} ({sys.platform})",
    ))

    # Python version
    v = sys.version_info
    results.append(check(
        "python",
        v >= (3, 10),
        f"{v.major}.{v.minor}.{v.micro} (requires >=3.10)",
    ))

    # paperang_cli importable
    try:
        import paperang_cli
        results.append(check("import", True, f"paperang_cli {paperang_cli.__version__}"))
    except ImportError as exc:
        results.append(check("import", False, str(exc)))
        return 1

    # CLI entrypoint
    try:
        from paperang_cli.cli import cli
        results.append(check("cli", True, "entrypoint importable"))
    except ImportError as exc:
        results.append(check("cli", False, str(exc)))
        return 1

    # Config path
    try:
        from paperang_cli.config import default_config_path
        path = default_config_path()
        results.append(check("config", True, str(path)))
    except Exception as exc:
        results.append(check("config", False, str(exc)))

    # Capability detection
    try:
        from paperang_cli.protocol._capabilities import report
        caps = report()
        results.append(check("capabilities", True, f"{len(caps)} checks"))
        for cap in caps:
            mark = "OK" if cap["available"] else "WARN"
            print(f"  [{mark}] {cap['name']}: {cap['detail']}")
    except ImportError as exc:
        results.append(check("capabilities", False, f"not available: {exc}"))
    except Exception as exc:
        results.append(check("capabilities", False, str(exc)))

    # bleak
    bleak_spec = importlib.util.find_spec("bleak")
    results.append(check(
        "bleak",
        bleak_spec is not None,
        "installed" if bleak_spec else "not installed (BLE unavailable)",
    ))

    # paperang-p2-lib
    try:
        v = importlib.metadata.version("paperang-p2-lib")
        results.append(check("paperang-p2-lib", True, f"v{v}"))
    except importlib.metadata.PackageNotFoundError:
        results.append(check("paperang-p2-lib", False, "not installed"))
    except Exception as exc:
        results.append(check("paperang-p2-lib", False, str(exc)))

    # Summary
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("All checks passed. Your installation is ready.")
        return 0
    else:
        print("Some checks failed. See above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
