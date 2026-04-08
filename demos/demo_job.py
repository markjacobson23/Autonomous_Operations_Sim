from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import summarize_engine_execution
from autonomous_ops_sim.simulation.world_state import WorldState


def build_engine() -> SimulationEngine:
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
        resources=(SharedResource("dock-a", initial_available_times_s=(4.0,)),),
    )


if __name__ == "__main__":
    engine = build_engine()

    result = engine.execute_job(
        vehicle_id=911,
        start_node_id=1,
        max_speed=5.0,
        max_payload=8.0,
        job=Job(
            id="demo-haul",
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
    )

    print("job result:", result)
    print("final simulated time:", engine.simulated_time_s)

    summary = summarize_engine_execution(engine)
    print("\nsummary:")
    print(summary)

    print("\ntrace:")
    for event in engine.trace.events:
        print(
            event.sequence,
            event.timestamp_s,
            event.event_type.value,
            event.job_id,
            event.task_index,
            event.task_type,
            event.resource_id,
            event.duration_s,
            event.from_behavior_state,
            event.to_behavior_state,
            event.transition_reason,
        )