"""Package layout: every sub-package imports, and the core stays independent of qPCR."""

import importlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import qpilot

ROOT = Path(__file__).resolve().parents[1]
SUBPACKAGES = ["ai", "cli", "core", "explain", "harness", "io", "qpcr", "schemas", "vendor"]


def test_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert qpilot.__version__ == pyproject["project"]["version"]


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports_and_is_documented(name):
    module = importlib.import_module(f"qpilot.{name}")
    assert module.__doc__ and module.__doc__.strip()


def test_core_does_not_import_qpcr_plugin():
    # A fresh interpreter, so modules already imported by other tests cannot mask a dependency.
    code = "import sys, qpilot.core; sys.exit('qpilot.qpcr' in sys.modules)"
    completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=False)
    assert completed.returncode == 0, "qpilot.core must not import the qPCR plugin"


def test_python_dash_m_runs_cli():
    completed = subprocess.run(
        [sys.executable, "-m", "qpilot", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == f"qpilot {qpilot.__version__}"
