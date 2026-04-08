from dataclasses import dataclass

@dataclass(frozen=True)
class CostContext:

    vehicle_id: int
    current_payload: float = 0.0
    current_velocity: float = 0.0
    time_of_day_seconds: float = 0.0
    weather_factor: float = 1.0
    active_work_zone_ids: tuple[int, ...] = ()
    is_return_trip: bool = False