from autonomous_ops_sim.perf import export_benchmark_suite_json, run_default_benchmark_suite


def main() -> int:
    print(export_benchmark_suite_json(run_default_benchmark_suite()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
