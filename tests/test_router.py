from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.routing import (
    CostModel,
    DistanceCostModel,
    Router,
    TimeCostModel,
)
from autonomous_ops_sim.simulation.world_state import WorldState
import pytest


class NegativeCostModel:
    def edge_cost(self, edge: Edge) -> float:
        return -1.0


def make_edge(
    edge_id: int,
    start_id: int,
    end_id: int,
    distance: float,
    speed_limit: float,
) -> Edge:
    return Edge(
        edge_id,
        Node(start_id, (float(start_id), 0.0, 0.0)),
        Node(end_id, (float(end_id), 0.0, 0.0)),
        distance,
        speed_limit,
    )


def build_route_choice_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (0.0, 1.0, 0.0))
    node_4 = Node(4, (2.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)
    graph.add_node(node_4)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 1.0))
    graph.add_edge(Edge(2, node_2, node_4, 1.0, 1.0))
    graph.add_edge(Edge(3, node_1, node_3, 3.0, 10.0))
    graph.add_edge(Edge(4, node_3, node_4, 3.0, 10.0))

    return graph


def test_router_is_public_routing_surface():
    router = Router()

    assert isinstance(router, Router)
    assert callable(router.route)


def test_router_defaults_to_distance_based_routing():
    graph = build_route_choice_graph()
    router = Router()

    cost, path = router.route(graph, 1, 4)

    assert cost == 2.0
    assert path == [1, 2, 4]


def test_router_can_choose_different_route_with_time_cost_model():
    graph = build_route_choice_graph()
    router = Router(cost_model=TimeCostModel())

    cost, path = router.route(graph, 1, 4)

    assert cost == 0.6
    assert path == [1, 3, 4]


def test_router_still_respects_blocked_edges_through_world_state():
    graph = build_route_choice_graph()
    world_state = WorldState(graph)
    world_state.block_edge(2)
    router = Router()

    cost, path = router.route(graph, 1, 4, world_state=world_state)

    assert cost == 6.0
    assert path == [1, 3, 4]


def test_router_rejects_negative_costs_clearly():
    graph = build_route_choice_graph()
    router = Router(cost_model=NegativeCostModel())

    with pytest.raises(
        ValueError,
        match="Dijkstra-based routing requires non-negative edge costs",
    ):
        router.route(graph, 1, 4)


def test_public_cost_model_types_are_importable_from_routing():
    distance_model: CostModel = DistanceCostModel()
    time_model: CostModel = TimeCostModel()

    assert distance_model.edge_cost(make_edge(99, 9, 10, 2.0, 5.0)) == 2.0
    assert time_model.edge_cost(make_edge(100, 11, 12, 2.0, 4.0)) == 0.5
