from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, TraceEventType, WorldState


def build_job_engine(*, resources: tuple[SharedResource, ...] = ()) -> SimulationEngine:
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
        resources=resources,
    )


def test_jobs_execute_tasks_in_declared_order():
    engine = build_job_engine()
    job = Job(
        id="haul-1",
        tasks=(
            MoveTask(destination_node_id=2),
            LoadTask(node_id=2, amount=5.0, service_duration_s=3.0),
            MoveTask(destination_node_id=3),
            UnloadTask(node_id=3, amount=5.0, service_duration_s=2.0),
        ),
    )

    result = engine.execute_job(
        vehicle_id=101,
        start_node_id=1,
        max_speed=5.0,
        job=job,
        max_payload=10.0,
    )

    assert result.completed_task_count == 4
    assert result.final_node_id == 3
    assert result.final_payload == 0.0
    assert [
        event.task_type
        for event in engine.trace.events
        if event.event_type == TraceEventType.TASK_START
    ] == ["move", "load", "move", "unload"]
    assert [
        event.task_index
        for event in engine.trace.events
        if event.event_type == TraceEventType.TASK_COMPLETE
    ] == [0, 1, 2, 3]


def test_service_timing_advances_simulated_time_for_load_and_unload():
    engine = build_job_engine()
    job = Job(
        id="haul-2",
        tasks=(
            MoveTask(destination_node_id=2),
            LoadTask(node_id=2, amount=2.0, service_duration_s=3.0),
            MoveTask(destination_node_id=3),
            UnloadTask(node_id=3, amount=2.0, service_duration_s=2.0),
        ),
    )

    engine.execute_job(
        vehicle_id=202,
        start_node_id=1,
        max_speed=5.0,
        job=job,
        max_payload=10.0,
    )

    assert engine.simulated_time_s == 8.0
    assert [
        event.timestamp_s
        for event in engine.trace.events
        if event.event_type
        in (TraceEventType.SERVICE_START, TraceEventType.SERVICE_COMPLETE)
    ] == [2.0, 5.0, 6.0, 8.0]


def test_shared_resources_force_waiting_when_busy():
    shovel = SharedResource(
        "shovel-a",
        initial_available_times_s=(4.0,),
    )
    engine = build_job_engine(resources=(shovel,))
    job = Job(
        id="haul-3",
        tasks=(
            MoveTask(destination_node_id=2),
            LoadTask(
                node_id=2,
                amount=1.0,
                service_duration_s=3.0,
                resource_id="shovel-a",
            ),
        ),
    )

    engine.execute_job(
        vehicle_id=303,
        start_node_id=1,
        max_speed=5.0,
        job=job,
        max_payload=5.0,
    )

    wait_events = [
        event
        for event in engine.trace.events
        if event.event_type == TraceEventType.RESOURCE_WAIT_START
    ]
    assert len(wait_events) == 1
    assert wait_events[0].timestamp_s == 2.0
    assert wait_events[0].duration_s == 2.0
    assert [
        (event.event_type, event.timestamp_s)
        for event in engine.trace.events
        if event.event_type
        in (
            TraceEventType.RESOURCE_WAIT_START,
            TraceEventType.RESOURCE_WAIT_COMPLETE,
            TraceEventType.SERVICE_START,
            TraceEventType.SERVICE_COMPLETE,
        )
    ] == [
        (TraceEventType.RESOURCE_WAIT_START, 2.0),
        (TraceEventType.RESOURCE_WAIT_COMPLETE, 4.0),
        (TraceEventType.SERVICE_START, 4.0),
        (TraceEventType.SERVICE_COMPLETE, 7.0),
    ]
    assert engine.simulated_time_s == 7.0


def test_repeated_runs_with_same_job_and_resources_are_deterministic():
    def run_once() -> tuple[float, tuple[object, ...]]:
        engine = build_job_engine(
            resources=(SharedResource("dock-1", initial_available_times_s=(3.0,)),)
        )
        job = Job(
            id="haul-4",
            tasks=(
                MoveTask(destination_node_id=2),
                LoadTask(
                    node_id=2,
                    amount=4.0,
                    service_duration_s=2.0,
                    resource_id="dock-1",
                ),
                MoveTask(destination_node_id=3),
                UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
            ),
        )
        engine.execute_job(
            vehicle_id=404,
            start_node_id=1,
            max_speed=5.0,
            job=job,
            max_payload=10.0,
        )
        return engine.simulated_time_s, engine.trace.events

    final_time_a, trace_a = run_once()
    final_time_b, trace_b = run_once()

    assert final_time_a == final_time_b
    assert trace_a == trace_b
