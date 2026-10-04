"""Regression test for scaffold.py: proves the token-substitution and
file-layout logic produces a working node skeleton, independent of any
specific entity name.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCAFFOLD = (
    Path(__file__).resolve().parent.parent / "skills" / "scaffold-node" / "scripts" / "scaffold.py"
)


def test_scaffold_produces_expected_layout(tmp_path: Path) -> None:
    target = tmp_path / "node-gps"
    subprocess.run(
        [sys.executable, str(SCAFFOLD), "gps", "GPS", "Test GPS node", str(target)],
        check=True,
    )

    assert (target / "node_gps" / "main.py").exists()
    assert (target / "node_gps" / "config.py").exists()
    assert (target / "node_gps" / "publisher.py").exists()
    assert (target / "node_gps" / "driver.py").exists()
    assert (target / "node_gps" / "systemd" / "node-gps.service").exists()
    assert (target / "tests" / "test_config.py").exists()
    assert not (target / "__PACKAGE__").exists()
    assert not list(target.rglob("*.tmpl"))

    pyproject = (target / "pyproject.toml").read_text()
    assert 'name = "node-gps"' in pyproject
    assert "__ENTITY__" not in pyproject
    assert "__PACKAGE__" not in pyproject

    driver = (target / "node_gps" / "driver.py").read_text()
    assert "renewvan/gps/" in driver
    assert "__ENTITY__" not in driver

    readme = (target / "README.md").read_text()
    assert "Test GPS node" in readme
    assert "node-gps" in readme

    license_text = (target / "LICENSE").read_text()
    assert "RenewVan" in license_text


def test_scaffold_rejects_invalid_entity_slug(tmp_path: Path) -> None:
    target = tmp_path / "node-bad"
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "Not-Valid", "X", "desc", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not target.exists()


def test_scaffold_refuses_existing_target(tmp_path: Path) -> None:
    target = tmp_path / "node-exists"
    target.mkdir()
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "exists", "Exists", "desc", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
