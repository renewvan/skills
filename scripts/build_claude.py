#!/usr/bin/env python3
"""Generate the Claude Code variant of every skill into claude/<name>/.

skills/<name>/ is the general, harness-neutral source. claude-overrides/<name>.md
holds extra frontmatter lines (allowed-tools, argument-hint, ...) between its own
`---` fences, and a body that is appended to SKILL.md as "Claude Code notes".
Everything else in the skill directory is copied unchanged, so the two variants
cannot drift: tests fail when claude/ is stale. Run with no arguments to rebuild.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skills"
OVERRIDES = ROOT / "claude-overrides"
OUTPUT = ROOT / "claude"
NOTES_HEADING = "## Claude Code notes"


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.split("\n")
    if lines[0] != "---":
        raise ValueError("missing frontmatter")
    end = lines.index("---", 1)
    return lines[1:end], "\n".join(lines[end + 1 :])


def build_skill(name: str, dest_root: Path) -> None:
    src = SOURCE / name
    dest = dest_root / name
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))

    override = OVERRIDES / f"{name}.md"
    if not override.is_file():
        return
    extra_fm, notes = split_frontmatter(override.read_text())
    fm, body = split_frontmatter((src / "SKILL.md").read_text())
    text = "---\n" + "\n".join(fm + extra_fm) + "\n---\n" + body.rstrip("\n")
    text += f"\n\n{NOTES_HEADING}\n\n{notes.strip()}\n"
    (dest / "SKILL.md").write_text(text)


def build(output: Path = OUTPUT) -> list[str]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    names = sorted(p.name for p in SOURCE.iterdir() if (p / "SKILL.md").is_file())
    for name in names:
        build_skill(name, output)
    return names


if __name__ == "__main__":
    built = build()
    print(f"Built Claude variant of {len(built)} skills into {OUTPUT}: {', '.join(built)}")
    sys.exit(0)
