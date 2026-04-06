from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.core.edge import Edge
from itertools import product
from autonomous_ops_sim.maps.map import Map
def make_grid_map(grid_size: int) -> Map:
    grid = [(float(x), float(y), 0.0) for x, y in product(range(grid_size), range(grid_size))]
    graph_out = Graph()
    coord_to_id = {}
    for node_id, coord in enumerate(grid):
        graph_out.add_node(Node(node_id, coord))
        coord_to_id[coord] = node_id
    vectors = [(0,1,0),(1,0,0)]
    edge_id = 0
    for coord in grid:
        for v in vectors:
            neighbor = (coord[0] + v[0], coord[1] + v[1], 0.0)
            if neighbor in coord_to_id:
                graph_out.add_edge(
                    Edge(edge_id, graph_out.nodes[coord_to_id[coord]], graph_out.nodes[coord_to_id[neighbor]],1,1)
                )
                graph_out.add_edge(
                    Edge(edge_id + 1, graph_out.nodes[coord_to_id[neighbor]], graph_out.nodes[coord_to_id[coord]], 1, 1)
                )
                edge_id += 2
    return Map(graph_out, coord_to_id)




