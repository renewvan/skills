#!/usr/bin/env python3
"""Scaffold a new renewvan/driver-<entity> repo from `renewvan/driver-template`.

The skeleton and the renderer live in the driver-template repo; this wrapper only finds a
checkout of it and runs its `scripts/scaffold.py` with the same arguments. Lookup order:

1. `$RENEWVAN_DRIVER_TEMPLATE`, a path to a driver-template checkout
2. a `driver-template` directory next to the current directory or next to this skills checkout
3. a shallow clone of https://github.com/renewvan/driver-template into a temp directory

Usage: scaffold.py <entity-slug> <entity-title> <description> <target-dir>
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TEMPLATE_URL = "https://github.com/renewvan/driver-template.git"
RENDERER = Path("scripts") / "scaffold.py"


def candidates() -> list[Path]:
    found: list[Path] = []
    if env := os.environ.get("RENEWVAN_DRIVER_TEMPLATE"):
        found.append(Path(env).expanduser())
    found.append(Path.cwd().parent / "driver-template")
    found.append(Path(__file__).resolve().parents[4] / "driver-template")
    return found


def find_template(tmp: Path) -> Path:
    for path in candidates():
        if (path / RENDERER).is_file():
            return path
    clone = tmp / "driver-template"
    subprocess.run(["git", "clone", "--depth", "1", "-q", TEMPLATE_URL, str(clone)], check=True)
    return clone


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        template = find_template(Path(tmp))
        result = subprocess.run([sys.executable, str(template / RENDERER), *sys.argv[1:]])
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
