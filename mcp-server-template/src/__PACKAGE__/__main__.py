"""Command-line entry point: `python -m __PACKAGE__` or the `__DIST_NAME__` script."""

from __future__ import annotations

import argparse

from . import __version__
from .server import build_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="__DIST_NAME__",
        description=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    build_server().run("stdio")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
