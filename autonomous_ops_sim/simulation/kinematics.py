from __future__ import annotations

from dataclasses import dataclass
import math


DEFAULT_ACCELERATION_MPS2 = 6.0
DEFAULT_DECELERATION_MPS2 = 6.0


@dataclass(frozen=True)
class KinematicTraversalProfile:
    """One deterministic traversal profile for a bounded edge movement."""

    distance_m: float
    duration_s: float
    peak_speed_mps: float
    cruise_speed_mps: float
    acceleration_mps2: float
    deceleration_mps2: float
    acceleration_duration_s: float
    cruise_duration_s: float
    deceleration_duration_s: float
    profile_kind: str


def estimate_edge_travel_time_s(
    *,
    distance_m: float,
    speed_limit_mps: float,
    vehicle_max_speed_mps: float,
    acceleration_mps2: float = DEFAULT_ACCELERATION_MPS2,
    deceleration_mps2: float = DEFAULT_DECELERATION_MPS2,
) -> float:
    """Estimate edge traversal time from shared kinematic assumptions."""

    profile = build_kinematic_profile(
        distance_m=distance_m,
        speed_limit_mps=speed_limit_mps,
        vehicle_max_speed_mps=vehicle_max_speed_mps,
        acceleration_mps2=acceleration_mps2,
        deceleration_mps2=deceleration_mps2,
    )
    return profile.duration_s


def build_kinematic_profile(
    *,
    distance_m: float,
    speed_limit_mps: float,
    vehicle_max_speed_mps: float,
    duration_s: float | None = None,
    acceleration_mps2: float = DEFAULT_ACCELERATION_MPS2,
    deceleration_mps2: float = DEFAULT_DECELERATION_MPS2,
) -> KinematicTraversalProfile:
    """Build one bounded acceleration-aware traversal profile."""

    if not math.isfinite(distance_m) or distance_m < 0.0:
        raise ValueError("distance_m must be finite and non-negative")
    if distance_m == 0.0:
        return KinematicTraversalProfile(
            distance_m=0.0,
            duration_s=0.0 if duration_s is None else max(duration_s, 0.0),
            peak_speed_mps=0.0,
            cruise_speed_mps=0.0,
            acceleration_mps2=max(acceleration_mps2, 0.0),
            deceleration_mps2=max(deceleration_mps2, 0.0),
            acceleration_duration_s=0.0,
            cruise_duration_s=0.0 if duration_s is None else max(duration_s, 0.0),
            deceleration_duration_s=0.0,
            profile_kind="stationary",
        )

    if duration_s is not None:
        return _profile_for_authoritative_duration(
            distance_m=distance_m,
            duration_s=duration_s,
        )

    cruise_speed = min(vehicle_max_speed_mps, speed_limit_mps)
    if not math.isfinite(cruise_speed) or cruise_speed <= 0.0:
        raise ValueError("effective traversal speed must be finite and positive")
    if not math.isfinite(acceleration_mps2) or acceleration_mps2 <= 0.0:
        raise ValueError("acceleration_mps2 must be finite and positive")
    if not math.isfinite(deceleration_mps2) or deceleration_mps2 <= 0.0:
        raise ValueError("deceleration_mps2 must be finite and positive")

    acceleration_distance = (cruise_speed * cruise_speed) / (2.0 * acceleration_mps2)
    deceleration_distance = (cruise_speed * cruise_speed) / (2.0 * deceleration_mps2)

    if acceleration_distance + deceleration_distance < distance_m:
        cruise_distance = distance_m - acceleration_distance - deceleration_distance
        acceleration_duration = cruise_speed / acceleration_mps2
        deceleration_duration = cruise_speed / deceleration_mps2
        cruise_duration = cruise_distance / cruise_speed
        return KinematicTraversalProfile(
            distance_m=distance_m,
            duration_s=acceleration_duration + cruise_duration + deceleration_duration,
            peak_speed_mps=cruise_speed,
            cruise_speed_mps=cruise_speed,
            acceleration_mps2=acceleration_mps2,
            deceleration_mps2=deceleration_mps2,
            acceleration_duration_s=acceleration_duration,
            cruise_duration_s=cruise_duration,
            deceleration_duration_s=deceleration_duration,
            profile_kind="trapezoid",
        )

    peak_speed = math.sqrt(
        (2.0 * distance_m * acceleration_mps2 * deceleration_mps2)
        / (acceleration_mps2 + deceleration_mps2)
    )
    acceleration_duration = peak_speed / acceleration_mps2
    deceleration_duration = peak_speed / deceleration_mps2
    return KinematicTraversalProfile(
        distance_m=distance_m,
        duration_s=acceleration_duration + deceleration_duration,
        peak_speed_mps=peak_speed,
        cruise_speed_mps=peak_speed,
        acceleration_mps2=acceleration_mps2,
        deceleration_mps2=deceleration_mps2,
        acceleration_duration_s=acceleration_duration,
        cruise_duration_s=0.0,
        deceleration_duration_s=deceleration_duration,
        profile_kind="triangle",
    )


