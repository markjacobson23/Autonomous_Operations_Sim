from autonomous_ops_sim.native import get_native_reservation_departure_accelerator
from autonomous_ops_sim.simulation.reservations import ReservationTable, VehicleRouteRequest


def build_reservation_table(*, use_native_acceleration: bool) -> ReservationTable:
    table = ReservationTable(use_native_acceleration=use_native_acceleration)
    for offset in range(40):
        table.reserve_node(
            vehicle_id=100 + offset,
            node_id=2,
            start_time_s=float(offset),
            end_time_s=float(offset) + 1.0,
            reason="benchmark_hold",
        )
        table.reserve_edge(
            vehicle_id=200 + offset,
            edge_id=500 + offset,
            start_node_id=2,
            end_node_id=3,
            start_time_s=float(offset),
            end_time_s=float(offset) + 0.75,
        )
        table.reserve_corridor(
            vehicle_id=300 + offset,
            node_ids=(1, 2, 3, 4),
            start_time_s=float(offset),
            end_time_s=float(offset) + 1.5,
        )
    return table


def test_native_reservation_accelerator_matches_python_departure_results() -> None:
    python_table = build_reservation_table(use_native_acceleration=False)
    native_table = build_reservation_table(use_native_acceleration=True)

    requests = tuple(
        VehicleRouteRequest(
            vehicle_id=10 + index,
            start_node_id=1,
            destination_node_id=4,
            max_speed=1.0,
            priority=index,
        )
        for index in range(6)
    )

    python_departures = [
        python_table.earliest_departure_time(
            vehicle_id=request.vehicle_id,
            current_node_id=request.start_node_id,
            next_node_id=2,
            not_before_s=float(index),
            travel_time_s=1.0,
            corridor_node_ids=(1, 2, 3, 4),
            corridor_travel_time_s=3.0,
        )
        for index, request in enumerate(requests)
    ]
    native_departures = [
        native_table.earliest_departure_time(
            vehicle_id=request.vehicle_id,
            current_node_id=request.start_node_id,
            next_node_id=2,
            not_before_s=float(index),
            travel_time_s=1.0,
            corridor_node_ids=(1, 2, 3, 4),
            corridor_travel_time_s=3.0,
        )
        for index, request in enumerate(requests)
    ]

    assert native_departures == python_departures
    assert native_table.departure_acceleration_mode in {"native", "python"}


def test_native_reservation_accelerator_loader_is_stable() -> None:
    accelerator_a = get_native_reservation_departure_accelerator()
    accelerator_b = get_native_reservation_departure_accelerator()

    assert accelerator_a is accelerator_b
