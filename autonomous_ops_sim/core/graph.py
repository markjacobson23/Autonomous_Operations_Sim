from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.core.edge import Edge

class Graph:

    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.edges: dict[int, Edge] = {}
        self.adjacency: dict[int, list[Edge]] = {}

    def add_node(self, node: Node):

        if node.id in self.nodes:
            raise ValueError(f"Node-{node.id} already exists in graph.")

        self.nodes[node.id] = node
        self.adjacency[node.id] = []

    def add_edge(self, edge: Edge):

        if edge.id in self.edges:
            raise ValueError(f"Edge-{edge.id} already exists in graph.")

        if edge.start_node.id not in self.nodes:
            raise ValueError(f"Node-{edge.start_node.id} of Edge-{edge.id} must already exist in graph.")

        if edge.end_node.id not in self.nodes:
            raise ValueError(f"Node-{edge.end_node.id} of Edge-{edge.id} must already exist in graph.")

        if any(edge.end_node.id == existing_edge.end_node.id for existing_edge in self.adjacency[edge.start_node.id]):
            raise ValueError("An edge already exists in the graph with these start and end nodes.")

        self.edges[edge.id] = edge
        self.adjacency[edge.start_node.id].append(edge)

    def has_node(self, node_id: int) -> bool:
        return node_id in self.nodes

    def has_edge(self, edge_id: int) -> bool:
        return edge_id in self.edges

    def get_neighbors(self, node_id: int) -> list[int]:

        if node_id not in self.nodes:
            raise KeyError(f"Node-{node_id} is not in the graph.")

        return [edge.end_node.id for edge in self.adjacency[node_id]]

    def get_outgoing_edges(self, node_id: int) -> list[Edge]:
        if node_id not in self.nodes:
            raise KeyError(f"Node-{node_id} is not in the graph.")
        return self.adjacency[node_id].copy()

