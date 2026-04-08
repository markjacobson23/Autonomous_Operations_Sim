from autonomous_ops_sim.core.node import Node
class Edge:
    """Directed connection between two nodes in the graph.

    Systems such as routing and simulation use edges to model
    traversable paths, along with constraints like travel distance, speed,
    and availability.
    """
    def __init__(
            self,
            id: int,
            start_node: Node,
            end_node: Node,
            distance: float,
            speed_limit: float,

    ):  # Expected to be unique within a graph.
        self.id = id

        # Directed edge, travel is defined from start_node to end_node.
        self.start_node = start_node
        self.end_node = end_node

        # Travel length for this segment.
        # Keep units consistent across a graph (ex: meters).
        self.distance = distance

        # Maximum allowed traversal speed for this segment.
        # Keep units consistent across a graph (ex: meters/second).
        self.speed_limit = speed_limit

    def __repr__(self):
        return (
            f"Edge(id={self.id!r}, start_node={self.start_node!r}, "
            f"end_node={self.end_node!r}, distance={self.distance!r}, "
            f"speed_limit={self.speed_limit!r})"
        )
