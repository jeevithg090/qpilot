"""Shared type for CLI command registrations."""

import argparse
from collections.abc import Callable

Command = tuple[str, str, Callable[[argparse.ArgumentParser], None], Callable[..., int | None]]
"""``(name, help, add_arguments, run)``: ``run(args)`` returns an exit code (``None`` means 0)."""
