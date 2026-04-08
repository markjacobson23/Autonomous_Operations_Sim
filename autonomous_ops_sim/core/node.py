from enum import Enum, auto

class NodeType(Enum):
    """ A node's role in the map/simulation.

    These values type how a node should be interpreted by
    systems such as routing, task planning, and environment logic.
    """

    WAYPOINT = auto()
    INTERSECTION = auto()
    DEPOT = auto()
    JOB_SITE = auto()
    LOADING_ZONE = auto()
    UNLOADING_ZONE = auto()
    CHARGING_STATION = auto()

    def __repr__(self):
        return f"<{self.name}>"

class Node:
    """Graph node with an identifier, 3D position, and type."""

    def __init__(
            self,
            id: int,
            position: tuple[float, float, float],
            node_type: NodeType = NodeType.INTERSECTION,
    ):
        # Expected to be unique within a graph.
        self.id = id
        # Position as (x, y, z).
        self.position = position
        # Default to INTERSECTION because most nodes are ordinary crossings.
        self.node_type = node_type

    def __repr__(self):
        return f"Node(id={self.id!r}, position={self.position!r}, node_type={self.node_type!r})"

