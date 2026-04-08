from dataclasses import dataclass
from enum import Enum
import math


class TraceEventType(str, Enum):
    """Stable event kinds emitted during simulated execution."""

    ROUTE_START = "route_start"
    EDGE_ENTER = "edge_enter"
    NODE_ARRIVAL = "node_arrival"
    ROUTE_COMPLETE = "route_complete"


@dataclass(frozen=True)
class TraceEvent:
    """Immutable execution event captured in deterministic order."""

    sequence: int
    timestamp_s: float
    vehicle_id: int
    event_type: TraceEventType
    node_id: int | None = None
    edge_id: int | None = None
    start_node_id: int | None = None
    end_node_id: int | None = None


class Trace:
    """Append-only deterministic execution trace."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._next_sequence = 0

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        """Return all recorded events in emission order."""

        return tuple(self._events)

    def emit(
        self,
        *,
        timestamp_s: float,
        vehicle_id: int,
        event_type: TraceEventType,
        node_id: int | None = None,
        edge_id: int | None = None,
        start_node_id: int | None = None,
        end_node_id: int | None = None,
    ) -> TraceEvent:
        """Append and return a trace event."""

        if not math.isfinite(timestamp_s):
            raise ValueError("timestamp_s must be finite")

        event = TraceEvent(
            sequence=self._next_sequence,
            timestamp_s=timestamp_s,
            vehicle_id=vehicle_id,
            event_type=event_type,
            node_id=node_id,
            edge_id=edge_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
        )
        self._events.append(event)
        self._next_sequence += 1
        return event
