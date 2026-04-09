from autonomous_ops_sim.core.graph import Graph


class WorldState:
    """Runtime simulation state layered on top of an immutable graph/map."""

    def __init__(self, graph: Graph):
        self._graph = graph
        self._blocked_edge_ids: set[int] = set()

    @property
    def blocked_edge_ids(self) -> set[int]:
        """Return a copy of all currently blocked edge IDs."""

        return self._blocked_edge_ids.copy()

    def is_edge_blocked(self, edge_id: int) -> bool:
        """Return True if the given edge is blocked in this world state."""

        self._ensure_edge_exists(edge_id)
        return edge_id in self._blocked_edge_ids

    def has_blocked_edge(self, edge_id: int) -> bool:
        """Return blocked-edge membership for known graph edge ids without validation."""

        return edge_id in self._blocked_edge_ids

    def block_edge(self, edge_id: int) -> None:
        """Block an edge for routing in this world state."""

        self._ensure_edge_exists(edge_id)
        self._blocked_edge_ids.add(edge_id)

    def unblock_edge(self, edge_id: int) -> None:
        """Remove an edge block in this world state."""

        self._ensure_edge_exists(edge_id)
        self._blocked_edge_ids.discard(edge_id)

    def reset(self) -> None:
        """Reset all runtime blocked-edge state for a fresh run."""

        self._blocked_edge_ids.clear()

    def _ensure_edge_exists(self, edge_id: int) -> None:
        if not self._graph.has_edge(edge_id):
            raise KeyError(f"There is no Edge-{edge_id}")
