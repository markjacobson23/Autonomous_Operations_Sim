from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Protocol


BENCHMARK_SCHEMA_VERSION = 1


class BenchmarkClock(Protocol):
    """Clock interface for repeatable benchmark timing."""

    def now_ns(self) -> int: ...


class SystemBenchmarkClock:
    """Default benchmark clock backed by perf_counter_ns."""

    def now_ns(self) -> int:
        from time import perf_counter_ns

        return perf_counter_ns()


BenchmarkWorkload = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class BenchmarkCase:
    """One repeatable benchmark workload definition."""

    name: str
    category: str
    repetitions: int
    warmup_iterations: int
    config: dict[str, Any]
    workload: BenchmarkWorkload


@dataclass(frozen=True)
class BenchmarkTimingSummary:
    """Stable timing summary for one repeated benchmark case."""

    durations_ns: tuple[int, ...]
    total_duration_ns: int
    min_duration_ns: int
    max_duration_ns: int
    average_duration_ns: int


@dataclass(frozen=True)
class BenchmarkCaseResult:
    """Stable result for one measured benchmark case."""

    name: str
    category: str
    repetitions: int
    warmup_iterations: int
    config: dict[str, Any]
    output_summary: dict[str, Any]
    timing: BenchmarkTimingSummary


@dataclass(frozen=True)
class BenchmarkSuiteResult:
    """Stable result surface for a full benchmark suite run."""

    schema_version: int
    suite_name: str
    case_results: tuple[BenchmarkCaseResult, ...]


def run_benchmark_case(
    case: BenchmarkCase,
    *,
    clock: BenchmarkClock | None = None,
) -> BenchmarkCaseResult:
    """Execute one benchmark case with repeatable structural validation."""

    if case.repetitions <= 0:
        raise ValueError("benchmark repetitions must be positive")
    if case.warmup_iterations < 0:
        raise ValueError("benchmark warmup_iterations must be non-negative")

    for _ in range(case.warmup_iterations):
        _canonicalize_jsonable(case.workload())

    active_clock = clock or SystemBenchmarkClock()
    durations: list[int] = []
    output_summary: dict[str, Any] | None = None
    for _ in range(case.repetitions):
        started_at_ns = active_clock.now_ns()
        candidate_output = _canonicalize_jsonable(case.workload())
        completed_at_ns = active_clock.now_ns()
        if completed_at_ns < started_at_ns:
            raise ValueError("benchmark clock produced a negative duration")

        if output_summary is None:
            output_summary = candidate_output
        elif candidate_output != output_summary:
            raise RuntimeError(
                f"benchmark case '{case.name}' produced inconsistent structural output"
            )

        durations.append(completed_at_ns - started_at_ns)

    assert output_summary is not None
    total_duration_ns = sum(durations)
    return BenchmarkCaseResult(
        name=case.name,
        category=case.category,
        repetitions=case.repetitions,
        warmup_iterations=case.warmup_iterations,
        config=_canonicalize_jsonable(case.config),
        output_summary=output_summary,
        timing=BenchmarkTimingSummary(
            durations_ns=tuple(durations),
            total_duration_ns=total_duration_ns,
            min_duration_ns=min(durations),
            max_duration_ns=max(durations),
            average_duration_ns=total_duration_ns // len(durations),
        ),
    )


def run_benchmark_suite(
    suite_name: str,
    cases: tuple[BenchmarkCase, ...] | list[BenchmarkCase],
    *,
    clock: BenchmarkClock | None = None,
) -> BenchmarkSuiteResult:
    """Execute a benchmark suite in the exact provided case order."""

    return BenchmarkSuiteResult(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        suite_name=suite_name,
        case_results=tuple(
            run_benchmark_case(case, clock=clock) for case in tuple(cases)
        ),
    )


def benchmark_timing_to_dict(summary: BenchmarkTimingSummary) -> dict[str, Any]:
    """Convert timing summary into a stable JSON-ready record."""

    return {
        "durations_ns": list(summary.durations_ns),
        "total_duration_ns": summary.total_duration_ns,
        "min_duration_ns": summary.min_duration_ns,
        "max_duration_ns": summary.max_duration_ns,
        "average_duration_ns": summary.average_duration_ns,
    }


def benchmark_case_result_to_dict(result: BenchmarkCaseResult) -> dict[str, Any]:
    """Convert one case result into a stable JSON-ready record."""

    return {
        "name": result.name,
        "category": result.category,
        "repetitions": result.repetitions,
        "warmup_iterations": result.warmup_iterations,
        "config": _canonicalize_jsonable(result.config),
        "output_summary": _canonicalize_jsonable(result.output_summary),
        "timing": benchmark_timing_to_dict(result.timing),
    }


def benchmark_suite_result_to_dict(result: BenchmarkSuiteResult) -> dict[str, Any]:
    """Convert one suite result into a stable JSON-ready record."""

    return {
        "schema_version": result.schema_version,
        "suite_name": result.suite_name,
        "case_results": [
            benchmark_case_result_to_dict(case_result)
            for case_result in result.case_results
        ],
    }


def export_benchmark_suite_json(result: BenchmarkSuiteResult) -> str:
    """Return deterministic JSON for one benchmark suite run."""

    return json.dumps(
        benchmark_suite_result_to_dict(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def _canonicalize_jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True))
