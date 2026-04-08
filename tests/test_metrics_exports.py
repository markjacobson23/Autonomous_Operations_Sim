import json
from pathlib import Path

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.exports import (
    EXPORT_SCHEMA_VERSION,
    build_engine_export,
    export_engine_json,
    metrics_summary_to_dict,
    trace_event_to_dict,
)
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    ExecutionMetricsSummary,
    SimulationEngine,
    TraceEventCount,
    WorldState,
    summarize_engine_execution,
)


def build_metrics_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (10.0, 0.0, 0.0))
    node_3 = Node(3, (15.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)
    graph.add_edge(Edge(1, node_1, node_2, 10.0, 5.0))
    graph.add_edge(Edge(2, node_2, node_3, 5.0, 5.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (10.0, 0.0, 0.0): 2,
            (15.0, 0.0, 0.0): 3,
        },
    )

    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=117,
        resources=(SharedResource("dock-a", initial_available_times_s=(4.0,)),),
    )


def run_golden_job() -> SimulationEngine:
    engine = build_metrics_engine()
    engine.execute_job(
        vehicle_id=911,
        start_node_id=1,
        max_speed=5.0,
        job=Job(
            id="step-11-golden-job",
            tasks=(
                MoveTask(destination_node_id=2),
                LoadTask(
                    node_id=2,
                    amount=4.0,
                    service_duration_s=3.0,
                    resource_id="dock-a",
                ),
                MoveTask(destination_node_id=3),
                UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
            ),
        ),
        max_payload=8.0,
    )
    return engine


def test_metrics_summary_is_correct_for_step_11_job_run():
    summary = summarize_engine_execution(run_golden_job())

    assert summary == ExecutionMetricsSummary(
        seed=117,
        final_time_s=9.0,
        trace_event_count=33,
        vehicle_ids=(911,),
        route_count=2,
        completed_job_count=1,
        completed_task_count=4,
        edge_traversal_count=2,
        node_arrival_count=2,
        total_route_distance=15.0,
        total_service_time_s=4.0,
        total_resource_wait_time_s=2.0,
        total_conflict_wait_time_s=0.0,
        event_counts=(
            TraceEventCount(event_type="behavior_transition", count=9),
            TraceEventCount(event_type="edge_enter", count=2),
            TraceEventCount(event_type="job_complete", count=1),
            TraceEventCount(event_type="job_start", count=1),
            TraceEventCount(event_type="node_arrival", count=2),
            TraceEventCount(event_type="resource_wait_complete", count=1),
            TraceEventCount(event_type="resource_wait_start", count=1),
            TraceEventCount(event_type="route_complete", count=2),
            TraceEventCount(event_type="route_start", count=2),
            TraceEventCount(event_type="service_complete", count=2),
            TraceEventCount(event_type="service_start", count=2),
            TraceEventCount(event_type="task_complete", count=4),
            TraceEventCount(event_type="task_start", count=4),
        ),
    )


def test_export_format_is_stable_for_summary_and_trace_records():
    engine = run_golden_job()
    summary = summarize_engine_execution(engine)
    export_record = build_engine_export(engine, summary=summary)

    assert export_record["schema_version"] == EXPORT_SCHEMA_VERSION
    assert export_record["seed"] == 117
    assert export_record["final_time_s"] == 9.0
    assert export_record["summary"] == {
        "seed": 117,
        "final_time_s": 9.0,
        "trace_event_count": 33,
        "vehicle_ids": [911],
        "route_count": 2,
        "completed_job_count": 1,
        "completed_task_count": 4,
        "edge_traversal_count": 2,
        "node_arrival_count": 2,
        "total_route_distance": 15.0,
        "total_service_time_s": 4.0,
        "total_resource_wait_time_s": 2.0,
        "total_conflict_wait_time_s": 0.0,
        "event_counts": [
            {"event_type": "behavior_transition", "count": 9},
            {"event_type": "edge_enter", "count": 2},
            {"event_type": "job_complete", "count": 1},
            {"event_type": "job_start", "count": 1},
            {"event_type": "node_arrival", "count": 2},
            {"event_type": "resource_wait_complete", "count": 1},
            {"event_type": "resource_wait_start", "count": 1},
            {"event_type": "route_complete", "count": 2},
            {"event_type": "route_start", "count": 2},
            {"event_type": "service_complete", "count": 2},
            {"event_type": "service_start", "count": 2},
            {"event_type": "task_complete", "count": 4},
            {"event_type": "task_start", "count": 4},
        ],
    }
    assert metrics_summary_to_dict(summary) == export_record["summary"]
    assert len(export_record["trace"]) == 33
    assert export_record["trace"][0] == {
        "sequence": 0,
        "timestamp_s": 0.0,
        "vehicle_id": 911,
        "event_type": "job_start",
        "node_id": 1,
        "edge_id": None,
        "start_node_id": None,
        "end_node_id": None,
        "job_id": "step-11-golden-job",
        "task_index": None,
        "task_type": None,
        "resource_id": None,
        "duration_s": None,
        "from_behavior_state": None,
        "to_behavior_state": None,
        "transition_reason": None,
    }
    assert trace_event_to_dict(engine.trace.events[-1]) == export_record["trace"][-1]


def test_repeated_runs_produce_identical_summary_and_export_output():
    engine_a = run_golden_job()
    engine_b = run_golden_job()

    summary_a = summarize_engine_execution(engine_a)
    summary_b = summarize_engine_execution(engine_b)
    export_json_a = export_engine_json(engine_a, summary=summary_a)
    export_json_b = export_engine_json(engine_b, summary=summary_b)

    assert summary_a == summary_b
    assert export_json_a == export_json_b


def test_golden_regression_export_matches_expected_fixture():
    engine = run_golden_job()
    summary = summarize_engine_execution(engine)
    export_json = export_engine_json(engine, summary=summary)

    golden_path = Path(__file__).parent / "golden" / "step_11_metrics_export.json"

    assert json.loads(export_json) == json.loads(golden_path.read_text())
    assert export_json == golden_path.read_text()
