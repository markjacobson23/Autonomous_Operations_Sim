from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autonomous_ops_sim.visualization.replay import get_replay_frame
from autonomous_ops_sim.visualization.state import (
    MapSurface,
    ReplayFrame,
    VisualizationState,
    load_visualization_json,
)


@dataclass(frozen=True)
class CanvasPoint:
    x: float
    y: float


@dataclass(frozen=True)
class RenderedNode:
    node_id: int
    center: CanvasPoint
    node_type: str


@dataclass(frozen=True)
class RenderedEdge:
    edge_id: int
    start: CanvasPoint
    end: CanvasPoint
    blocked: bool


@dataclass(frozen=True)
class RenderedVehicle:
    vehicle_id: int
    node_id: int
    center: CanvasPoint
    operational_state: str
    color: str


@dataclass(frozen=True)
class FrameRenderPlan:
    frame_index: int
    timestamp_s: float
    frame_label: str
    nodes: tuple[RenderedNode, ...]
    edges: tuple[RenderedEdge, ...]
    vehicles: tuple[RenderedVehicle, ...]


@dataclass
class ReplayController:
    """Deterministic playback controller over completed replay frames."""

    state: VisualizationState
    frame_index: int = 0
    is_playing: bool = False

    def current_frame(self) -> ReplayFrame:
        return get_replay_frame(self.state, self.frame_index)

    def play(self) -> None:
        if self.frame_index < len(self.state.frames) - 1:
            self.is_playing = True

    def pause(self) -> None:
        self.is_playing = False

    def next_frame(self) -> ReplayFrame:
        if self.frame_index < len(self.state.frames) - 1:
            self.frame_index += 1
        else:
            self.is_playing = False
        return self.current_frame()

    def reset(self) -> ReplayFrame:
        self.is_playing = False
        self.frame_index = 0
        return self.current_frame()

    def advance_playback(self) -> bool:
        if not self.is_playing:
            return False
        if self.frame_index >= len(self.state.frames) - 1:
            self.is_playing = False
            return False

        self.frame_index += 1
        if self.frame_index >= len(self.state.frames) - 1:
            self.is_playing = False
        return True


def build_frame_render_plan(
    state: VisualizationState,
    *,
    frame_index: int,
    canvas_width: int = 900,
    canvas_height: int = 640,
    padding: int = 48,
) -> FrameRenderPlan:
    """Project one visualization frame into deterministic canvas primitives."""

    if canvas_width <= padding * 2 or canvas_height <= padding * 2:
        raise ValueError("canvas dimensions must exceed twice the padding")

    frame = get_replay_frame(state, frame_index)
    layout = _build_canvas_layout(
        state.map_surface,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        padding=padding,
    )

    return FrameRenderPlan(
        frame_index=frame.frame_index,
        timestamp_s=frame.timestamp_s,
        frame_label=(
            f"Frame {frame.frame_index} @ {frame.timestamp_s}s "
            f"{frame.trigger.source}:{frame.trigger.event_name}"
        ),
        nodes=tuple(
            RenderedNode(
                node_id=node.node_id,
                center=layout[node.node_id],
                node_type=node.node_type,
            )
            for node in state.map_surface.nodes
        ),
        edges=tuple(
            RenderedEdge(
                edge_id=edge.edge_id,
                start=layout[edge.start_node_id],
                end=layout[edge.end_node_id],
                blocked=edge.edge_id in frame.blocked_edge_ids,
            )
            for edge in state.map_surface.edges
        ),
        vehicles=tuple(
            RenderedVehicle(
                vehicle_id=vehicle.vehicle_id,
                node_id=vehicle.node_id,
                center=_project_position(
                    position=vehicle.position,
                    map_surface=state.map_surface,
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                    padding=padding,
                ),
                operational_state=vehicle.operational_state,
                color=_vehicle_color(vehicle.operational_state),
            )
            for vehicle in frame.vehicles
        ),
    )


def render_frame_plan_to_canvas(
    canvas: Any,
    plan: FrameRenderPlan,
) -> None:
    """Draw one projected frame onto a Tk-compatible canvas."""

    canvas.delete("all")
    canvas.create_text(
        12,
        12,
        anchor="nw",
        text=plan.frame_label,
        fill="#111827",
        font=("TkDefaultFont", 11, "bold"),
        tags=("frame-label",),
    )

    for edge in plan.edges:
        canvas.create_line(
            edge.start.x,
            edge.start.y,
            edge.end.x,
            edge.end.y,
            fill="#dc2626" if edge.blocked else "#94a3b8",
            width=3 if edge.blocked else 2,
            tags=("edge", f"edge-{edge.edge_id}"),
        )

    for node in plan.nodes:
        canvas.create_oval(
            node.center.x - 8,
            node.center.y - 8,
            node.center.x + 8,
            node.center.y + 8,
            fill="#0f172a",
            outline="#f8fafc",
            width=2,
            tags=("node", f"node-{node.node_id}"),
        )
        canvas.create_text(
            node.center.x,
            node.center.y - 16,
            text=str(node.node_id),
            fill="#1f2937",
            font=("TkDefaultFont", 10),
            tags=("node-label", f"node-label-{node.node_id}"),
        )

    for vehicle in plan.vehicles:
        canvas.create_oval(
            vehicle.center.x - 12,
            vehicle.center.y - 12,
            vehicle.center.x + 12,
            vehicle.center.y + 12,
            fill=vehicle.color,
            outline="#0f172a",
            width=2,
            tags=("vehicle", f"vehicle-{vehicle.vehicle_id}"),
        )
        canvas.create_text(
            vehicle.center.x,
            vehicle.center.y + 18,
            text=f"V{vehicle.vehicle_id}:{vehicle.operational_state}",
            fill="#111827",
            font=("TkDefaultFont", 10),
            tags=("vehicle-label", f"vehicle-label-{vehicle.vehicle_id}"),
        )


