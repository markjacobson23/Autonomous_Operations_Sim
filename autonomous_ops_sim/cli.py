import argparse
import sys
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_summary import format_scenario_summary


def _run_scenario_command(scenario_path: str) -> int:
    try:
        scenario = load_scenario(Path(scenario_path))
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(f"Error: failed to load scenario '{scenario_path}': {exc}", file=sys.stderr)
        return 1

    print(format_scenario_summary(scenario))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autonomous-ops-sim",
        description="A Python simulator for autonomous operations research and development.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="autonomous-ops-sim 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Load and validate a scenario JSON file.")
    run_parser.add_argument("scenario_path", help="Path to a scenario JSON file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_scenario_command(args.scenario_path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
