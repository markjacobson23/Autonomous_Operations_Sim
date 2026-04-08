from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.simulation.trace import TraceEventType

if TYPE_CHECKING:
    from autonomous_ops_sim.simulation.engine import SimulationEngine


@dataclass
class VehicleProcess:
    """Single-vehicle route execution over simulated time."""

    vehicle_id: int
    current_node_id: int
    max_speed: float

    def execute_route(
        self,
        *,
        destination_node_id: int,
        engine: "SimulationEngine",
    ) -> tuple[int, ...]:
        """Route to the destination and emit deterministic execution events."""

        if not math.isfinite(self.max_speed) or self.max_speed <= 0.0:
            raise ValueError("max_speed must be finite and positive")

        _, path = engine.router.route(
            engine.map.graph,
            self.current_node_id,
            destination_node_id,
            world_state=engine.world_state,
        )
        route = tuple(path)

        engine.trace.emit(
            timestamp_s=engine.simulated_time_s,
            vehicle_id=self.vehicle_id,
            event_type=TraceEventType.ROUTE_START,
            node_id=self.current_node_id,
            start_node_id=self.current_node_id,
            end_node_id=destination_node_id,
        )

        for start_node_id, end_node_id in zip(route, route[1:]):
            edge = engine.map.get_edge_between(start_node_id, end_node_id)
            if edge is None:
                raise RuntimeError(
                    "Router returned a path containing a missing map edge: "
                    f"{start_node_id} -> {end_node_id}."
                )

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.EDGE_ENTER,
                edge_id=edge.id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
            )

            engine.run(engine.simulated_time_s + _edge_travel_time_s(edge, self.max_speed))
            self.current_node_id = end_node_id

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.NODE_ARRIVAL,
                node_id=end_node_id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
            )

        engine.trace.emit(
            timestamp_s=engine.simulated_time_s,
            vehicle_id=self.vehicle_id,
            event_type=TraceEventType.ROUTE_COMPLETE,
            node_id=self.current_node_id,
            start_node_id=route[0],
            end_node_id=destination_node_id,
        )

        return route


def _edge_travel_time_s(edge: Edge, max_speed: float) -> float:
    """Return traversal time using both the vehicle and edge constraints."""

    effective_speed = min(max_speed, edge.speed_limit)
    if effective_speed <= 0.0:
        raise ValueError(
            f"Edge-{edge.id} cannot be traversed with effective_speed={effective_speed}."
        )
    return edge.distance / effective_speed
