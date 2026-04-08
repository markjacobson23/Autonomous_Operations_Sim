from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import DistanceCostModel, Router, TimeCostModel
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.world_state import WorldState


def build_demo_world() -> tuple[Map, Graph]:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (0.0, 1.0, 0.0))
    node_4 = Node(4, (2.0, 0.0, 0.0))
    node_5 = Node(5, (3.0, 0.0, 0.0))

    for node in (node_1, node_2, node_3, node_4, node_5):
        graph.add_node(node)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 1.0))
    graph.add_edge(Edge(2, node_2, node_4, 1.0, 1.0))
    graph.add_edge(Edge(5, node_4, node_5, 1.0, 1.0))

    graph.add_edge(Edge(3, node_1, node_3, 3.0, 10.0))
    graph.add_edge(Edge(4, node_3, node_4, 3.0, 10.0))

    demo_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (0.0, 1.0, 0.0): 3,
            (2.0, 0.0, 0.0): 4,
            (3.0, 0.0, 0.0): 5,
        },
    )
    return demo_map, graph


def run_case(title: str, router: Router, blocked_edge_ids: set[int] | None = None) -> None:
    simulation_map, graph = build_demo_world()
    world_state = WorldState(graph)

    for edge_id in blocked_edge_ids or set():
        world_state.block_edge(edge_id)

    engine = SimulationEngine(
        simulation_map=simulation_map,
        world_state=world_state,
        router=router,
        seed=123,
    )

    route = engine.execute_vehicle_route(
        vehicle_id=101,
        start_node_id=1,
        destination_node_id=5,
        max_speed=20.0,
    )

    print(f"\n=== {title} ===")
    print("route:", route)
    print("final simulated time:", engine.simulated_time_s)
    for event in engine.trace.events:
        print(
            event.sequence,
            event.timestamp_s,
            event.event_type.value,
            event.node_id,
            event.edge_id,
            event.from_behavior_state,
            event.to_behavior_state,
            event.transition_reason,
        )


if __name__ == "__main__":
    run_case("distance", Router(DistanceCostModel()))
    run_case("time", Router(TimeCostModel()))
    run_case("time with fast edge blocked", Router(TimeCostModel()), blocked_edge_ids={3})