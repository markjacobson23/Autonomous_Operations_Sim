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


@dataclass(frozen=True)
class CorridorReservation:
    """Reserved occupancy window for a bounded one-lane corridor."""

    vehicle_id: int
    node_ids: tuple[int, ...]
    segment_keys: tuple[tuple[int, int], ...]
    start_time_s: float
    end_time_s: float


class ReservationTable:
    """Deterministic reservation store for a narrow multi-vehicle baseline."""

    def __init__(self) -> None:
        self._node_reservations: list[NodeReservation] = []
        self._edge_reservations: list[EdgeReservation] = []
        self._corridor_reservations: list[CorridorReservation] = []

    @property
    def node_reservations(self) -> tuple[NodeReservation, ...]:
        return tuple(self._node_reservations)

    @property
    def edge_reservations(self) -> tuple[EdgeReservation, ...]:
        return tuple(self._edge_reservations)

    @property
    def corridor_reservations(self) -> tuple[CorridorReservation, ...]:
        return tuple(self._corridor_reservations)

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

    def reserve_corridor(
        self,
        *,
        vehicle_id: int,
        node_ids: tuple[int, ...],
        start_time_s: float,
        end_time_s: float,
    ) -> CorridorReservation:
        """Reserve one linear corridor over a half-open interval."""

        if len(node_ids) < 3:
            raise ValueError("corridor reservations require at least three nodes")

        _validate_time_window(start_time_s, end_time_s)
        reservation = CorridorReservation(
            vehicle_id=vehicle_id,
            node_ids=node_ids,
            segment_keys=_segment_keys_for_nodes(node_ids),
            start_time_s=start_time_s,
            end_time_s=end_time_s,
        )
        self._corridor_reservations.append(reservation)
        return reservation

    def earliest_departure_time(
        self,
        *,
        vehicle_id: int,
        current_node_id: int,
        next_node_id: int,
        not_before_s: float,
        travel_time_s: float,
        corridor_node_ids: tuple[int, ...] | None = None,
        corridor_travel_time_s: float | None = None,
    ) -> float:
        """Return the earliest safe departure time under current reservations."""

        if not math.isfinite(not_before_s) or not_before_s < 0.0:
            raise ValueError("not_before_s must be finite and non-negative")
        if not math.isfinite(travel_time_s) or travel_time_s <= 0.0:
            raise ValueError("travel_time_s must be finite and positive")
        if corridor_node_ids is None and corridor_travel_time_s is not None:
            raise ValueError(
                "corridor_travel_time_s requires corridor_node_ids to be provided"
            )
        if corridor_node_ids is not None:
            if len(corridor_node_ids) < 3:
                raise ValueError(
                    "corridor_node_ids must contain at least three nodes when provided"
                )
            if (
                corridor_travel_time_s is None
                or not math.isfinite(corridor_travel_time_s)
                or corridor_travel_time_s <= 0.0
            ):
                raise ValueError(
                    "corridor_travel_time_s must be finite and positive when "
                    "corridor_node_ids are provided"
                )

        candidate = not_before_s
        while True:
            blockers: list[float] = []

            if candidate > not_before_s:
                node_wait_blocker = self._find_node_wait_blocker(
                    vehicle_id=vehicle_id,
                    node_id=current_node_id,
                    start_time_s=not_before_s,
                    end_time_s=candidate,
                )
                if node_wait_blocker is not None:
                    blockers.append(node_wait_blocker.end_time_s)

            arrival_time_s = candidate + travel_time_s
            edge_blocker = self._find_edge_blocker(
                vehicle_id=vehicle_id,
                start_node_id=current_node_id,
                end_node_id=next_node_id,
                start_time_s=candidate,
                end_time_s=arrival_time_s,
            )
            if edge_blocker is not None:
                blockers.append(edge_blocker.end_time_s)

            node_arrival_blocker = self._find_node_arrival_blocker(
                vehicle_id=vehicle_id,
                node_id=next_node_id,
                arrival_time_s=arrival_time_s,
            )
            if node_arrival_blocker is not None:
                blockers.append(node_arrival_blocker.end_time_s)

            if corridor_node_ids is not None and corridor_travel_time_s is not None:
                corridor_blocker = self._find_corridor_blocker(
                    vehicle_id=vehicle_id,
                    node_ids=corridor_node_ids,
                    start_time_s=candidate,
                    end_time_s=candidate + corridor_travel_time_s,
                )
                if corridor_blocker is not None:
                    blockers.append(corridor_blocker.end_time_s)

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
        vehicle_id: int,
        node_id: int,
        start_time_s: float,
        end_time_s: float,
    ) -> NodeReservation | None:
        for reservation in self._node_reservations:
            if reservation.vehicle_id == vehicle_id:
                continue
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
        vehicle_id: int,
        node_id: int,
        arrival_time_s: float,
    ) -> NodeReservation | None:
        for reservation in self._node_reservations:
            if reservation.vehicle_id == vehicle_id:
                continue
            if reservation.node_id != node_id:
                continue
            if reservation.start_time_s <= arrival_time_s < reservation.end_time_s:
                return reservation
        return None

    def _find_edge_blocker(
        self,
        *,
        vehicle_id: int,
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
            if reservation.vehicle_id == vehicle_id:
                continue
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

    def _find_corridor_blocker(
        self,
        *,
        vehicle_id: int,
        node_ids: tuple[int, ...],
        start_time_s: float,
        end_time_s: float,
    ) -> CorridorReservation | None:
        requested_segment_keys = _segment_keys_for_nodes(node_ids)
        requested_segments = set(requested_segment_keys)

        for reservation in self._corridor_reservations:
            if reservation.vehicle_id == vehicle_id:
                continue
            if requested_segments.isdisjoint(reservation.segment_keys):
                continue
            if _windows_overlap(
                start_a=start_time_s,
                end_a=end_time_s,
                start_b=reservation.start_time_s,
                end_b=reservation.end_time_s,
            ):
                return reservation
        return None


def _segment_keys_for_nodes(
    node_ids: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (
            min(start_node_id, end_node_id),
            max(start_node_id, end_node_id),
        )
        for start_node_id, end_node_id in zip(node_ids, node_ids[1:])
    )


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
