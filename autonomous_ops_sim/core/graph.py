from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.core.edge import Edge

class Graph:
    """Directed graph storing nodes, edges, and edge adjacency.

    This class is the topological container for routing and simulation.
    It owns the node/edge registries and maintains adjacency
    lists for traversal from a node to its outgoing neighbors.
    """

    def __init__(self):

        # Maps node_id to Node object.
        self.nodes: dict[int, Node] = {}

        # Maps edge_id to Edge object.
        self.edges: dict[int, Edge] = {}

        # Maps node_id to list of outgoing edges.
        self.adjacency: dict[int, list[Edge]] = {}

    def add_node(self, node: Node):
        """Add a node to the graph and initialize its adjacency list."""

        if node.id in self.nodes:
            raise ValueError(f"Node-{node.id} already exists in graph.")

        self.nodes[node.id] = node
        self.adjacency[node.id] = []

    def add_edge(self, edge: Edge):
        """Add an edge to the graph and update its adjacency list.

        Enforces that:
        -The edge's start and end nodes already exist in the graph.
        -The edge's start and end nodes are not connected by another edge.
        """


        if edge.id in self.edges:
            raise ValueError(f"Edge-{edge.id} already exists in graph.")

        if edge.start_node.id not in self.nodes:
            raise ValueError(f"Node-{edge.start_node.id} of Edge-{edge.id} must already exist in graph.")

        if edge.end_node.id not in self.nodes:
            raise ValueError(f"Node-{edge.end_node.id} of Edge-{edge.id} must already exist in graph.")

        if edge.start_node.id == edge.end_node.id:
            raise ValueError("An edge cannot connect a node to itself.")

        # Check if the edge already exists in the graph
        if any(edge.end_node.id == existing_edge.end_node.id for existing_edge in self.adjacency[edge.start_node.id]):
            raise ValueError("An edge already exists in the graph with these start and end nodes.")

        self.edges[edge.id] = edge
        self.adjacency[edge.start_node.id].append(edge)

    def has_node(self, node_id: int) -> bool:
        """Check if a node with the given ID exists in the graph."""
        
        return node_id in self.nodes

    def has_edge(self, edge_id: int) -> bool:
        """Check if an edge with the given ID exists in the graph."""

        return edge_id in self.edges

    def get_neighbors(self, node_id: int) -> list[int]:
        """Return a list of node IDs that are directly connected to the given node."""

        if node_id not in self.nodes:
            raise KeyError(f"Node-{node_id} is not in the graph.")

        return [edge.end_node.id for edge in self.adjacency[node_id]]

    def get_outgoing_edges(self, node_id: int) -> list[Edge]:
        """Return a copy of the list of outgoing edges from the given node."""

        if node_id not in self.nodes:
            raise KeyError(f"Node-{node_id} is not in the graph.")

        return self.adjacency[node_id].copy()

