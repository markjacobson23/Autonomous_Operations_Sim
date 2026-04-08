import math
import random

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing.router import Router
from autonomous_ops_sim.simulation.trace import Trace
from autonomous_ops_sim.simulation.vehicle_process import VehicleProcess
from autonomous_ops_sim.simulation.world_state import WorldState


class SimulationEngine:
    """Own deterministic state and simulated time for a single run."""

    def __init__(
        self,
        simulation_map: Map,
        world_state: WorldState,
        router: Router,
        seed: int,
    ):
        self._map = simulation_map
        self._world_state = world_state
        self._router = router
        self._seed = seed
        self._rng = random.Random(seed)
        self._simulated_time_s = 0.0
        self._trace = Trace()

    @property
    def map(self) -> Map:
        """Return the static map used for this run."""

        return self._map

    @property
    def world_state(self) -> WorldState:
        """Return the runtime world state used for this run."""

        return self._world_state

    @property
    def router(self) -> Router:
        """Return the router used for this run."""

        return self._router

    @property
    def seed(self) -> int:
        """Return the engine-owned deterministic seed."""

        return self._seed

    @property
    def trace(self) -> Trace:
        """Return the execution trace for this run."""

        return self._trace

    @property
    def rng(self) -> random.Random:
        """Return the engine-owned deterministic random stream."""

        return self._rng

    @property
    def simulated_time_s(self) -> float:
        """Return the current simulated time."""

        return self._simulated_time_s

    def run(self, until_s: float) -> float:
        """Advance the engine's simulated time to the requested point."""

        if not math.isfinite(until_s):
            raise ValueError("until_s must be finite")
        if until_s < 0.0:
            raise ValueError("until_s must be non-negative")
        if until_s < self._simulated_time_s:
            raise ValueError(
                "until_s must be greater than or equal to current simulated time"
            )

        self._simulated_time_s = until_s
        return self._simulated_time_s

    def execute_vehicle_route(
        self,
        *,
        vehicle_id: int,
        start_node_id: int,
        destination_node_id: int,
        max_speed: float,
    ) -> tuple[int, ...]:
        """Execute one vehicle over one routed path."""

        process = VehicleProcess(
            vehicle_id=vehicle_id,
            current_node_id=start_node_id,
            max_speed=max_speed,
        )
        return process.execute_route(
            destination_node_id=destination_node_id,
            engine=self,
        )
