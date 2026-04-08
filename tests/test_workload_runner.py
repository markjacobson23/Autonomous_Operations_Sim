import json

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.exports import export_engine_json
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations import (
    FirstFeasibleDispatcher,
    Job,
    LoadTask,
    MoveTask,
    SharedResource,
    UnloadTask,
)
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, summarize_engine_execution
from autonomous_ops_sim.simulation.workload_runner import run_dispatch_job_queue
from autonomous_ops_sim.simulation.world_state import WorldState
from autonomous_ops_sim.vehicles.vehicle import Vehicle


def build_workload_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (10.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 10.0, 5.0))
    graph.add_edge(Edge(2, node_2, node_1, 10.0, 5.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (10.0, 0.0, 0.0): 2,
        },
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=416,
        resources=(SharedResource("loader-16", initial_available_times_s=(3.0,)),),
    )


def run_workload_once():
    engine = build_workload_engine()
    vehicle = Vehicle(
        id=16,
        current_node_id=1,
        position=engine.map.get_position(1),
        velocity=0.0,
        payload=0.0,
        max_payload=10.0,
        max_speed=5.0,
    )
    workload_result = run_dispatch_job_queue(
        engine=engine,
        dispatcher=FirstFeasibleDispatcher(),
        vehicle=vehicle,
        pending_jobs=(
            Job(
                id="yard-dropoff",
                tasks=(UnloadTask(node_id=1, amount=2.0, service_duration_s=1.0),),
            ),
            Job(
                id="pickup-cycle",
                tasks=(
                    MoveTask(destination_node_id=2),
                    LoadTask(
                        node_id=2,
                        amount=2.0,
                        service_duration_s=2.0,
                        resource_id="loader-16",
                    ),
                    MoveTask(destination_node_id=1),
                ),
            ),
            Job(
                id="reposition",
                tasks=(MoveTask(destination_node_id=2),),
            ),
        ),
    )
    summary = summarize_engine_execution(engine)
    export_json = export_engine_json(engine, summary=summary)
    return workload_result, vehicle, summary, export_json, engine.trace.events


def test_dispatch_job_queue_executes_multiple_jobs_with_one_persistent_vehicle():
    workload_result, vehicle, summary, export_json, _ = run_workload_once()
    export_record = json.loads(export_json)

    assert workload_result.completed_job_ids == (
        "pickup-cycle",
        "yard-dropoff",
        "reposition",
    )
    assert workload_result.remaining_job_ids == ()
    assert vehicle.current_node_id == 2
    assert vehicle.payload == 0.0
    assert vehicle.operational_state == "idle"
    assert summary.final_time_s == 10.0
    assert summary.completed_job_count == 3
    assert summary.completed_task_count == 5
    assert summary.route_count == 3
    assert summary.total_route_distance == 30.0
    assert summary.total_service_time_s == 3.0
    assert summary.total_resource_wait_time_s == 1.0
    assert export_record["summary"]["completed_job_count"] == 3
    assert [
        event["job_id"]
        for event in export_record["trace"]
        if event["event_type"] == "job_start"
    ] == ["pickup-cycle", "yard-dropoff", "reposition"]


def test_dispatch_job_queue_repeated_runs_are_identical():
    first_result = run_workload_once()
    second_result = run_workload_once()

    assert first_result[0] == second_result[0]
    assert first_result[1].current_node_id == second_result[1].current_node_id
    assert first_result[1].payload == second_result[1].payload
    assert first_result[2] == second_result[2]
    assert first_result[3] == second_result[3]
    assert first_result[4] == second_result[4]
