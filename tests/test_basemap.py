"""Tests for build-basemap's helper: the offline parts (bbox reordering, tile maths, CLI)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

BASEMAP = (
    Path(__file__).resolve().parent.parent / "skills" / "build-basemap" / "scripts" / "basemap.py"
)

_spec = importlib.util.spec_from_file_location("basemap", BASEMAP)
basemap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(basemap)


def test_nominatim_box_is_reordered_to_pmtiles_order() -> None:
    # Nominatim: [south, north, west, east].
    box = basemap.nominatim_to_bbox(["36.9", "42.2", "-9.6", "-6.1"])
    assert box == "-9.6000,36.9000,-6.1000,42.2000"


def test_nominatim_box_rejects_antimeridian_and_garbage() -> None:
    with pytest.raises(ValueError):
        basemap.nominatim_to_bbox(["-17", "-16", "179", "-179"])
    with pytest.raises(ValueError):
        basemap.nominatim_to_bbox(["50", "40", "0", "1"])


def test_tile_under_freiburg_muenster() -> None:
    z, x, y = basemap.tile_for(47.9955, 7.8529)
    assert z == 14
    assert (x, y) == (8549, 5695)


def test_tile_clamps_the_edge_and_rejects_out_of_range() -> None:
    assert basemap.tile_for(0, 180, zoom=2)[1] == 3
    with pytest.raises(ValueError):
        basemap.tile_for(95, 0)


def test_cli_tile_prints_zxy() -> None:
    result = subprocess.run(
        [sys.executable, str(BASEMAP), "tile", "47.9955", "7.8529"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.split()[0] == "14"
    assert len(result.stdout.split()) == 3
