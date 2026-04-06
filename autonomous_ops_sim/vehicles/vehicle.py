from enum import Enum, auto

class VehicleType(Enum):
    GENERIC = auto()



class Vehicle:
    def __init__(
        self,
        id: int,
        position: tuple[float, float, float],
        velocity: float,
        payload: float,
        max_payload: float,
        max_speed: float,
        vehicle_type : VehicleType = VehicleType.GENERIC
    ):
        self.id = id
        self.position = position
        self.velocity = velocity
        self.payload = payload
        self.max_payload = max_payload
        self.max_speed = max_speed
        self.vehicle_type = vehicle_type

    def get_position(self) -> tuple[float, float, float]:
        return self.position

    def get_velocity(self) -> float:
        return self.velocity

    def get_payload(self) -> float:
        return self.payload

    def get_cost_context(self):
        ...

    def update_position(self, new_position: tuple[float, float, float]):
        ...

    def set_payload(self, new_payload: float):
        ...

    def set_velocity(self, new_velocity: float):
        ...