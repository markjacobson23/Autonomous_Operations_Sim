from __future__ import annotations

from dataclasses import dataclass

from autonomous_ops_sim.vehicles.vehicle import VehicleType


@dataclass(frozen=True)
class VehiclePresentationProfile:
    presentation_key: str
    display_name: str
    role_label: str
    body_length_m: float
    body_width_m: float
    primary_color: str
    accent_color: str


@dataclass(frozen=True)
class VehiclePresentationSurface:
    vehicle_id: int
    vehicle_type: str
    presentation_key: str
    display_name: str
    role_label: str
    body_length_m: float
    body_width_m: float
    primary_color: str
    accent_color: str


def presentation_profile_for_vehicle_type(
    vehicle_type: VehicleType | None,
) -> VehiclePresentationProfile:
    if vehicle_type == VehicleType.HAUL_TRUCK:
        return VehiclePresentationProfile(
            presentation_key="haul_truck",
            display_name="Haul Truck",
            role_label="Heavy haul",
            body_length_m=1.72,
            body_width_m=0.92,
            primary_color="rgba(187, 101, 30, 0.96)",
            accent_color="rgba(246, 215, 167, 0.96)",
        )
    if vehicle_type == VehicleType.FORKLIFT:
        return VehiclePresentationProfile(
            presentation_key="forklift",
            display_name="Forklift",
            role_label="Yard handling",
            body_length_m=1.08,
            body_width_m=0.66,
            primary_color="rgba(10, 118, 108, 0.96)",
            accent_color="rgba(215, 245, 239, 0.96)",
        )
    if vehicle_type == VehicleType.CAR:
        return VehiclePresentationProfile(
            presentation_key="car",
            display_name="Car",
            role_label="Light vehicle",
            body_length_m=0.98,
            body_width_m=0.56,
            primary_color="rgba(36, 83, 199, 0.96)",
            accent_color="rgba(216, 227, 255, 0.96)",
        )
    return VehiclePresentationProfile(
        presentation_key="generic",
        display_name="Generic Vehicle",
        role_label="General operations",
        body_length_m=1.12,
        body_width_m=0.62,
        primary_color="rgba(95, 109, 121, 0.96)",
        accent_color="rgba(255, 255, 255, 0.92)",
    )


def build_vehicle_presentation_surface(
    *,
    vehicle_id: int,
    vehicle_type: VehicleType | None,
) -> VehiclePresentationSurface:
    profile = presentation_profile_for_vehicle_type(vehicle_type)
    return VehiclePresentationSurface(
        vehicle_id=vehicle_id,
        vehicle_type=vehicle_type.name if vehicle_type is not None else "GENERIC",
        presentation_key=profile.presentation_key,
        display_name=profile.display_name,
        role_label=profile.role_label,
        body_length_m=profile.body_length_m,
        body_width_m=profile.body_width_m,
        primary_color=profile.primary_color,
        accent_color=profile.accent_color,
    )


__all__ = [
    "VehiclePresentationProfile",
    "VehiclePresentationSurface",
    "build_vehicle_presentation_surface",
    "presentation_profile_for_vehicle_type",
]
