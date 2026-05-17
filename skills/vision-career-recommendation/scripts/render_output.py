#!/usr/bin/env python3
"""CLI: render plan.json + profile.json → markdown."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.render import cli_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli_main(sys.argv))
