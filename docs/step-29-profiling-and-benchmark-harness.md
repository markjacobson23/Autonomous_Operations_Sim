# Step 29 Profiling and Benchmark Harness

## Goal
Finish Step 29 cleanly by adding repeatable performance measurement surfaces for the simulator.

## Required implementation
Add a benchmark/profiling harness that measures the current simulator architecture without changing its semantics.

## Required design
- Reuse the existing:
  - routing surfaces
  - simulation engine
  - scenario execution
  - scenario-pack execution
  - visualization/export/live-sync surfaces where relevant
- Add a module or package such as:
  - `autonomous_ops_sim/benchmarks/`
  - or `autonomous_ops_sim/perf/`
- Keep measurement logic separate from the core runtime where possible

## Required behavior
- Benchmarks can be run repeatably
- Results are summarized in a stable, machine-readable or clearly structured form
- The harness covers at least the most likely current hotspots
- Benchmarking itself does not alter simulator semantics

## Minimum expected scope
At minimum, Step 29 should support:
- routing benchmark(s)
- scenario or scenario-pack execution benchmark(s)
- at least one coordination/reservation-related benchmark or proxy
- at least one replay/export/live-sync generation benchmark
- stable summary output for results

## Design constraints
- Do not start major optimization work yet
- Do not split to another language/runtime yet
- Do not redesign the simulator for the sake of benchmarks
- Do not overbuild a full benchmarking platform
- Keep the implementation small and production-like

## Preferred strategy
- Measure the current system honestly
- Start with the smallest useful benchmark suite that can guide later work
- Prefer stable benchmark result records over one-off printouts
- Include enough context in outputs to make later comparisons meaningful

## Tests to add
Add tests for:
- stable benchmark harness behavior
- deterministic benchmark config/result formatting where practical
- repeated benchmark scaffolding producing structurally consistent results

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
