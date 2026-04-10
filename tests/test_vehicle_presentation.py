from autonomous_ops_sim.vehicles.presentation import (
    build_vehicle_presentation_surface,
    presentation_profile_for_vehicle_type,
)
from autonomous_ops_sim.vehicles.vehicle import VehicleType


def test_vehicle_presentation_profiles_are_distinct() -> None:
    haul = presentation_profile_for_vehicle_type(VehicleType.HAUL_TRUCK)
    forklift = presentation_profile_for_vehicle_type(VehicleType.FORKLIFT)
    car = presentation_profile_for_vehicle_type(VehicleType.CAR)
    generic = presentation_profile_for_vehicle_type(VehicleType.GENERIC)

    assert haul.presentation_key == "haul_truck"
    assert forklift.presentation_key == "forklift"
    assert car.presentation_key == "car"
    assert generic.presentation_key == "generic"
    assert haul.display_name == "Haul Truck"
    assert forklift.role_label == "Yard handling"
    assert car.primary_color != generic.primary_color


def test_vehicle_presentation_surface_binds_vehicle_id() -> None:
    surface = build_vehicle_presentation_surface(
        vehicle_id=17,
        vehicle_type=VehicleType.CAR,
    )

    assert surface.vehicle_id == 17
    assert surface.vehicle_type == "CAR"
    assert surface.display_name == "Car"
