import math

from autonomous_ops_sim.simulation.kinematics import (
    build_kinematic_profile,
    estimate_edge_travel_time_s,
    sample_profile_distance,
    sample_profile_speed,
)


def test_estimated_edge_travel_time_uses_acceleration_aware_profile() -> None:
    travel_time_s = estimate_edge_travel_time_s(
        distance_m=1.0,
        speed_limit_mps=10.0,
        vehicle_max_speed_mps=5.0,
    )

    assert math.isclose(travel_time_s, 0.816496580927726)


def test_authoritative_duration_profile_samples_distance_and_speed_consistently() -> None:
    profile = build_kinematic_profile(
        distance_m=1.0,
        speed_limit_mps=5.0,
        vehicle_max_speed_mps=5.0,
        duration_s=0.2,
    )

    assert profile.profile_kind == "triangle_authoritative"
    assert math.isclose(sample_profile_distance(profile, 0.1), 0.5)
    assert math.isclose(sample_profile_speed(profile, 0.1), 10.0)
