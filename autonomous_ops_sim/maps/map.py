from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import NodeType, Node
from autonomous_ops_sim.core.edge import Edge
class Map:
    """Spatial facade over graph.

    Provides coordinate-based access on top of the underlying graph,
    including lookups by position, region queries, node_type filtering, and
    static edge queries needed by routing and simulation code.
    """

    def __init__(
            self,
            graph: Graph,
            coord_to_id: dict[tuple[float, float, float], int],
            render_geometry: dict[str, object] | None = None,
    ):
        self._graph = graph
        self.coord_to_id = coord_to_id
        self._render_geometry = render_geometry or {}

    @property
    def graph(self) -> Graph:
        """Return the immutable graph backing this map."""

        return self._graph

    @property
    def render_geometry(self) -> dict[str, object]:
        """Return optional rendered-geometry metadata layered on the routing graph."""

        return self._render_geometry

    def has_coordinate(self, position: tuple[float, float, float]) -> bool:
        """Return True if the given coordinate exists in the map."""

        return position in self.coord_to_id

    def get_node_id(self, position: tuple[float, float, float]) -> int:
        """Return the node ID for a coordinate."""

        if not self.has_coordinate(position):
            raise KeyError(f"There is no node with Position-{position}")
        return self.coord_to_id[position]

    def get_position(self, node_id: int) -> tuple[float, float, float]:
        """Return the coordinate position for a given node ID."""

        if not self._graph.has_node(node_id):
            raise KeyError(f"There is no Node-{node_id}")
        return self._graph.nodes[node_id].position

    def get_nodes_by_type(self, node_type: NodeType) -> list[int]:
        """Return all node IDs that have the given NodeType."""

        return [
            node_id
            for node_id, node in self._graph.nodes.items()
            if node.node_type == node_type
        ]

    def get_node_type(self, node_id: int) -> NodeType:
        """Return the NodeType for a given node ID."""

        if not self._graph.has_node(node_id):
           raise KeyError(f"There is no Node-{node_id}")
        return self._graph.nodes[node_id].node_type

    def get_nodes_in_region(
            self,
            min_x: float,
            min_y: float,
            min_z: float,
            max_x: float,
            max_y: float,
            max_z: float,
    ) -> list[int]:
        """Return all node IDs inside the bounding box."""

        if max_x < min_x:
            raise ValueError(f"max_x = {max_x} < {min_x} = min_x")
        if max_y < min_y:
            raise ValueError(f"max_y = {max_y} < {min_y} = min_y")
        if max_z < min_z:
            raise ValueError(f"max_z = {max_z} < {min_z} = min_z")
        return [
            node_id
            for node_id, node in self._graph.nodes.items()
            if min_x <= node.position[0] <= max_x
            and min_y <= node.position[1] <= max_y
            and min_z <= node.position[2] <= max_z
        ]

    def get_node(self, node_id: int) -> Node:
        """Return Node object from node ID"""

        if not self._graph.has_node(node_id):
            raise KeyError(f"There is no Node-{node_id}")
        return self._graph.nodes[node_id]

    def get_all_node_ids(self) -> list[int]:
        """Return every node ID in the map."""

        return list(self._graph.nodes.keys())

    def get_nearest_node_of_type(
            self, position: tuple[float, float, float], node_type: NodeType
    ) -> int:
        """Return the closest node ID of the given type (Euclidean)."""

        candidates = self.get_nodes_by_type(node_type)
        if not candidates:
            raise ValueError(f"There are no nodes of type {node_type}")
        x, y, z = position
        return min(
            candidates,
            key= lambda nid:(
                (self.get_position(nid)[0] - x) ** 2 +
                (self.get_position(nid)[1] - y) ** 2 +
                (self.get_position(nid)[2] - z) ** 2
            )
        )

    def get_outgoing_edges(self, node_id: int) -> list[Edge]:
        """Return a copy of all outgoing edges from the node."""

        return self._graph.get_outgoing_edges(node_id)

    def get_neighbors(self, node_id: int) -> list[int]:
        """Return the node IDs of all direct outgoing neighbors."""

        return self._graph.get_neighbors(node_id)

    def get_edge_between(self, start_id: int, end_id: int) -> Edge | None:
        """Return the edge from start to end, or None if none exists."""

        for edge in self.get_outgoing_edges(start_id):
            if edge.end_node.id == end_id:
                return edge
        return None

    def get_edges_from_position(self, position: tuple[float, float, float]) -> list[Edge]:
        """Return all outgoing edges from the node at the given position."""

        nid = self.get_node_id(position)
        return self.get_outgoing_edges(nid)

    def validate_path(self, path: list[int]) -> bool:
        """Return True if every node exists and every consecutive pair has an edge."""

        if not path:
            return True
        for start, end in zip(path, path[1:]):
            if not self._graph.has_node(start) or not self._graph.has_node(end):
                return False
            if self.get_edge_between(start, end) is None:
                return False
        return True

    def __repr__(self):
        return f"Map(graph={self._graph!r}, coord_to_id={self.coord_to_id!r})"
