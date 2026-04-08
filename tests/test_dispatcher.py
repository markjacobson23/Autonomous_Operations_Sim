from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations import (
    DispatchRequest,
    FirstFeasibleDispatcher,
    Job,
    LoadTask,
    MoveTask,
    UnloadTask,
)
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, TraceEventType, WorldState
from autonomous_ops_sim.vehicles.vehicle import Vehicle


def build_job_engine() -> SimulationEngine:
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
        seed=17,
    )


def test_first_feasible_dispatcher_selects_jobs_deterministically():
    engine = build_job_engine()
    dispatcher = FirstFeasibleDispatcher()
    request = DispatchRequest(
        vehicle=Vehicle(
            id=501,
            current_node_id=1,
            position=engine.map.get_position(1),
            velocity=0.0,
            payload=0.0,
            max_payload=5.0,
            max_speed=5.0,
        )
    )
    pending_jobs = (
        Job(
            id="infeasible-load",
            tasks=(LoadTask(node_id=1, amount=6.0, service_duration_s=1.0),),
        ),
        Job(
            id="selected-haul",
            tasks=(
                MoveTask(destination_node_id=2),
                LoadTask(node_id=2, amount=4.0, service_duration_s=2.0),
                MoveTask(destination_node_id=3),
                UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
            ),
        ),
        Job(
            id="later-haul",
            tasks=(
                MoveTask(destination_node_id=2),
                LoadTask(node_id=2, amount=2.0, service_duration_s=2.0),
            ),
        ),
    )

    assignment_a = dispatcher.assign_job(
        pending_jobs=pending_jobs,
        engine=engine,
        request=request,
    )
    assignment_b = dispatcher.assign_job(
        pending_jobs=pending_jobs,
        engine=engine,
        request=request,
    )

    assert assignment_a is not None
    assert assignment_a == assignment_b
    assert assignment_a.job.id == "selected-haul"


def test_dispatch_assignment_carries_selected_job_and_vehicle():
    engine = build_job_engine()
    dispatcher = FirstFeasibleDispatcher()
    request = DispatchRequest(
        vehicle=Vehicle(
            id=601,
            current_node_id=1,
            position=engine.map.get_position(1),
            velocity=0.0,
            payload=0.0,
            max_payload=10.0,
            max_speed=5.0,
        )
    )
    job = Job(
        id="assigned-haul",
        tasks=(
            MoveTask(destination_node_id=2),
            LoadTask(node_id=2, amount=3.0, service_duration_s=1.0),
        ),
    )

    assignment = dispatcher.assign_job(
        pending_jobs=(job,),
        engine=engine,
        request=request,
    )

    assert assignment is not None
    assert assignment.vehicle_id == 601
    assert assignment.job == job


def test_dispatch_job_executes_selected_job_through_existing_engine_path():
    engine = build_job_engine()
    dispatcher = FirstFeasibleDispatcher()
    pending_jobs = (
        Job(
            id="too-large",
            tasks=(LoadTask(node_id=1, amount=12.0, service_duration_s=1.0),),
        ),
        Job(
            id="dispatch-haul",
            tasks=(
                MoveTask(destination_node_id=2),
                LoadTask(node_id=2, amount=5.0, service_duration_s=3.0),
                MoveTask(destination_node_id=3),
                UnloadTask(node_id=3, amount=5.0, service_duration_s=2.0),
            ),
        ),
    )

    result = engine.dispatch_job(
        dispatcher=dispatcher,
        pending_jobs=pending_jobs,
        vehicle_id=701,
        start_node_id=1,
        max_speed=5.0,
        max_payload=10.0,
    )

    assert result is not None
    assert result.assignment.job.id == "dispatch-haul"
    assert result.job_result.job_id == "dispatch-haul"
    assert result.job_result.completed_task_count == 4
    assert result.job_result.final_node_id == 3
    assert result.job_result.final_payload == 0.0
    assert engine.simulated_time_s == 8.0
    assert [
        event.job_id
        for event in engine.trace.events
        if event.event_type
        in (TraceEventType.JOB_START, TraceEventType.JOB_COMPLETE)
    ] == ["dispatch-haul", "dispatch-haul"]


def test_repeated_dispatch_runs_with_same_setup_produce_same_choice_and_outcome():
    def run_once() -> tuple[str, float, tuple[object, ...]]:
        engine = build_job_engine()
        result = engine.dispatch_job(
            dispatcher=FirstFeasibleDispatcher(),
            pending_jobs=(
                Job(
                    id="wrong-node",
                    tasks=(UnloadTask(node_id=2, amount=1.0, service_duration_s=1.0),),
                ),
                Job(
                    id="stable-choice",
                    tasks=(
                        MoveTask(destination_node_id=2),
                        LoadTask(node_id=2, amount=4.0, service_duration_s=2.0),
                        MoveTask(destination_node_id=3),
                        UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
                    ),
                ),
            ),
            vehicle_id=801,
            start_node_id=1,
            max_speed=5.0,
            max_payload=10.0,
        )

        assert result is not None
        return (
            result.assignment.job.id,
            engine.simulated_time_s,
            engine.trace.events,
        )

    assignment_a, final_time_a, trace_a = run_once()
    assignment_b, final_time_b, trace_b = run_once()

    assert assignment_a == assignment_b
    assert final_time_a == final_time_b
    assert trace_a == trace_b


def test_vehicle_backed_dispatch_execution_remains_deterministic():
    def run_once() -> tuple[str, float, float, tuple[object, ...]]:
        engine = build_job_engine()
        vehicle = Vehicle(
            id=901,
            current_node_id=1,
            position=engine.map.get_position(1),
            velocity=0.0,
            payload=0.0,
            max_payload=10.0,
            max_speed=5.0,
        )

        result = engine.dispatch_job(
            dispatcher=FirstFeasibleDispatcher(),
            pending_jobs=(
                Job(
                    id="not-feasible",
                    tasks=(UnloadTask(node_id=1, amount=1.0, service_duration_s=1.0),),
                ),
                Job(
                    id="vehicle-backed",
                    tasks=(
                        MoveTask(destination_node_id=2),
                        LoadTask(node_id=2, amount=4.0, service_duration_s=2.0),
                        MoveTask(destination_node_id=3),
                        UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
                    ),
                ),
            ),
            vehicle=vehicle,
        )

        assert result is not None
        return (
            result.assignment.job.id,
            engine.simulated_time_s,
            vehicle.payload,
            engine.trace.events,
        )

    assert run_once() == run_once()
