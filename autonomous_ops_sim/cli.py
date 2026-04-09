import argparse
import sys
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_summary import format_scenario_summary
from autonomous_ops_sim.perf import export_benchmark_suite_json, run_default_benchmark_suite
from autonomous_ops_sim.showcase import export_showcase_demo
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario


def _run_scenario_command(scenario_path: str) -> int:
    try:
        scenario = load_scenario(Path(scenario_path))
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(f"Error: failed to load scenario '{scenario_path}': {exc}", file=sys.stderr)
        return 1

    print(format_scenario_summary(scenario))
    return 0


def _execute_scenario_command(scenario_path: str) -> int:
    try:
        scenario = load_scenario(Path(scenario_path))
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(f"Error: failed to load scenario '{scenario_path}': {exc}", file=sys.stderr)
        return 1

    try:
        result = execute_scenario(scenario)
    except (ValueError, KeyError, RuntimeError) as exc:
        print(
            f"Error: failed to execute scenario '{scenario_path}': {exc}",
            file=sys.stderr,
        )
        return 1

    print(result.export_json, end="")
    return 0


def _benchmark_command(*, repetitions: int, warmup_iterations: int) -> int:
    result = run_default_benchmark_suite(
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
    )
    print(export_benchmark_suite_json(result), end="")
    return 0


def _showcase_command(
    *,
    output_dir: str,
    flagship_scenario: str,
    pack_directory: str,
) -> int:
    artifacts = export_showcase_demo(
        output_dir,
        flagship_scenario_path=flagship_scenario,
        pack_directory=pack_directory,
    )
    print(artifacts.manifest_path)
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

    run_parser = subparsers.add_parser(
        "run",
        help="Load and summarize a scenario JSON file.",
    )
    run_parser.add_argument("scenario_path", help="Path to a scenario JSON file.")

    execute_parser = subparsers.add_parser(
        "execute",
        help="Execute a scenario JSON file and emit deterministic export JSON.",
    )
    execute_parser.add_argument("scenario_path", help="Path to a scenario JSON file.")

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run the repeatable Step 29 benchmark suite and emit JSON results.",
    )
    benchmark_parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Measured repetitions per benchmark case.",
    )
    benchmark_parser.add_argument(
        "--warmup-iterations",
        type=int,
        default=1,
        help="Warmup iterations per benchmark case before measurement.",
    )

    showcase_parser = subparsers.add_parser(
        "showcase",
        help="Export the Step 38 mining showpiece replay/live/viewer artifacts.",
    )
    showcase_parser.add_argument(
        "--output-dir",
        default="showcase_output",
        help="Directory to receive the exported showcase artifacts.",
    )
    showcase_parser.add_argument(
        "--flagship-scenario",
        default="scenarios/showpiece_pack/01_mine_ore_shift.json",
        help="Optional flagship scenario JSON path override.",
    )
    showcase_parser.add_argument(
        "--pack-directory",
        default="scenarios/showpiece_pack",
        help="Optional scenario pack directory override.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_scenario_command(args.scenario_path)
    if args.command == "execute":
        return _execute_scenario_command(args.scenario_path)
    if args.command == "benchmark":
        return _benchmark_command(
            repetitions=args.repetitions,
            warmup_iterations=args.warmup_iterations,
        )
    if args.command == "showcase":
        return _showcase_command(
            output_dir=args.output_dir,
            flagship_scenario=args.flagship_scenario,
            pack_directory=args.pack_directory,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


