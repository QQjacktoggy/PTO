"""Command-line entry point for Phase 0 governance operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from pto_quant.config import ConfigValidationError, load_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pto", description="PTO adaptive quant research CLI")
    commands = parser.add_subparsers(dest="command", required=True)

    config = commands.add_parser("config", help="configuration operations")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    validate = config_commands.add_parser("validate", help="validate all config contracts")
    validate.add_argument("--config-dir", default="config")

    project = commands.add_parser("project", help="project metadata")
    project_commands = project.add_subparsers(dest="project_command", required=True)
    info = project_commands.add_parser("info", help="print validated project information")
    info.add_argument("--config-dir", default="config")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible status code."""

    args = _parser().parse_args(argv)
    try:
        bundle = load_config(args.config_dir)
    except ConfigValidationError as exc:
        print(f"configuration validation failed:\n{exc}", file=sys.stderr)
        return 2

    if args.command == "config" and args.config_command == "validate":
        print(f"configuration valid: {bundle.config_dir}")
        return 0
    if args.command == "project" and args.project_command == "info":
        print(json.dumps(asdict(bundle.project), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
