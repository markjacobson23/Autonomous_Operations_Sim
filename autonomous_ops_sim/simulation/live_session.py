from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any

from autonomous_ops_sim.simulation.commands import SimulationCommand
from autonomous_ops_sim.simulation.control import (
    CommandApplicationRecord,
    SimulationController,
    build_controlled_engine_export,
)
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)


class SessionStateError(RuntimeError):
    """Raised when a live session operation is invalid for the session state."""


@dataclass(frozen=True)
class SessionAdvanceRecord:
    """Stable audit record for one explicit live session progression step."""

    sequence: int
    started_at_s: float
    completed_at_s: float


class LiveSimulationSession:
    """Own one explicit deterministic live runtime session for an engine run."""

    def __init__(
        self,
        engine: SimulationEngine,
        *,
        controller: SimulationController | None = None,
    ) -> None:
        runtime_controller = controller or SimulationController(engine)
        if runtime_controller.engine is not engine:
            raise ValueError("controller must own the provided engine")

        self._controller = runtime_controller
        self._progress_history: list[SessionAdvanceRecord] = []
        self._is_active = True

    @property
    def controller(self) -> SimulationController:
        """Return the controller used for live typed command application."""

        return self._controller

    @property
    def engine(self) -> SimulationEngine:
        """Return the authoritative engine for this live session."""

        return self.controller.engine

    @property
    def is_active(self) -> bool:
        """Return whether the session still accepts progression and commands."""

        return self._is_active

    @property
    def progress_history(self) -> tuple[SessionAdvanceRecord, ...]:
        """Return explicit live progression steps in stable application order."""

        return tuple(self._progress_history)

    @property
    def command_history(self) -> tuple[CommandApplicationRecord, ...]:
        """Return typed command applications captured during the session."""

        return self.controller.command_history

    def advance_to(self, until_s: float) -> SessionAdvanceRecord:
        """Advance the active session to one explicit simulated time."""

        self._require_active()
        if not math.isfinite(until_s):
            raise ValueError("until_s must be finite")
        if until_s < self.engine.simulated_time_s:
            raise ValueError(
                "until_s must be greater than or equal to current simulated time"
            )

        started_at_s = self.engine.simulated_time_s
        self.engine.run(until_s)
        record = SessionAdvanceRecord(
            sequence=len(self._progress_history),
            started_at_s=started_at_s,
            completed_at_s=self.engine.simulated_time_s,
        )
        self._progress_history.append(record)
        return record

    def advance_by(self, delta_s: float) -> SessionAdvanceRecord:
        """Advance the active session by one explicit simulated duration."""

        if not math.isfinite(delta_s):
            raise ValueError("delta_s must be finite")
        if delta_s < 0.0:
            raise ValueError("delta_s must be non-negative")
        return self.advance_to(self.engine.simulated_time_s + delta_s)

    def apply(self, command: SimulationCommand) -> CommandApplicationRecord:
        """Apply one typed command through the existing deterministic controller."""

        self._require_active()
        return self.controller.apply(command)

    def apply_all(
        self,
        commands: tuple[SimulationCommand, ...] | list[SimulationCommand],
    ) -> tuple[CommandApplicationRecord, ...]:
        """Apply typed commands in the exact provided order."""

        self._require_active()
        return tuple(self.apply(command) for command in commands)

    def close(self) -> None:
        """Mark the session complete and reject future mutation."""

        self._is_active = False

    def _require_active(self) -> None:
        if not self.is_active:
            raise SessionStateError("live session is not active")


def build_live_session_export(
    session: LiveSimulationSession,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> dict[str, Any]:
    """Return a stable export for one live-controlled runtime session."""

    metrics_summary = summary or summarize_engine_execution(session.engine)
    export_record = build_controlled_engine_export(
        session.controller,
        summary=metrics_summary,
    )
    export_record["session_history"] = [
        session_advance_to_dict(record) for record in session.progress_history
    ]
    return export_record


def export_live_session_json(
    session: LiveSimulationSession,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> str:
    """Return deterministic JSON for one live-controlled runtime session."""

    export_record = build_live_session_export(session, summary=summary)
    return json.dumps(export_record, indent=2, sort_keys=True) + "\n"


def session_advance_to_dict(record: SessionAdvanceRecord) -> dict[str, Any]:
    """Convert one session advancement record into a stable export record."""

    return {
        "sequence": record.sequence,
        "started_at_s": record.started_at_s,
        "completed_at_s": record.completed_at_s,
    }
