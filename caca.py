#!/usr/bin/env python3
"""Lançador: o mesmo que `python -m caca_zoo`."""

import sys

from caca_zoo.cli import main

if __name__ == "__main__":
    sys.exit(main())
