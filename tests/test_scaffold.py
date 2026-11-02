"""The scaffold script is a thin wrapper: it must find a driver-template checkout and run its
renderer with the caller's arguments. The skeleton and renderer are tested in
renewvan/driver-template, so these tests use a stub renderer."""

from __future__ import annotations

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

STUB = """\
import sys
from pathlib import Path
Path(sys.argv[4]).mkdir()
print("stub:" + "|".join(sys.argv[1:]))
raise SystemExit(7 if sys.argv[1] == "fail" else 0)
"""


def make_stub_template(root: Path) -> Path:
    template = root / "driver-template"
    (template / "scripts").mkdir(parents=True)
    (template / "scripts" / "scaffold.py").write_text(STUB)
    return template


def run(env_template: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCAFFOLD), *args],
        capture_output=True,
        text=True,
        check=False,
        env={"RENEWVAN_DRIVER_TEMPLATE": str(env_template), "PATH": "/usr/bin:/bin"},
    )


def test_wrapper_runs_the_template_renderer_with_the_same_arguments(tmp_path: Path) -> None:
    template = make_stub_template(tmp_path)
    target = tmp_path / "driver-gps"

    result = run(template, "gps", "GPS", "desc", str(target))

    assert result.returncode == 0
    assert f"stub:gps|GPS|desc|{target}" in result.stdout
    assert target.is_dir()


def test_wrapper_passes_the_renderer_exit_code_through(tmp_path: Path) -> None:
    template = make_stub_template(tmp_path)

    result = run(template, "fail", "X", "desc", str(tmp_path / "driver-fail"))

    assert result.returncode == 7
