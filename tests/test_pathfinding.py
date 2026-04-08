from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.routing.pathfinding import dijkstra
from autonomous_ops_sim.simulation.world_state import WorldState
import pytest

def build_indirect_route_cheaper_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (1, 0, 0))
    node_3 = Node(3, (2, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 25.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 25.0))
    graph.add_edge(Edge(3, node_1, node_3, 5.0, 25.0))

    return graph

def build_direct_route_cheaper_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (1, 0, 0))
    node_3 = Node(3, (2, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 2.0, 25.0))
    graph.add_edge(Edge(2, node_2, node_3, 2.0, 25.0))
    graph.add_edge(Edge(3, node_1, node_3, 1.0, 25.0))
    return graph

def build_unreachable_node_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (1, 0, 0))
    node_3 = Node(3, (2, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 25.0))

    return graph

def build_blocked_route_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (1, 0, 0))
    node_3 = Node(3, (2, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 25.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 25.0))
    graph.add_edge(Edge(3, node_1, node_3, 3.0, 25.0))

    return graph

def build_all_routes_blocked_graph() -> Graph:
    graph = Graph()

    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (1, 0, 0))
    node_3 = Node(3, (2, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 25.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 25.0))
    graph.add_edge(Edge(3, node_1, node_3, 3.0, 25.0))

    return graph


def test_dijkstra_returns_shortest_path():

    graph = build_indirect_route_cheaper_graph()

    cost, path = dijkstra(graph, 1, 3)

    assert cost == 2.0
    assert path == [1, 2, 3]

def test_dijkstra_returns_direct_path_when_it_is_cheapest():
    graph = build_direct_route_cheaper_graph()

    cost, path = dijkstra(graph,1,3)

    assert cost == 1.0
    assert path == [1, 3]


def test_dijkstra_returns_trivial_path_when_start_equals_end():
    graph = build_direct_route_cheaper_graph()

    cost, path = dijkstra(graph, 1, 1)

    assert cost == 0.0
    assert path == [1]

def test_dijkstra_raises_for_missing_start():
    graph = build_direct_route_cheaper_graph()

    with pytest.raises(ValueError):
        dijkstra(graph, 99, 3)

def test_dijkstra_raises_for_missing_end():
    graph = build_direct_route_cheaper_graph()

    with pytest.raises(ValueError):
        dijkstra(graph, 3, 99)

def test_dijkstra_raises_for_unreachable_destination():
    graph = build_unreachable_node_graph()

    with pytest.raises(ValueError):
        dijkstra(graph, 1, 3)

def test_dijkstra_ignores_blocked_edge_and_uses_alternate_route():
    graph = build_blocked_route_graph()
    world_state = WorldState(graph)
    world_state.block_edge(2)

    cost, path = dijkstra(graph, 1, 3, world_state=world_state)

    assert cost == 3.0
    assert path == [1, 3]

def test_dijkstra_raises_when_all_routes_are_blocked():
    graph = build_all_routes_blocked_graph()
    world_state = WorldState(graph)
    world_state.block_edge(1)
    world_state.block_edge(3)

    with pytest.raises(ValueError):
        dijkstra(graph, 1, 3, world_state=world_state)