def sample_profile_distance(profile: KinematicTraversalProfile, elapsed_s: float) -> float:
    """Return traversed distance at one elapsed time within the profile."""

    if profile.duration_s <= 0.0 or profile.distance_m <= 0.0:
        return 0.0
    bounded_elapsed = min(max(elapsed_s, 0.0), profile.duration_s)
    acceleration_end = profile.acceleration_duration_s
    cruise_end = acceleration_end + profile.cruise_duration_s

    if bounded_elapsed <= acceleration_end:
        return 0.5 * profile.acceleration_mps2 * bounded_elapsed * bounded_elapsed

    acceleration_distance = (
        0.5
        * profile.acceleration_mps2
        * profile.acceleration_duration_s
        * profile.acceleration_duration_s
    )
    if bounded_elapsed <= cruise_end:
        cruise_elapsed = bounded_elapsed - acceleration_end
        return acceleration_distance + profile.cruise_speed_mps * cruise_elapsed

    deceleration_elapsed = bounded_elapsed - cruise_end
    deceleration_distance = (
        profile.cruise_speed_mps * deceleration_elapsed
        - 0.5 * profile.deceleration_mps2 * deceleration_elapsed * deceleration_elapsed
    )
    return min(
        profile.distance_m,
        acceleration_distance
        + profile.cruise_speed_mps * profile.cruise_duration_s
        + deceleration_distance,
    )


def sample_profile_speed(profile: KinematicTraversalProfile, elapsed_s: float) -> float:
    """Return instantaneous speed at one elapsed time within the profile."""

    if profile.duration_s <= 0.0:
        return 0.0
    bounded_elapsed = min(max(elapsed_s, 0.0), profile.duration_s)
    acceleration_end = profile.acceleration_duration_s
    cruise_end = acceleration_end + profile.cruise_duration_s

    if bounded_elapsed <= acceleration_end:
        return profile.acceleration_mps2 * bounded_elapsed
    if bounded_elapsed <= cruise_end:
        return profile.cruise_speed_mps
    deceleration_elapsed = bounded_elapsed - cruise_end
    return max(
        0.0,
        profile.cruise_speed_mps - profile.deceleration_mps2 * deceleration_elapsed,
    )


def _profile_for_authoritative_duration(
    *,
    distance_m: float,
    duration_s: float,
) -> KinematicTraversalProfile:
    if not math.isfinite(duration_s) or duration_s < 0.0:
        raise ValueError("duration_s must be finite and non-negative")
    if duration_s == 0.0:
        return KinematicTraversalProfile(
            distance_m=distance_m,
            duration_s=0.0,
            peak_speed_mps=0.0,
            cruise_speed_mps=0.0,
            acceleration_mps2=0.0,
            deceleration_mps2=0.0,
            acceleration_duration_s=0.0,
            cruise_duration_s=0.0,
            deceleration_duration_s=0.0,
            profile_kind="stationary",
        )

    half_duration = duration_s / 2.0
    peak_speed = (2.0 * distance_m) / duration_s
    acceleration = peak_speed / max(half_duration, 1e-9)
    return KinematicTraversalProfile(
        distance_m=distance_m,
        duration_s=duration_s,
        peak_speed_mps=peak_speed,
        cruise_speed_mps=peak_speed,
        acceleration_mps2=acceleration,
        deceleration_mps2=acceleration,
        acceleration_duration_s=half_duration,
        cruise_duration_s=0.0,
        deceleration_duration_s=half_duration,
        profile_kind="triangle_authoritative",
    )


__all__ = [
    "DEFAULT_ACCELERATION_MPS2",
    "DEFAULT_DECELERATION_MPS2",
    "KinematicTraversalProfile",
    "build_kinematic_profile",
    "estimate_edge_travel_time_s",
    "sample_profile_distance",
    "sample_profile_speed",
]
