from __future__ import annotations

from dataclasses import dataclass

from autonomous_ops_sim.visualization.state import ReplayFrame, VisualizationState


@dataclass(frozen=True)
class ReplayStep:
    """Stable indexed replay step over visualization frames."""

    index: int
    frame: ReplayFrame


def iter_replay_steps(state: VisualizationState) -> tuple[ReplayStep, ...]:
    """Return replay steps in deterministic frame order."""

    return tuple(
        ReplayStep(index=index, frame=frame)
        for index, frame in enumerate(state.frames)
    )


def get_replay_frame(state: VisualizationState, index: int) -> ReplayFrame:
    """Return one replay frame by stable index."""

    if index < 0 or index >= len(state.frames):
        raise IndexError(f"frame index out of range: {index}")
    return state.frames[index]
