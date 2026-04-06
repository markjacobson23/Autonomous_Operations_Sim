from autonomous_ops_sim.core.graph import Graph
import heapq
import math

def dijkstra(graph: Graph, start_id: int, end_id: int) -> tuple[float, list[int]]:

    if not graph.has_node(start_id):
        raise ValueError(f"Node-{start_id} does not exist in graph.")
    if not graph.has_node(end_id):
        raise ValueError(f"Node-{end_id} does not exist in graph.")

    prev = {}
    distance = {start_id: 0.0}
    queue = [(0.0, start_id)]

    while queue:

        cost, node = heapq.heappop(queue)

        if cost > distance.get(node, math.inf):
            continue

        if node == end_id:
            break

        for edge in graph.get_outgoing_edges(node):

            if edge.blocked:
                continue

            neighbor = edge.end_node.id
            new_cost = cost + edge.distance
            if new_cost < distance.get(neighbor, math.inf):
                distance[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(queue, (new_cost, neighbor))

    if end_id not in distance:
        raise ValueError(f'Node-{end_id} is unreachable from Node-{start_id}.')

    path = [end_id]
    step = end_id
    while step != start_id:
        step = prev[step]
        path.append(step)
    path.reverse()

    return distance[end_id], path