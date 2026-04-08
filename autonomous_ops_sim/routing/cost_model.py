from typing import Protocol

from autonomous_ops_sim.core.edge import Edge


class CostModel(Protocol):
    """Provide a non-negative traversal cost for an edge."""

    def edge_cost(self, edge: Edge) -> float:
        """Return the traversal cost for the given edge."""


class DistanceCostModel:
    """Route by raw edge distance."""

    def edge_cost(self, edge: Edge) -> float:
        return edge.distance


class TimeCostModel:
    """Route by travel time derived from distance and speed limit."""

    def edge_cost(self, edge: Edge) -> float:
        if edge.speed_limit <= 0.0:
            raise ValueError(
                f"Edge-{edge.id} has non-positive speed_limit={edge.speed_limit}. "
                "Time-based routing requires a positive speed limit."
            )
        return edge.distance / edge.speed_limit


def get_validated_edge_cost(cost_model: CostModel, edge: Edge) -> float:
    """Return an edge cost validated for Dijkstra-based routing."""

    cost = cost_model.edge_cost(edge)
    if cost < 0.0:
        raise ValueError(
            f"Edge-{edge.id} produced negative cost {cost}. "
            "Dijkstra-based routing requires non-negative edge costs."
        )
    return cost
