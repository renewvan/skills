#!/usr/bin/env python3
"""Scaffold a new renewvan/driver-<entity> repo from the driver-tank reference
shape (templates/driver-skeleton). One step of ../SKILL.md -- run this after
collecting entity-slug, entity-title, description, and target-dir from the
user; don't hand-copy template files yourself.

Usage: scaffold.py <entity-slug> <entity-title> <description> <target-dir>
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates" / "driver-skeleton"

ENTITY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def main() -> None:
    if len(sys.argv) != 5:
        print(
            "Usage: scaffold.py <entity-slug> <entity-title> <description> <target-dir>",
            file=sys.stderr,
        )
        raise SystemExit(1)

    entity, entity_title, description, target_dir = sys.argv[1:5]
    if not ENTITY_RE.match(entity):
        print(
            f"entity-slug must be lowercase alphanumeric/underscore, starting "
            f"with a letter (got: {entity!r})",
            file=sys.stderr,
        )
        raise SystemExit(1)

    package = f"driver_{entity}"
    repo = f"driver-{entity.replace('_', '-')}"
    tokens = {
        "__ENTITY__": entity,
        "__ENTITY_TITLE__": entity_title,
        "__PACKAGE__": package,
        "__REPO__": repo,
        "__DESCRIPTION__": description,
        "__YEAR__": str(datetime.now(tz=timezone.utc).year),
    }

    target = Path(target_dir).expanduser().resolve()
    if target.exists():
        print(f"Target already exists: {target}", file=sys.stderr)
        raise SystemExit(1)

    if not TEMPLATE_DIR.is_dir():
        print(f"Template directory missing: {TEMPLATE_DIR}", file=sys.stderr)
        raise SystemExit(1)

    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel_str = str(src.relative_to(TEMPLATE_DIR))
        for token, value in tokens.items():
            rel_str = rel_str.replace(token, value)
        rel_str = rel_str.removesuffix(".tmpl")
        dest = target / rel_str

        if src.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src.read_text()
        except UnicodeDecodeError:
            dest.write_bytes(src.read_bytes())
            continue
        for token, value in tokens.items():
            text = text.replace(token, value)
        dest.write_text(text)

    print(f"Scaffolded {repo} at {target}")


if __name__ == "__main__":
    main()
