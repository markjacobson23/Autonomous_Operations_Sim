import heapq
import math

from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.routing.cost_model import (
    CostModel,
    DistanceCostModel,
    get_validated_edge_cost,
)
from autonomous_ops_sim.simulation.world_state import WorldState


def dijkstra(
    graph: Graph,
    start_id: int,
    end_id: int,
    world_state: WorldState | None = None,
    cost_model: CostModel | None = None,
) -> tuple[float, list[int]]:
    if not graph.has_node(start_id):
        raise ValueError(f"Node-{start_id} does not exist in graph.")
    if not graph.has_node(end_id):
        raise ValueError(f"Node-{end_id} does not exist in graph.")

    runtime_state = world_state or WorldState(graph)
    active_cost_model = cost_model or DistanceCostModel()

    prev: dict[int, int] = {}
    distance: dict[int, float] = {start_id: 0.0}
    queue: list[tuple[float, int]] = [(0.0, start_id)]

    while queue:
        cost, node = heapq.heappop(queue)

        if cost > distance.get(node, math.inf):
            continue

        if node == end_id:
            break

        for edge in graph.iter_outgoing_edges(node):
            if runtime_state.has_blocked_edge(edge.id):
                continue

            neighbor = edge.end_node.id
            edge_cost = get_validated_edge_cost(active_cost_model, edge)
            new_cost = cost + edge_cost
            if new_cost < distance.get(neighbor, math.inf):
                distance[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(queue, (new_cost, neighbor))

    if end_id not in distance:
        raise ValueError(f"Node-{end_id} is unreachable from Node-{start_id}.")

    path = [end_id]
    step = end_id
    while step != start_id:
        step = prev[step]
        path.append(step)
    path.reverse()

    return distance[end_id], path
