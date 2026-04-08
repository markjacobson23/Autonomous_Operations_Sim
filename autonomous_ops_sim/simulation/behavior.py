from dataclasses import dataclass
from enum import Enum


class VehicleOperationalState(str, Enum):
    """Small FSM state set for vehicle operational execution."""

    IDLE = "idle"
    MOVING = "moving"
    CONFLICT_WAIT = "conflict_wait"
    RESOURCE_WAIT = "resource_wait"
    SERVICING = "servicing"
    FAILED = "failed"


@dataclass(frozen=True)
class BehaviorTransition:
    """Immutable record of one behavior state transition."""

    from_state: VehicleOperationalState
    to_state: VehicleOperationalState
    reason: str


class InvalidBehaviorTransitionError(ValueError):
    """Raised when a vehicle behavior transition is not allowed."""


class VehicleBehaviorController:
    """Own explicit vehicle operational state and validated transitions."""

    _ALLOWED_TRANSITIONS = {
        VehicleOperationalState.IDLE: frozenset(
            {
                VehicleOperationalState.MOVING,
                VehicleOperationalState.CONFLICT_WAIT,
                VehicleOperationalState.RESOURCE_WAIT,
                VehicleOperationalState.SERVICING,
                VehicleOperationalState.FAILED,
            }
        ),
        VehicleOperationalState.MOVING: frozenset(
            {
                VehicleOperationalState.IDLE,
                VehicleOperationalState.CONFLICT_WAIT,
                VehicleOperationalState.FAILED,
            }
        ),
        VehicleOperationalState.CONFLICT_WAIT: frozenset(
            {
                VehicleOperationalState.MOVING,
                VehicleOperationalState.FAILED,
            }
        ),
        VehicleOperationalState.RESOURCE_WAIT: frozenset(
            {
                VehicleOperationalState.SERVICING,
                VehicleOperationalState.FAILED,
            }
        ),
        VehicleOperationalState.SERVICING: frozenset(
            {
                VehicleOperationalState.IDLE,
                VehicleOperationalState.FAILED,
            }
        ),
        VehicleOperationalState.FAILED: frozenset({VehicleOperationalState.IDLE}),
    }

    def __init__(
        self,
        *,
        vehicle_id: int,
        initial_state: VehicleOperationalState = VehicleOperationalState.IDLE,
    ) -> None:
        self._vehicle_id = vehicle_id
        self._state = initial_state
        self._history: list[BehaviorTransition] = []

    @property
    def vehicle_id(self) -> int:
        return self._vehicle_id

    @property
    def state(self) -> VehicleOperationalState:
        return self._state

    @property
    def transition_history(self) -> tuple[BehaviorTransition, ...]:
        return tuple(self._history)

    def transition_to(
        self,
        to_state: VehicleOperationalState,
        *,
        reason: str,
    ) -> BehaviorTransition:
        """Move to a new state when the transition is valid."""

        if not reason:
            raise ValueError("reason must be non-empty")
        if to_state == self._state:
            raise InvalidBehaviorTransitionError(
                f"Vehicle-{self.vehicle_id} is already in state {self._state.value}."
            )

        allowed = self._ALLOWED_TRANSITIONS[self._state]
        if to_state not in allowed:
            allowed_values = ", ".join(
                state.value for state in sorted(allowed, key=lambda state: state.value)
            )
            raise InvalidBehaviorTransitionError(
                "Invalid behavior transition for "
                f"Vehicle-{self.vehicle_id}: {self._state.value} -> {to_state.value}. "
                f"Allowed targets: {allowed_values}."
            )

        transition = BehaviorTransition(
            from_state=self._state,
            to_state=to_state,
            reason=reason,
        )
        self._history.append(transition)
        self._state = to_state
        return transition

    def fail(self, *, reason: str) -> BehaviorTransition:
        """Enter the failed state explicitly."""

        return self.transition_to(VehicleOperationalState.FAILED, reason=reason)

    def recover(self, *, reason: str) -> BehaviorTransition:
        """Recover from a failed state back to idle."""

        return self.transition_to(VehicleOperationalState.IDLE, reason=reason)
