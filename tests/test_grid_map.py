from autonomous_ops_sim.maps.grid_map import make_grid_map

def test_make_grid_map_creates_correct_number_of_nodes():
    grid_map = make_grid_map(2)
    assert len(grid_map.get_all_node_ids()) == 4


def test_make_grid_map_creates_correct_number_of_edges():
    grid_map = make_grid_map(2)
    assert len(grid_map._graph.edges) == 8


def test_make_grid_map_creates_nodes_for_all_grid_coordinates():
    grid_map = make_grid_map(2)
    expected_positions = {
        (0, 0, 0), (1, 0, 0),
        (0, 1, 0), (1, 1, 0)
    }
    positions = {grid_map.get_position(node_id) for node_id in grid_map.get_all_node_ids()}
    assert expected_positions == positions


def test_make_grid_map_assigns_unique_positions_to_nodes():
    grid_map = make_grid_map(2)
    positions = [grid_map.get_position(nid) for nid in grid_map.get_all_node_ids()]
    assert len(positions) == len(set(positions))


def test_make_grid_map_connects_adjacent_coordinates_in_both_directions():
    grid_map = make_grid_map(2)
    node00 = grid_map.get_node_id((0, 0, 0))
    node10 = grid_map.get_node_id((1, 0, 0))
    node01 = grid_map.get_node_id((0, 1, 0))

    assert grid_map.get_edge_between(node00, node10) is not None
    assert grid_map.get_edge_between(node10, node00) is not None
    assert grid_map.get_edge_between(node00, node01) is not None
    assert grid_map.get_edge_between(node01, node00) is not None


def test_make_grid_map_corner_node_has_two_outgoing_edges():
    grid_map = make_grid_map(3)
    corner = grid_map.get_node_id((0, 0, 0))
    assert len(grid_map.get_outgoing_edges(corner)) == 2


def test_make_grid_map_edge_node_has_three_outgoing_edges():
    grid_map = make_grid_map(3)
    edge_node = grid_map.get_node_id((0, 1, 0))
    assert len(grid_map.get_outgoing_edges(edge_node)) == 3


def test_make_grid_map_interior_node_has_four_outgoing_edges():
    grid_map = make_grid_map(3)
    interior = grid_map.get_node_id((1, 1, 0))
    assert len(grid_map.get_outgoing_edges(interior)) == 4


def test_make_grid_map_does_not_create_diagonal_edges():
    grid_map = make_grid_map(2)
    node00 = grid_map.get_node_id((0, 0, 0))
    node11 = grid_map.get_node_id((1, 1, 0))
    assert grid_map.get_edge_between(node00, node11) is None