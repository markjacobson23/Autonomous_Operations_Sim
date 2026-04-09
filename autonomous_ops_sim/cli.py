import argparse
import sys
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_summary import format_scenario_summary
from autonomous_ops_sim.live_app import (
    DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY,
    DEFAULT_LIVE_OUTPUT_DIRECTORY,
    export_live_app_artifacts,
    launch_live_app,
)
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


def _live_command(
    *,
    scenario_path: str,
    output_dir: str,
    frontend_dist_dir: str,
    open_browser: bool,
    host: str,
    port: int,
    serve_seconds: float | None,
) -> int:
    try:
        artifacts = export_live_app_artifacts(
            scenario_path=scenario_path,
            output_directory=output_dir,
            frontend_dist_directory=frontend_dist_dir,
        )
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(
            f"Error: failed to prepare live app for scenario '{scenario_path}': {exc}",
            file=sys.stderr,
        )
        return 1

    if not open_browser:
        print(artifacts.launch_path)
        return 0

    launch_result = launch_live_app(
        artifacts,
        open_browser=True,
        host=host,
        port=port,
        serve_seconds=serve_seconds,
    )
    print(launch_result.launch_target)
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

    live_parser = subparsers.add_parser(
        "live",
        help="Prepare a live session and open the serious frontend launch path.",
    )
    live_parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario JSON path to bootstrap into a live session.",
    )
    live_parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_LIVE_OUTPUT_DIRECTORY),
        help="Directory to receive live app bootstrap artifacts.",
    )
    live_parser.add_argument(
        "--frontend-dist-dir",
        default=str(DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY),
        help="Optional serious UI build directory override.",
    )
    live_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Prepare artifacts but do not open a browser or serve the app.",
    )
    live_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Local host to bind when serving a built serious UI.",
    )
    live_parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Local port to bind when serving a built serious UI. Use 0 for auto.",
    )
    live_parser.add_argument(
        "--serve-seconds",
        type=float,
        default=None,
        help="Optional finite serve duration when a built serious UI is launched.",
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
    if args.command == "live":
        return _live_command(
            scenario_path=args.scenario,
            output_dir=args.output_dir,
            frontend_dist_dir=args.frontend_dist_dir,
            open_browser=not args.no_browser,
            host=args.host,
            port=args.port,
            serve_seconds=args.serve_seconds,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

