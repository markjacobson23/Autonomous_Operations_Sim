from dataclasses import dataclass
import heapq
import math


@dataclass(frozen=True)
class ResourceReservation:
    """Resolved waiting and service window for one resource use."""

    start_time_s: float
    end_time_s: float
    wait_duration_s: float


class SharedResource:
    """Small deterministic shared resource with fixed concurrent capacity."""

    def __init__(
        self,
        resource_id: str,
        *,
        capacity: int = 1,
        initial_available_times_s: tuple[float, ...] | None = None,
    ) -> None:
        if not resource_id:
            raise ValueError("resource_id must be non-empty")
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        if initial_available_times_s is None:
            initial_available_times_s = (0.0,) * capacity
        elif len(initial_available_times_s) != capacity:
            raise ValueError("initial_available_times_s must match capacity")

        heap: list[tuple[float, int]] = []
        for slot_index, available_at_s in enumerate(initial_available_times_s):
            if not math.isfinite(available_at_s) or available_at_s < 0.0:
                raise ValueError(
                    "initial_available_times_s values must be finite and non-negative"
                )
            heap.append((available_at_s, slot_index))

        self._resource_id = resource_id
        self._capacity = capacity
        self._availability_heap = heap
        heapq.heapify(self._availability_heap)

    @property
    def resource_id(self) -> str:
        return self._resource_id

    @property
    def capacity(self) -> int:
        return self._capacity

    def reserve(self, *, requested_at_s: float, duration_s: float) -> ResourceReservation:
        """Reserve the next available capacity slot for the requested duration."""

        if not math.isfinite(requested_at_s) or requested_at_s < 0.0:
            raise ValueError("requested_at_s must be finite and non-negative")
        if not math.isfinite(duration_s) or duration_s < 0.0:
            raise ValueError("duration_s must be finite and non-negative")

        available_at_s, slot_index = heapq.heappop(self._availability_heap)
        start_time_s = max(requested_at_s, available_at_s)
        end_time_s = start_time_s + duration_s
        heapq.heappush(self._availability_heap, (end_time_s, slot_index))
        return ResourceReservation(
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            wait_duration_s=start_time_s - requested_at_s,
        )
