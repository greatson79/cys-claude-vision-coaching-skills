#!/usr/bin/env python3
"""CLI entry. Usage:
    python3 scripts/run_pipeline.py profile.json
    cat profile.json | python3 scripts/run_pipeline.py -
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.pipeline import cli_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli_main(sys.argv))
