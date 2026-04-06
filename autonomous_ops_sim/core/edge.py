from autonomous_ops_sim.core.node import Node
class Edge:
    def __init__(self, id: int, start_node: Node, end_node: Node, distance: float, speed_limit: float, blocked: bool = False):
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.distance = distance
        self.speed_limit = speed_limit
        self.blocked = blocked
    def __repr__(self):
        return f"Edge(id={self.id!r}, start_node={self.start_node!r}, end_node={self.end_node!r}, distance={self.distance!r}, speed_limit={self.speed_limit!r}, blocked={self.blocked!r})"

