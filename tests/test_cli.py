"""The command-line dispatcher: help, version, registration and exit codes."""

import argparse

import pytest

from qpilot import __version__
from qpilot.cli import build_parser, main


def _command(name, run):
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--flag", action="store_true")

    return (name, f"{name} help", add_arguments, run)


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: qpilot")
    assert "Research use only" in out


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"qpilot {__version__}"


def test_unknown_command_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["no-such-command"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_duplicate_command_names_are_rejected():
    commands = [_command("run", lambda args: 0), _command("run", lambda args: 0)]
    with pytest.raises(ValueError, match="registered twice: run"):
        build_parser(commands)


def test_registered_command_receives_parsed_arguments():
    seen = {}

    def run(args):
        seen["flag"] = args.flag
        return 0

    parser = build_parser([_command("demo", run)])
    args = parser.parse_args(["demo", "--flag"])
    assert args._run(args) == 0
    assert seen == {"flag": True}


@pytest.mark.parametrize(("returned", "expected"), [(0, 0), (None, 0), (3, 3)])
def test_main_propagates_exit_code(monkeypatch, returned, expected):
    from qpilot.cli import core_cmds

    monkeypatch.setattr(core_cmds, "COMMANDS", [_command("demo", lambda args: returned)])
    assert main(["demo"]) == expected
