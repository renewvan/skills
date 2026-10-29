"""Structure checks for every skill: valid frontmatter, a version, and a Claude variant
that is in sync with the general source (rebuild with scripts/build_claude.py)."""

from __future__ import annotations

import importlib.util
import re
import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
EXPECTED = {"renewvan-create-driver", "renewvan-build-basemap", "renewvan-deploy", "renewvan-port-dbus-driver", "renewvan-flash-esp32"}


def _frontmatter(path: Path) -> str:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(), re.S)
    assert match, f"{path} has no frontmatter"
    return match.group(1)


def _version(path: Path) -> str:
    match = re.search(r'^  version: "(\d+\.\d+\.\d+)"$', _frontmatter(path), re.M)
    assert match, f"{path} has no metadata.version"
    return match.group(1)


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_claude", ROOT / "scripts/build_claude.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_expected_skills_exist() -> None:
    assert {p.name for p in SKILLS} == EXPECTED


def test_general_skill_frontmatter() -> None:
    for skill in SKILLS:
        fm = _frontmatter(skill / "SKILL.md")
        assert re.search(rf"^name: {skill.name}$", fm, re.M)
        assert re.search(r"^description: Use when|^description: .*\. Use when", fm, re.M)
        _version(skill / "SKILL.md")


def test_claude_variant_has_same_version_and_is_in_sync(tmp_path: Path) -> None:
    builder = _load_builder()
    builder.build(tmp_path)
    for skill in SKILLS:
        built = tmp_path / skill.name / "SKILL.md"
        committed = ROOT / "claude" / skill.name / "SKILL.md"
        assert committed.is_file(), f"claude/{skill.name} missing: run scripts/build_claude.py"
        assert committed.read_text() == built.read_text(), f"claude/{skill.name} is stale"
        assert _version(committed) == _version(skill / "SKILL.md")
        assert "## Claude Code notes" in committed.read_text()


def test_claude_variant_copies_supporting_files() -> None:
    src = ROOT / "skills" / "renewvan-create-driver" / "scripts" / "scaffold.py"
    assert filecmp.cmp(src, ROOT / "claude" / "renewvan-create-driver" / "scripts" / "scaffold.py")
