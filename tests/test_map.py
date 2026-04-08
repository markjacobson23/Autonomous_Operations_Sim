from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node, NodeType
from autonomous_ops_sim.maps.map import Map
import pytest

def build_test_map() -> tuple[Map, list[Node], list[Edge]]:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0), NodeType.DEPOT)
    node_2 = Node(2, (1.0, 0.0, 0.0), NodeType.INTERSECTION)
    node_3 = Node(3, (0.0, 1.0, 0.0), NodeType.LOADING_ZONE)
    node_4 = Node(4, (2.0, 0.0, 0.0), NodeType.UNLOADING_ZONE)
    node_5 = Node(5, (5.0, 5.0, 0.0), NodeType.CHARGING_STATION)
    node_6 = Node(6, (6.0, 6.0, 5.0), NodeType.CHARGING_STATION)
    nodes_list = [node_1, node_2, node_3, node_4, node_5, node_6]
    for node in nodes_list:
        graph.add_node(node)

    edge_1 = Edge(1, node_1, node_2, 1.0, 25.0)
    edge_2 = Edge(2, node_2, node_4, 1.0, 25.0)
    edge_3 = Edge(3, node_1, node_3, 1.0, 25.0)
    edge_4 = Edge(4, node_3, node_2, 1.0, 25.0)
    edge_5 = Edge(5, node_4, node_5, 1.0, 25.0)
    edges_list = [edge_1, edge_2, edge_3, edge_4, edge_5]
    for edge in edges_list:
        graph.add_edge(edge)

    coord_to_id = {
        (0.0, 0.0, 0.0): 1,
        (1.0, 0.0, 0.0): 2,
        (0.0, 1.0, 0.0): 3,
        (2.0, 0.0, 0.0): 4,
        (5.0, 5.0, 0.0): 5,
        (6.0, 6.0, 5.0): 6,
    }

    return Map(graph, coord_to_id), nodes_list, edges_list

@pytest.fixture
def map_parts():
    return build_test_map()

def test_has_coordinate_returns_true_for_existing_coordinate(map_parts):
    test_map, _, _ = map_parts
    assert test_map.has_coordinate((0.0, 0.0, 0.0))

def test_has_coordinate_returns_false_for_missing_coordinate(map_parts):
    test_map, _, _ = map_parts
    assert not test_map.has_coordinate((10.0, 10.0, 10.0))

def test_get_node_id_returns_correct_id_for_existing_coordinate(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_node_id((0.0, 0.0, 0.0)) == 1

def test_get_node_id_raises_for_missing_coordinate(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(KeyError):
        test_map.get_node_id((10.0, 10.0, 10.0))

def test_get_position_returns_correct_coordinate_for_existing_node(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_position(1) == (0.0, 0.0, 0.0)

def test_get_position_raises_for_missing_node(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(KeyError):
        test_map.get_position(99)

def test_get_nodes_by_type_returns_matching_node_ids(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_nodes_by_type(NodeType.DEPOT) == [1]

def test_get_node_type_returns_type_for_existing_node(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_node_type(1) == NodeType.DEPOT

def test_get_node_type_raises_for_missing_node(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(KeyError):
        test_map.get_node_type(99)

def test_get_nodes_in_region_returns_nodes_inside_bounds(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_nodes_in_region(0,0,0,2,2,2) == [1, 2, 3, 4]

def test_get_nodes_in_region_raises_when_max_less_than_min(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(ValueError):
        test_map.get_nodes_in_region(2,0,0,1,1,1)

def test_get_node_returns_node_for_existing_id(map_parts):
    test_map, test_nodes, _ = map_parts
    assert test_map.get_node(1) is test_nodes[0]

def test_get_node_raises_for_missing_id(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(KeyError):
        test_map.get_node(99)

def test_get_all_node_ids_returns_all_ids(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_all_node_ids() == [1, 2, 3, 4, 5, 6]

def test_get_nearest_node_of_type_returns_closest_matching_node(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_nearest_node_of_type((5.0, 5.0, 5.0), NodeType.CHARGING_STATION) == 6

def test_get_nearest_node_of_type_raises_when_no_nodes_of_type_exist(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(ValueError):
        test_map.get_nearest_node_of_type((5.0, 5.0, 5.0), NodeType.JOB_SITE)

def test_get_outgoing_edges_returns_copy_from_graph(map_parts):
    test_map, _, _ = map_parts
    outgoing_edges = test_map.get_outgoing_edges(1)
    outgoing_edges.pop()
    new_outgoing_edges = test_map.get_outgoing_edges(1)
    assert len(outgoing_edges) == 1
    assert len(new_outgoing_edges) == 2

def test_get_neighbors_returns_direct_neighbor_ids(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_neighbors(1) == [2, 3]

def test_get_edge_between_returns_edge_when_present(map_parts):
    test_map, _, test_edges = map_parts
    assert test_map.get_edge_between(1, 3) == test_edges[2]

def test_get_edge_between_returns_none_when_missing(map_parts):
    test_map, _, _ = map_parts
    assert test_map.get_edge_between(1, 4) is None

def test_get_edges_from_position_returns_outgoing_edges_for_coordinate(map_parts):
    test_map, _, test_edges = map_parts
    assert test_map.get_edges_from_position((0.0, 0.0, 0.0)) == [test_edges[0], test_edges[2]]

def test_validate_path_returns_true_for_valid_path(map_parts):
    test_map, _, _ = map_parts
    assert test_map.validate_path([1, 2, 4])

def test_validate_path_returns_true_for_empty_path(map_parts):
    test_map, _, _ = map_parts
    assert test_map.validate_path([])

def test_validate_path_returns_false_for_missing_node(map_parts):
    test_map, _, _ = map_parts
    assert not test_map.validate_path([1, 2, 99])

def test_validate_path_returns_false_for_missing_edge(map_parts):
    test_map, _, _ = map_parts
    assert not test_map.validate_path([1, 2, 3, 4])

def test_map_no_longer_owns_runtime_edge_blocking(map_parts):
    test_map, _, _ = map_parts
    with pytest.raises(AttributeError):
        _ = test_map.block_edge
    with pytest.raises(AttributeError):
        _ = test_map.unblock_edge
