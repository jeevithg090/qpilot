"""CLI commands about qPilot itself: environment and installation diagnostics."""

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from qpilot import __version__
from qpilot.cli._types import Command

DEMO_DATASET = Path.home() / ".cache" / "qpilot" / "data_vermeulen_raw.rdml"
"""Where the 64-plate demo dataset is expected once fetched."""

OPTIONAL_EXTRAS: dict[str, tuple[str, ...]] = {
    "ai": ("anthropic", "httpx"),
    "parquet": ("pyarrow",),
    "xlsx": ("openpyxl",),
}
"""Each optional extra in ``pyproject.toml`` and the import names it provides."""


def collect_info() -> dict[str, Any]:
    """Gather version, interpreter, install location, demo-dataset and extras status."""
    extras = {}
    for extra, modules in OPTIONAL_EXTRAS.items():
        missing = [m for m in modules if importlib.util.find_spec(m) is None]
        extras[extra] = {"installed": not missing, "missing": missing}
    return {
        "version": __version__,
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "package_dir": str(Path(__file__).resolve().parents[1]),
        "demo_dataset": {"path": str(DEMO_DATASET), "cached": DEMO_DATASET.is_file()},
        "extras": extras,
    }


def format_info(info: dict[str, Any]) -> str:
    """Render :func:`collect_info` output as aligned, human-readable lines."""
    demo = info["demo_dataset"]
    demo_line = "cached" if demo["cached"] else "not cached"
    lines = [
        f"qpilot {info['version']}  (research use only; not for clinical or diagnostic use)",
        "",
        f"  python        {info['python']} ({info['implementation']})",
        f"  platform      {info['platform']}",
        f"  executable    {info['executable']}",
        f"  package       {info['package_dir']}",
        f"  demo dataset  {demo_line}: {demo['path']}",
        "",
        "  optional extras",
    ]
    for extra, status in info["extras"].items():
        if status["installed"]:
            lines.append(f"    {extra:<8}  installed")
        else:
            missing = ", ".join(status["missing"])
            lines.append(
                f'    {extra:<8}  not installed (missing {missing}); pip install "qpilot[{extra}]"'
            )
    return "\n".join(lines)


def _add_info_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of text",
    )


def _run_info(args: argparse.Namespace) -> int:
    info = collect_info()
    print(json.dumps(info, indent=2) if args.json else format_info(info))
    return 0


COMMANDS: list[Command] = [
    (
        "info",
        "show version, Python, install location and optional extras (useful in bug reports)",
        _add_info_arguments,
        _run_info,
    ),
]