class GraphicalReplayViewer:
    """Small Tkinter replay viewer over deterministic visualization state."""

    def __init__(
        self,
        state: VisualizationState,
        *,
        canvas_width: int = 900,
        canvas_height: int = 640,
        frame_delay_ms: int = 250,
    ) -> None:
        import tkinter as tk

        self._tk = tk
        self.state = state
        self.controller = ReplayController(state)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.frame_delay_ms = frame_delay_ms
        self._after_id: str | None = None

        self.root = tk.Tk()
        self.root.title("Autonomous Ops Graphical Replay Viewer")

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=12, pady=12)

        tk.Button(controls, text="Play", command=self.play).pack(side="left")
        tk.Button(controls, text="Pause", command=self.pause).pack(side="left")
        tk.Button(controls, text="Next Frame", command=self.next_frame).pack(side="left")
        tk.Button(controls, text="Reset", command=self.reset).pack(side="left")

        self.status_var = tk.StringVar()
        tk.Label(controls, textvariable=self.status_var).pack(side="right")

        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            background="#f8fafc",
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._render_current_frame()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def play(self) -> None:
        self.controller.play()
        self._schedule_tick()
        self._update_status()

    def pause(self) -> None:
        self.controller.pause()
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._update_status()

    def next_frame(self) -> None:
        self.controller.pause()
        self.controller.next_frame()
        self._render_current_frame()

    def reset(self) -> None:
        self.controller.reset()
        self._render_current_frame()

    def run(self) -> None:
        self.root.mainloop()

    def _schedule_tick(self) -> None:
        if self._after_id is None and self.controller.is_playing:
            self._after_id = self.root.after(self.frame_delay_ms, self._tick)

    def _tick(self) -> None:
        self._after_id = None
        if self.controller.advance_playback():
            self._render_current_frame()
        else:
            self._update_status()
        self._schedule_tick()

    def _render_current_frame(self) -> None:
        plan = build_frame_render_plan(
            self.state,
            frame_index=self.controller.frame_index,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
        )
        render_frame_plan_to_canvas(self.canvas, plan)
        self._update_status()

    def _update_status(self) -> None:
        status = "playing" if self.controller.is_playing else "paused"
        self.status_var.set(
            f"{status} frame={self.controller.frame_index}/{len(self.state.frames) - 1}"
        )

    def _on_close(self) -> None:
        self.pause()
        self.root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autonomous-ops-gui-viewer",
        description="Render deterministic visualization replay graphics.",
    )
    parser.add_argument(
        "visualization_path",
        help="Path to a visualization-state JSON export.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=900,
        help="Canvas width in pixels.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=640,
        help="Canvas height in pixels.",
    )
    parser.add_argument(
        "--frame-delay-ms",
        type=int,
        default=250,
        help="Playback delay between frames while playing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    state = load_visualization_json(Path(args.visualization_path))
    viewer = GraphicalReplayViewer(
        state,
        canvas_width=args.width,
        canvas_height=args.height,
        frame_delay_ms=args.frame_delay_ms,
    )
    viewer.run()
    return 0


def _build_canvas_layout(
    map_surface: MapSurface,
    *,
    canvas_width: int,
    canvas_height: int,
    padding: int,
) -> dict[int, CanvasPoint]:
    positions = {
        node.node_id: node.position
        for node in map_surface.nodes
    }

    for edge in map_surface.edges:
        if edge.start_node_id not in positions or edge.end_node_id not in positions:
            raise ValueError(
                "map surface edge references a node that is not present in the node list"
            )

    return {
        node.node_id: _project_position(
            position=node.position,
            map_surface=map_surface,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            padding=padding,
        )
        for node in map_surface.nodes
    }


def _project_position(
    *,
    position: tuple[float, float, float],
    map_surface: MapSurface,
    canvas_width: int,
    canvas_height: int,
    padding: int,
) -> CanvasPoint:
    xs = [node.position[0] for node in map_surface.nodes]
    ys = [node.position[1] for node in map_surface.nodes]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    inner_width = canvas_width - (padding * 2)
    inner_height = canvas_height - (padding * 2)

    x = _project_axis(position[0], min_x, max_x, padding, inner_width)
    y = canvas_height - _project_axis(position[1], min_y, max_y, padding, inner_height)
    return CanvasPoint(x=x, y=y)


def _project_axis(
    value: float,
    minimum: float,
    maximum: float,
    padding: int,
    span_size: int,
) -> float:
    if maximum == minimum:
        return padding + (span_size / 2.0)
    scale = (value - minimum) / (maximum - minimum)
    return padding + (scale * span_size)


def _vehicle_color(operational_state: str) -> str:
    return {
        "idle": "#2563eb",
        "moving": "#059669",
        "loading": "#ca8a04",
        "unloading": "#ea580c",
    }.get(operational_state, "#7c3aed")
