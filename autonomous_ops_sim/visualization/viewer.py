from __future__ import annotations

import argparse
from pathlib import Path

from autonomous_ops_sim.visualization.replay import (
    get_replay_frame,
    iter_replay_steps,
)
from autonomous_ops_sim.visualization.state import (
    ReplayFrame,
    VisualizationState,
    load_visualization_json,
)


def render_replay_text(
    state: VisualizationState,
    *,
    frame_index: int | None = None,
) -> str:
    """Render a stable text view of a visualization replay."""

    lines = [
        (
            "Visualization Replay "
            f"seed={state.seed} final_time_s={state.final_time_s} "
            f"frames={len(state.frames)}"
        ),
        (
            "Map "
            f"nodes={len(state.map_surface.nodes)} "
            f"edges={len(state.map_surface.edges)}"
        ),
    ]

    frames = (
        (get_replay_frame(state, frame_index),)
        if frame_index is not None
        else tuple(step.frame for step in iter_replay_steps(state))
    )
    for frame in frames:
        lines.extend(_render_frame_lines(frame))

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autonomous-ops-viewer",
        description="Render deterministic visualization replay text.",
    )
    parser.add_argument(
        "visualization_path",
        help="Path to a visualization-state JSON export.",
    )
    parser.add_argument(
        "--frame-index",
        type=int,
        default=None,
        help="Render only one frame by index.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    state = load_visualization_json(Path(args.visualization_path))
    print(render_replay_text(state, frame_index=args.frame_index), end="")
    return 0


def _render_frame_lines(frame: ReplayFrame) -> list[str]:
    lines = [
        (
            f"Frame {frame.frame_index} @ {frame.timestamp_s}s "
            f"{frame.trigger.source}:{frame.trigger.event_name}"
        ),
        f"blocked_edges={list(frame.blocked_edge_ids)}",
    ]
    for vehicle in frame.vehicles:
        lines.append(
            "vehicle "
            f"{vehicle.vehicle_id} "
            f"node={vehicle.node_id} "
            f"state={vehicle.operational_state} "
            f"position={vehicle.position}"
        )
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
