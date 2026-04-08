from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import summarize_engine_execution
from autonomous_ops_sim.simulation.reservations import VehicleRouteRequest
from autonomous_ops_sim.simulation.world_state import WorldState


def build_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 1.0, 1.0))
    graph.add_edge(Edge(2, node_2, node_1, 1.0, 1.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
        },
    )

    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=9,
    )


if __name__ == "__main__":
    engine = build_engine()

    result = engine.execute_multi_vehicle_routes(
        requests=(
            VehicleRouteRequest(
                vehicle_id=20,
                start_node_id=2,
                destination_node_id=1,
                max_speed=1.0,
            ),
            VehicleRouteRequest(
                vehicle_id=10,
                start_node_id=1,
                destination_node_id=2,
                max_speed=1.0,
            ),
        )
    )

    print("route results:")
    for route_result in result.route_results:
        print(route_result)

    print("\nedge reservations:")
    for reservation in result.reservations.edge_reservations:
        print(reservation)

    print("\nnode reservations:")
    for reservation in result.reservations.node_reservations:
        print(reservation)

    print("\nsummary:")
    print(summarize_engine_execution(engine))

    print("\ntrace:")
    for event in engine.trace.events:
        print(
            event.sequence,
            event.timestamp_s,
            event.vehicle_id,
            event.event_type.value,
            event.node_id,
            event.edge_id,
            event.duration_s,
            event.from_behavior_state,
            event.to_behavior_state,
            event.transition_reason,
        )