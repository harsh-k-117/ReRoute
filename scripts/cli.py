#!/usr/bin/env python3
"""scripts/cli.py - `reroute plan|replan|validate` command line

Lane : P3 Integration & language lead (single writer for this path)
Stack: bash + Python 3.12 (stdlib argparse) · uv · openapi-typescript
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="reroute")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="build the initial plan for a scenario")
    sub.add_parser("replan", help="apply a disruption and replan")
    sub.add_parser("validate", help="run the independent validator on a plan")
    parser.parse_args()
    raise NotImplementedError("TODO(P3)")


if __name__ == "__main__":
    raise SystemExit(main())
