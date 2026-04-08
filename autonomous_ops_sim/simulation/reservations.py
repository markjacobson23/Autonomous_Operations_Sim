from dataclasses import dataclass
import math


@dataclass(frozen=True)
class VehicleRouteRequest:
    """Stable input for one coordinated route execution."""

    vehicle_id: int
    start_node_id: int
    destination_node_id: int
    max_speed: float
    priority: int | None = None

    @property
    def effective_priority(self) -> tuple[int, int]:
        """Return the deterministic sort key used for conflict handling."""

        priority = self.vehicle_id if self.priority is None else self.priority
        return priority, self.vehicle_id


@dataclass(frozen=True)
class ConflictWait:
    """Wait inserted to avoid a reserved conflict area."""

    node_id: int
    start_time_s: float
    end_time_s: float

    @property
    def duration_s(self) -> float:
        return self.end_time_s - self.start_time_s


@dataclass(frozen=True)
class NodeReservation:
    """Reserved occupancy window for one node."""

    vehicle_id: int
    node_id: int
    start_time_s: float
    end_time_s: float
    reason: str


@dataclass(frozen=True)
class EdgeReservation:
    """Reserved traversal window for one graph edge segment."""

    vehicle_id: int
    edge_id: int
    start_node_id: int
    end_node_id: int
    start_time_s: float
    end_time_s: float

    @property
    def segment_key(self) -> tuple[int, int]:
        return (
            min(self.start_node_id, self.end_node_id),
            max(self.start_node_id, self.end_node_id),
        )


class ReservationTable:
    """Deterministic reservation store for a narrow multi-vehicle baseline."""

    def __init__(self) -> None:
        self._node_reservations: list[NodeReservation] = []
        self._edge_reservations: list[EdgeReservation] = []

    @property
    def node_reservations(self) -> tuple[NodeReservation, ...]:
        return tuple(self._node_reservations)

    @property
    def edge_reservations(self) -> tuple[EdgeReservation, ...]:
        return tuple(self._edge_reservations)

    def reserve_node(
        self,
        *,
        vehicle_id: int,
        node_id: int,
        start_time_s: float,
        end_time_s: float,
        reason: str,
    ) -> NodeReservation:
        """Reserve one node over a half-open interval."""

        _validate_time_window(start_time_s, end_time_s)
        reservation = NodeReservation(
            vehicle_id=vehicle_id,
            node_id=node_id,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            reason=reason,
        )
        self._node_reservations.append(reservation)
        return reservation

    def reserve_edge(
        self,
        *,
        vehicle_id: int,
        edge_id: int,
        start_node_id: int,
        end_node_id: int,
        start_time_s: float,
        end_time_s: float,
    ) -> EdgeReservation:
        """Reserve one traversed edge over a half-open interval."""

        _validate_time_window(start_time_s, end_time_s)
        reservation = EdgeReservation(
            vehicle_id=vehicle_id,
            edge_id=edge_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
        )
        self._edge_reservations.append(reservation)
        return reservation

    def earliest_departure_time(
        self,
        *,
        current_node_id: int,
        next_node_id: int,
        not_before_s: float,
        travel_time_s: float,
    ) -> float:
        """Return the earliest safe departure time under current reservations."""

        if not math.isfinite(not_before_s) or not_before_s < 0.0:
            raise ValueError("not_before_s must be finite and non-negative")
        if not math.isfinite(travel_time_s) or travel_time_s <= 0.0:
            raise ValueError("travel_time_s must be finite and positive")

        candidate = not_before_s
        while True:
            blockers: list[float] = []

            if candidate > not_before_s:
                node_wait_blocker = self._find_node_wait_blocker(
                    node_id=current_node_id,
                    start_time_s=not_before_s,
                    end_time_s=candidate,
                )
                if node_wait_blocker is not None:
                    blockers.append(node_wait_blocker.end_time_s)

            arrival_time_s = candidate + travel_time_s
            edge_blocker = self._find_edge_blocker(
                start_node_id=current_node_id,
                end_node_id=next_node_id,
                start_time_s=candidate,
                end_time_s=arrival_time_s,
            )
            if edge_blocker is not None:
                blockers.append(edge_blocker.end_time_s)

            node_arrival_blocker = self._find_node_arrival_blocker(
                node_id=next_node_id,
                arrival_time_s=arrival_time_s,
            )
            if node_arrival_blocker is not None:
                blockers.append(node_arrival_blocker.end_time_s)

            if not blockers:
                return candidate

            candidate = max(blockers)
            if not math.isfinite(candidate):
                raise RuntimeError(
                    "No finite conflict-free departure time is available for the "
                    f"segment {current_node_id}->{next_node_id}."
                )

    def _find_node_wait_blocker(
        self,
        *,
        node_id: int,
        start_time_s: float,
        end_time_s: float,
    ) -> NodeReservation | None:
        for reservation in self._node_reservations:
            if reservation.node_id != node_id:
                continue
            if _windows_overlap(
                start_a=start_time_s,
                end_a=end_time_s,
                start_b=reservation.start_time_s,
                end_b=reservation.end_time_s,
            ):
                return reservation
        return None

    def _find_node_arrival_blocker(
        self,
        *,
        node_id: int,
        arrival_time_s: float,
    ) -> NodeReservation | None:
        for reservation in self._node_reservations:
            if reservation.node_id != node_id:
                continue
            if reservation.start_time_s <= arrival_time_s < reservation.end_time_s:
                return reservation
        return None

    def _find_edge_blocker(
        self,
        *,
        start_node_id: int,
        end_node_id: int,
        start_time_s: float,
        end_time_s: float,
    ) -> EdgeReservation | None:
        requested_segment = (
            min(start_node_id, end_node_id),
            max(start_node_id, end_node_id),
        )
        for reservation in self._edge_reservations:
            if reservation.segment_key != requested_segment:
                continue
            if _windows_overlap(
                start_a=start_time_s,
                end_a=end_time_s,
                start_b=reservation.start_time_s,
                end_b=reservation.end_time_s,
            ):
                return reservation
        return None


def _validate_time_window(start_time_s: float, end_time_s: float) -> None:
    if not math.isfinite(start_time_s) or start_time_s < 0.0:
        raise ValueError("start_time_s must be finite and non-negative")
    if math.isnan(end_time_s):
        raise ValueError("end_time_s must not be NaN")
    if end_time_s <= start_time_s:
        raise ValueError("end_time_s must be greater than start_time_s")


def _windows_overlap(
    *,
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
) -> bool:
    return start_a < end_b and start_b < end_a
