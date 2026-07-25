"""Command-line entry point for governed PTO research operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pto_quant.config import ConfigValidationError, load_config
from pto_quant.data.client import BinancePublicClient, PublicDataError
from pto_quant.data.pipeline import (
    acquire_symbol,
    acquire_symbol_vision,
    git_sha,
    validate_symbol,
)
from pto_quant.data.vision import BinanceVisionClient, months_between


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

    data = commands.add_parser("data", help="Phase 1 public-data operations")
    data_commands = data.add_subparsers(dest="data_command", required=True)
    acquire = data_commands.add_parser("acquire", help="download and normalize bounded public data")
    acquire.add_argument("--config-dir", default="config")
    acquire.add_argument("--root", default=".")
    acquire.add_argument("--symbol", action="append", dest="symbols")
    acquire.add_argument("--start", required=True, help="inclusive UTC timestamp")
    acquire.add_argument("--end", required=True, help="inclusive UTC timestamp")
    acquire.add_argument("--base-url", default="https://fapi.binance.com")
    acquire.add_argument(
        "--transport",
        choices=("rest", "vision"),
        default="rest",
        help="public historical-data transport",
    )
    validate_data = data_commands.add_parser("validate", help="fail on critical normalized defects")
    validate_data.add_argument("--config-dir", default="config")
    validate_data.add_argument("--root", default=".")
    validate_data.add_argument("--symbol", action="append", dest="symbols")
    return parser


def _timestamp_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return int(parsed.astimezone(UTC).timestamp() * 1000)


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
    configured_symbols = (
        bundle.markets.primary_symbol,
        *bundle.markets.generalization_symbols,
    )
    if args.command == "data" and args.data_command == "acquire":
        try:
            start_ms = _timestamp_ms(args.start)
            end_ms = _timestamp_ms(args.end)
            if end_ms < start_ms:
                raise ValueError("--end must be at or after --start")
            root = Path(args.root).resolve()
            revision = git_sha(root)
            if args.transport == "vision":
                vision_client = BinanceVisionClient(
                    args.base_url
                    if args.base_url != "https://fapi.binance.com"
                    else "https://data.binance.vision"
                )
                months = months_between(start_ms, end_ms)
                results = [
                    acquire_symbol_vision(
                        vision_client,
                        root=root,
                        symbol=symbol,
                        months=months,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        config_hash=bundle.project.config_hash,
                        revision=revision,
                    )
                    for symbol in (args.symbols or configured_symbols)
                ]
            else:
                rest_client = BinancePublicClient(args.base_url)
                results = [
                    acquire_symbol(
                        rest_client,
                        root=root,
                        symbol=symbol,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        config_hash=bundle.project.config_hash,
                        revision=revision,
                    )
                    for symbol in (args.symbols or configured_symbols)
                ]
        except (OSError, ValueError, PublicDataError) as exc:
            print(f"data acquisition failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0
    if args.command == "data" and args.data_command == "validate":
        root = Path(args.root).resolve()
        validation_results = {
            symbol: validate_symbol(root, symbol).to_dict()
            for symbol in (args.symbols or configured_symbols)
        }
        print(json.dumps(validation_results, indent=2, sort_keys=True))
        return 2 if any(result["critical_count"] for result in validation_results.values()) else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
