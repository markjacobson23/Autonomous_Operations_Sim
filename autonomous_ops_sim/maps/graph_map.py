from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node, NodeType
from autonomous_ops_sim.maps.map import Map


def make_graph_map(
    *,
    nodes: tuple[dict[str, object], ...],
    edges: tuple[dict[str, object], ...],
) -> Map:
    """Build a map from explicit node and edge records."""

    graph = Graph()
    coord_to_id: dict[tuple[float, float, float], int] = {}

    for node_record in nodes:
        node_id = _required_int(node_record, "id")
        position = _position_from_record(node_record["position"])
        node_type = _node_type_from_name(node_record.get("node_type", "INTERSECTION"))
        node = Node(node_id, position, node_type)
        graph.add_node(node)
        coord_to_id[position] = node_id

    for edge_record in edges:
        edge = Edge(
            _required_int(edge_record, "id"),
            graph.nodes[_required_int(edge_record, "start_node_id")],
            graph.nodes[_required_int(edge_record, "end_node_id")],
            _required_float(edge_record, "distance"),
            _required_float(edge_record, "speed_limit"),
        )
        graph.add_edge(edge)

    return Map(graph, coord_to_id)


def _position_from_record(value: object) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("Graph map node position must contain exactly 3 coordinates.")
    if not all(isinstance(coord, (int, float)) for coord in value):
        raise ValueError("Graph map node coordinates must be numeric.")
    return (float(value[0]), float(value[1]), float(value[2]))


def _node_type_from_name(name: object) -> NodeType:
    if not isinstance(name, str):
        raise ValueError("Graph map node_type must be a string.")
    try:
        return NodeType[name]
    except KeyError as exc:
        allowed = ", ".join(member.name for member in NodeType)
        raise ValueError(
            f"Graph map node_type must be one of: {allowed}"
        ) from exc


def _required_int(record: dict[str, object], field_name: str) -> int:
    value = record[field_name]
    if not isinstance(value, int):
        raise ValueError(f"Graph map '{field_name}' must be an int.")
    return value


def _required_float(record: dict[str, object], field_name: str) -> float:
    value = record[field_name]
    if not isinstance(value, (int, float)):
        raise ValueError(f"Graph map '{field_name}' must be numeric.")
    return float(value)
