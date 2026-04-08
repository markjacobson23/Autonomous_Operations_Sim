from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing.pathfinding import dijkstra
from autonomous_ops_sim.simulation.world_state import WorldState
import pytest


def build_map_and_graph() -> tuple[Map, Graph]:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (2.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 25.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 25.0))
    graph.add_edge(Edge(3, node_1, node_3, 5.0, 25.0))

    test_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
        },
    )
    return test_map, graph


def test_default_world_state_has_no_blocked_edges():
    _, graph = build_map_and_graph()
    world_state = WorldState(graph)

    assert world_state.blocked_edge_ids == set()
    assert not world_state.is_edge_blocked(1)
    assert not world_state.is_edge_blocked(2)
    assert not world_state.is_edge_blocked(3)


def test_blocked_edge_routing_changes_happen_through_world_state():
    _, graph = build_map_and_graph()
    world_state = WorldState(graph)
    world_state.block_edge(2)

    cost, path = dijkstra(graph, 1, 3, world_state=world_state)

    assert cost == 5.0
    assert path == [1, 3]


def test_same_map_can_be_used_with_independent_world_states():
    test_map, graph = build_map_and_graph()
    world_state_a = WorldState(graph)
    world_state_b = WorldState(graph)
    world_state_a.block_edge(2)

    cost_a, path_a = dijkstra(graph, 1, 3, world_state=world_state_a)
    cost_b, path_b = dijkstra(graph, 1, 3, world_state=world_state_b)

    assert test_map.get_node_id((0.0, 0.0, 0.0)) == 1
    assert cost_a == 5.0
    assert path_a == [1, 3]
    assert cost_b == 2.0
    assert path_b == [1, 2, 3]


def test_fresh_default_world_state_restores_baseline_behavior():
    _, graph = build_map_and_graph()
    world_state = WorldState(graph)
    world_state.block_edge(2)

    rerouted_cost, rerouted_path = dijkstra(graph, 1, 3, world_state=world_state)
    baseline_cost, baseline_path = dijkstra(graph, 1, 3)

    assert rerouted_cost == 5.0
    assert rerouted_path == [1, 3]
    assert baseline_cost == 2.0
    assert baseline_path == [1, 2, 3]


def test_world_state_raises_for_unknown_edge_ids():
    _, graph = build_map_and_graph()
    world_state = WorldState(graph)

    with pytest.raises(KeyError):
        world_state.block_edge(999)
