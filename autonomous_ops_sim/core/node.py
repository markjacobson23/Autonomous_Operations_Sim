from enum import Enum, auto

class NodeType(Enum):
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
    def __init__(self, id: int, position: tuple[float, float, float], node_type: NodeType = NodeType.INTERSECTION):
        self.id = id
        self.position = position
        self.node_type = node_type

    def __repr__(self):
        return f"Node(id={self.id!r}, position={self.position!r}, node_type={self.node_type!r})"

