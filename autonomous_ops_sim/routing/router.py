from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.routing.cost_model import CostModel, DistanceCostModel
from autonomous_ops_sim.routing.pathfinding import dijkstra
from autonomous_ops_sim.simulation.world_state import WorldState


class Router:
    """Public routing surface for shortest-path queries."""

    def __init__(self, cost_model: CostModel | None = None):
        self._cost_model = cost_model or DistanceCostModel()

    def route(
        self,
        graph: Graph,
        start_id: int,
        end_id: int,
        world_state: WorldState | None = None,
    ) -> tuple[float, list[int]]:
        return dijkstra(
            graph,
            start_id,
            end_id,
            world_state=world_state,
            cost_model=self._cost_model,
        )
