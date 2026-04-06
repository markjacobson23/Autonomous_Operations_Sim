from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.node import Node
import pytest

def test_add_node_adds_node_to_graph():
    graph = Graph()
    node = Node(1, (0, 0, 0))

    graph.add_node(node)

    assert graph.nodes[1] is node
    assert graph.adjacency[1] == []

def test_add_node_raises_for_duplicate_node_id():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(1, (0, 1, 0))

    graph.add_node(node_1)

    with pytest.raises(ValueError):
        graph.add_node(node_2)

def test_add_edge_adds_edge_to_graph():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)

    edge = Edge(1, node_1, node_2, 1, 1)

    graph.add_edge(edge)

    assert graph.edges[1] is edge
    assert graph.adjacency[1][0] is edge

def test_add_edge_raises_for_duplicate_edge_id():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))
    node_3 = Node(3, (1, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    edge_1 = Edge(1, node_1, node_2, 1, 1)
    edge_2 = Edge(1,node_1, node_3, 1, 1)

    graph.add_edge(edge_1)

    with pytest.raises(ValueError):
        graph.add_edge(edge_2)

def test_add_edge_raises_when_start_node_missing():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))

    graph.add_node(node_2)

    edge = Edge(1, node_1, node_2, 1, 1)

    with pytest.raises(ValueError):
        graph.add_edge(edge)

def test_add_edge_raises_when_end_node_missing():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))

    graph.add_node(node_1)

    edge = Edge(1, node_1, node_2, 1, 1)

    with pytest.raises(ValueError):
        graph.add_edge(edge)


def test_add_edge_raises_for_duplicate_start_end_pair():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)

    edge_1 = Edge(1, node_1, node_2, 1, 1)
    edge_2 = Edge(2, node_1, node_2, 1, 1)

    graph.add_edge(edge_1)

    with pytest.raises(ValueError):
        graph.add_edge(edge_2)

def test_get_outgoing_edges_returns_copy_of_outgoing_edges():
    graph = Graph()
    node_1 = Node(1, (0, 0, 0))
    node_2 = Node(2, (0, 1, 0))
    node_3 = Node(3, (1, 0, 0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    edge_1 = Edge(1, node_1, node_2, 1, 1)
    edge_2 = Edge(2, node_1, node_3, 1, 1)

    graph.add_edge(edge_1)
    graph.add_edge(edge_2)

    outgoing_edges = graph.get_outgoing_edges(1)
    outgoing_edges.pop()

    assert len(outgoing_edges) == 1
    assert len(graph.adjacency[1]) == 2
    assert graph.adjacency[1] == [edge_1, edge_2]

def test_get_outgoing_edges_raises_for_missing_node():
    graph = Graph()

    with pytest.raises(KeyError):
        graph.get_outgoing_edges(1)

