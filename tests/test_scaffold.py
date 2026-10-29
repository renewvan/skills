"""Regression test for scaffold.py: proves the token-substitution and
file-layout logic produces a working device skeleton, independent of any
specific entity name.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCAFFOLD = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "renewvan-create-driver"
    / "scripts"
    / "scaffold.py"
)


def test_scaffold_produces_expected_layout(tmp_path: Path) -> None:
    target = tmp_path / "driver-gps"
    subprocess.run(
        [sys.executable, str(SCAFFOLD), "gps", "GPS", "Test GPS device", str(target)],
        check=True,
    )

    assert (target / "driver_gps" / "main.py").exists()
    assert (target / "driver_gps" / "config.py").exists()
    assert (target / "driver_gps" / "publisher.py").exists()
    assert (target / "driver_gps" / "driver.py").exists()
    assert (target / "driver_gps" / "systemd" / "driver-gps.service").exists()
    assert (target / "tests" / "test_config.py").exists()
    assert (target / "driver_gps" / "driver_info.py").exists()
    assert (target / "tests" / "test_driver_info.py").exists()
    assert (target / ".github" / "workflows" / "manifest.yml").exists()
    assert not (target / "version").exists()
    assert not (target / "__PACKAGE__").exists()
    manifest = json.loads((target / "manifest.json").read_text())
    assert manifest["driver"] == "gps"
    assert manifest["publishes"] == ["gps"]
    assert "version" not in manifest and "board_serial" not in manifest
    assert not list(target.rglob("*.tmpl"))

    pyproject = (target / "pyproject.toml").read_text()
    assert 'name = "driver-gps"' in pyproject
    assert "__ENTITY__" not in pyproject
    assert "__PACKAGE__" not in pyproject

    driver = (target / "driver_gps" / "driver.py").read_text()
    assert "renewvan/gps/" in driver
    assert "__ENTITY__" not in driver

    readme = (target / "README.md").read_text()
    assert "Test GPS device" in readme
    assert "driver-gps" in readme

    license_text = (target / "LICENSE").read_text()
    assert "RenewVan" in license_text


def test_scaffold_rejects_invalid_entity_slug(tmp_path: Path) -> None:
    target = tmp_path / "device-bad"
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "Not-Valid", "X", "desc", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not target.exists()


def test_scaffold_underscore_slug_gives_hyphenated_repo(tmp_path: Path) -> None:
    target = tmp_path / "driver-gps-fix"
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "gps_fix", "GPS Fix", "Test device", str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "REPO=driver-gps-fix  PACKAGE=driver_gps_fix" in result.stdout
    assert (target / "driver_gps_fix" / "systemd" / "driver-gps-fix.service").exists()
    # Driver key follows manifest's slug rule (no underscores, no driver- prefix).
    assert json.loads((target / "manifest.json").read_text())["driver"] == "gps-fix"


def test_scaffold_rejects_description_that_would_break_toml(tmp_path: Path) -> None:
    target = tmp_path / "driver-bad"
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "bad", "Bad", 'has "quotes"', str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not target.exists()


def test_scaffold_refuses_existing_target(tmp_path: Path) -> None:
    target = tmp_path / "device-exists"
    target.mkdir()
    result = subprocess.run(
        [sys.executable, str(SCAFFOLD), "exists", "Exists", "desc", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
