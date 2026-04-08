import json
from typing import Any

from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)
from autonomous_ops_sim.simulation.trace import TraceEvent


EXPORT_SCHEMA_VERSION = 1


def build_engine_export(
    engine: SimulationEngine,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> dict[str, Any]:
    """Return a stable structured export for one engine run."""

    metrics_summary = summary or summarize_engine_execution(engine)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "seed": engine.seed,
        "final_time_s": engine.simulated_time_s,
        "summary": metrics_summary_to_dict(metrics_summary),
        "trace": [trace_event_to_dict(event) for event in engine.trace.events],
    }


def export_engine_json(
    engine: SimulationEngine,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> str:
    """Return a deterministic JSON export for one engine run."""

    return json.dumps(
        build_engine_export(engine, summary=summary),
        indent=2,
        sort_keys=True,
    ) + "\n"


def metrics_summary_to_dict(summary: ExecutionMetricsSummary) -> dict[str, Any]:
    """Convert a metrics summary into a JSON-ready stable record."""

    return {
        "seed": summary.seed,
        "final_time_s": summary.final_time_s,
        "trace_event_count": summary.trace_event_count,
        "vehicle_ids": list(summary.vehicle_ids),
        "route_count": summary.route_count,
        "completed_job_count": summary.completed_job_count,
        "completed_task_count": summary.completed_task_count,
        "edge_traversal_count": summary.edge_traversal_count,
        "node_arrival_count": summary.node_arrival_count,
        "total_route_distance": summary.total_route_distance,
        "total_service_time_s": summary.total_service_time_s,
        "total_resource_wait_time_s": summary.total_resource_wait_time_s,
        "total_conflict_wait_time_s": summary.total_conflict_wait_time_s,
        "event_counts": [
            {
                "event_type": event_count.event_type,
                "count": event_count.count,
            }
            for event_count in summary.event_counts
        ],
    }


def trace_event_to_dict(event: TraceEvent) -> dict[str, Any]:
    """Convert one trace event into a JSON-ready stable record."""

    return {
        "sequence": event.sequence,
        "timestamp_s": event.timestamp_s,
        "vehicle_id": event.vehicle_id,
        "event_type": event.event_type.value,
        "node_id": event.node_id,
        "edge_id": event.edge_id,
        "start_node_id": event.start_node_id,
        "end_node_id": event.end_node_id,
        "job_id": event.job_id,
        "task_index": event.task_index,
        "task_type": event.task_type,
        "resource_id": event.resource_id,
        "duration_s": event.duration_s,
        "from_behavior_state": event.from_behavior_state,
        "to_behavior_state": event.to_behavior_state,
        "transition_reason": event.transition_reason,
    }
