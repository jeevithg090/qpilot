"""Command-line entry point.

Commands are registered in ``engine_cmds.py`` (analysis engine and app) and ``core_cmds.py``
(robustness core, records and integrations). A command is a tuple
``(name, help, add_arguments, run)`` where ``add_arguments(parser)`` adds options to an
``argparse`` sub-parser and ``run(args)`` returns an exit code.
"""

import argparse
from collections.abc import Sequence

from qpilot import __version__
from qpilot.cli import core_cmds, engine_cmds
from qpilot.cli._types import Command

__all__ = ["Command", "build_parser", "main"]


def build_parser(commands: Sequence[Command] | None = None) -> argparse.ArgumentParser:
    """Build the top-level parser with one sub-command per registered command.

    Args:
        commands: Commands to register. Defaults to every command in ``engine_cmds`` and
            ``core_cmds``.

    Raises:
        ValueError: If two commands share a name.
    """
    if commands is None:
        commands = [*engine_cmds.COMMANDS, *core_cmds.COMMANDS]
    parser = argparse.ArgumentParser(
        prog="qpilot",
        description="qPilot: open qPCR analysis. Research use only.",
    )
    parser.add_argument("--version", action="version", version=f"qpilot {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    seen: set[str] = set()
    for name, help_text, add_arguments, run in commands:
        if name in seen:
            raise ValueError(f"command registered twice: {name}")
        seen.add(name)
        command_parser = sub.add_parser(name, help=help_text)
        add_arguments(command_parser)
        command_parser.set_defaults(_run=run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``qpilot`` command line and return its exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    run = getattr(args, "_run", None)
    if run is None:
        parser.print_help()
        return 0
    return int(run(args) or 0)
