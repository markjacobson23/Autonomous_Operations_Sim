from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from autonomous_ops_sim.visualization.live_viewer import (
    AssignSelectedDestinationViewerAction,
    BlockEdgeViewerAction,
    LiveViewerActionValidationError,
    LiveViewerController,
    RepositionSelectedVehicleViewerAction,
    SelectVehicleViewerAction,
)
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
    selected: bool = False


@dataclass(frozen=True)
class FrameRenderPlan:
    frame_index: int
    timestamp_s: float
    frame_label: str
    nodes: tuple[RenderedNode, ...]
    edges: tuple[RenderedEdge, ...]
    vehicles: tuple[RenderedVehicle, ...]


@dataclass(frozen=True)
class FrameStatus:
    playback_state: str
    playback_speed: float
    frame_index: int
    last_frame_index: int
    frame_count: int
    timestamp_s: float
    trigger_source: str
    trigger_event_name: str
    blocked_edge_ids: tuple[int, ...]
    vehicle_count: int
    vehicle_states: tuple[tuple[str, int], ...]

    def summary_text(self) -> str:
        return (
            f"{self.playback_state} frame={self.frame_index}/{self.last_frame_index} "
            f"time={self.timestamp_s}s "
            f"trigger={self.trigger_source}:{self.trigger_event_name} "
            f"speed={self.playback_speed}x"
        )

    def metadata_text(self) -> str:
        state_counts = ", ".join(
            f"{state}={count}"
            for state, count in self.vehicle_states
        ) or "none"
        return (
            f"blocked_edges={list(self.blocked_edge_ids)} "
            f"vehicles={self.vehicle_count} "
            f"states={state_counts}"
        )


@dataclass
class ReplayController:
    """Deterministic playback controller over completed replay frames."""

    state: VisualizationState
    frame_index: int = 0
    is_playing: bool = False
    playback_speed: float = 1.0

    def current_frame(self) -> ReplayFrame:
        return get_replay_frame(self.state, self.frame_index)

    @property
    def frame_count(self) -> int:
        return len(self.state.frames)

    @property
    def last_frame_index(self) -> int:
        return self.frame_count - 1

    def play(self) -> None:
        if self.frame_index < self.last_frame_index:
            self.is_playing = True

    def pause(self) -> None:
        self.is_playing = False

    def next_frame(self) -> ReplayFrame:
        self.pause()
        if self.frame_index < self.last_frame_index:
            self.frame_index += 1
        return self.current_frame()

    def previous_frame(self) -> ReplayFrame:
        self.pause()
        if self.frame_index > 0:
            self.frame_index -= 1
        return self.current_frame()

    def first_frame(self) -> ReplayFrame:
        self.pause()
        self.frame_index = 0
        return self.current_frame()

    def last_frame(self) -> ReplayFrame:
        self.pause()
        self.frame_index = self.last_frame_index
        return self.current_frame()

    def jump_to_frame(self, frame_index: int) -> ReplayFrame:
        self.pause()
        get_replay_frame(self.state, frame_index)
        self.frame_index = frame_index
        return self.current_frame()

    def set_playback_speed(self, speed: float) -> None:
        if not math.isfinite(speed) or speed <= 0.0:
            raise ValueError("playback speed must be a finite positive number")
        self.playback_speed = speed

    def playback_delay_ms(self, base_delay_ms: int) -> int:
        if base_delay_ms <= 0:
            raise ValueError("base delay must be positive")
        return max(1, int(round(base_delay_ms / self.playback_speed)))

    def current_status(self) -> FrameStatus:
        frame = self.current_frame()
        vehicle_state_counts: dict[str, int] = {}
        for vehicle in frame.vehicles:
            vehicle_state_counts[vehicle.operational_state] = (
                vehicle_state_counts.get(vehicle.operational_state, 0) + 1
            )
        return FrameStatus(
            playback_state="playing" if self.is_playing else "paused",
            playback_speed=self.playback_speed,
            frame_index=frame.frame_index,
            last_frame_index=self.last_frame_index,
            frame_count=self.frame_count,
            timestamp_s=frame.timestamp_s,
            trigger_source=frame.trigger.source,
            trigger_event_name=frame.trigger.event_name,
            blocked_edge_ids=frame.blocked_edge_ids,
            vehicle_count=len(frame.vehicles),
            vehicle_states=tuple(sorted(vehicle_state_counts.items())),
        )

    def reset(self) -> ReplayFrame:
        return self.first_frame()

    def advance_playback(self) -> bool:
        if not self.is_playing:
            return False
        if self.frame_index >= self.last_frame_index:
            self.is_playing = False
            return False

        self.frame_index += 1
        if self.frame_index >= self.last_frame_index:
            self.is_playing = False
        return True


def build_frame_render_plan(
    state: VisualizationState,
    *,
    frame_index: int,
    canvas_width: int = 900,
    canvas_height: int = 640,
    padding: int = 48,
    selected_vehicle_id: int | None = None,
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
                selected=vehicle.vehicle_id == selected_vehicle_id,
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
            outline="#f59e0b" if vehicle.selected else "#0f172a",
            width=3 if vehicle.selected else 2,
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
        tk.Button(controls, text="First", command=self.first_frame).pack(side="left")
        tk.Button(controls, text="Previous", command=self.previous_frame).pack(side="left")
        tk.Button(controls, text="Next", command=self.next_frame).pack(side="left")
        tk.Button(controls, text="Last", command=self.last_frame).pack(side="left")
        tk.Button(controls, text="Reset", command=self.reset).pack(side="left")

        self.jump_var = tk.StringVar(value="0")
        tk.Entry(controls, textvariable=self.jump_var, width=6).pack(
            side="left",
            padx=(12, 4),
        )
        tk.Button(controls, text="Jump", command=self.jump_to_frame).pack(side="left")

        self.speed_var = tk.StringVar(value="1.0x")
        tk.Label(controls, text="Speed").pack(side="left", padx=(12, 4))
        tk.OptionMenu(
            controls,
            self.speed_var,
            "0.5x",
            "1.0x",
            "2.0x",
            "4.0x",
            command=lambda _selected: self._on_speed_change(),
        ).pack(side="left")

        self.status_var = tk.StringVar()
        tk.Label(controls, textvariable=self.status_var).pack(side="right")

        self.metadata_var = tk.StringVar()
        tk.Label(
            self.root,
            textvariable=self.metadata_var,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=12, pady=(0, 8))

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
        self.controller.next_frame()
        self._render_current_frame()

    def previous_frame(self) -> None:
        self.controller.previous_frame()
        self._render_current_frame()

    def first_frame(self) -> None:
        self.controller.first_frame()
        self.jump_var.set(str(self.controller.frame_index))
        self._render_current_frame()

    def last_frame(self) -> None:
        self.controller.last_frame()
        self.jump_var.set(str(self.controller.frame_index))
        self._render_current_frame()

    def jump_to_frame(self) -> None:
        try:
            frame_index = int(self.jump_var.get())
            self.controller.jump_to_frame(frame_index)
        except (TypeError, ValueError, IndexError):
            self.status_var.set(
                f"paused invalid-frame={self.jump_var.get()} "
                f"valid=0-{self.controller.last_frame_index}"
            )
            return
        self._render_current_frame()

    def reset(self) -> None:
        self.controller.reset()
        self.jump_var.set(str(self.controller.frame_index))
        self._render_current_frame()

    def run(self) -> None:
        self.root.mainloop()

    def _schedule_tick(self) -> None:
        if self._after_id is None and self.controller.is_playing:
            self._after_id = self.root.after(
                self.controller.playback_delay_ms(self.frame_delay_ms),
                self._tick,
            )

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
        status = self.controller.current_status()
        self.jump_var.set(str(status.frame_index))
        self.status_var.set(status.summary_text())
        self.metadata_var.set(status.metadata_text())

    def _on_speed_change(self) -> None:
        speed_text = self.speed_var.get().removesuffix("x")
        try:
            speed = float(speed_text)
        except ValueError:
            self.status_var.set(f"paused invalid-speed={self.speed_var.get()}")
            return
        self.controller.set_playback_speed(speed)
        self._update_status()

    def _on_close(self) -> None:
        self.pause()
        self.root.destroy()


class GraphicalLiveViewer:
    """Small Tkinter live viewer over a deterministic live-session controller."""

    def __init__(
        self,
        controller: LiveViewerController,
        *,
        canvas_width: int = 900,
        canvas_height: int = 640,
    ) -> None:
        import tkinter as tk

        self._tk = tk
        self.controller = controller
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        self.root = tk.Tk()
        self.root.title("Autonomous Ops Graphical Live Viewer")

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=12, pady=12)

        tk.Label(controls, text="Vehicle").pack(side="left")
        self.vehicle_var = tk.StringVar(value="")
        tk.Entry(controls, textvariable=self.vehicle_var, width=6).pack(
            side="left",
            padx=(4, 4),
        )
        tk.Button(
            controls,
            text="Select",
            command=self.select_vehicle,
        ).pack(side="left", padx=(0, 12))

        tk.Label(controls, text="Destination").pack(side="left")
        self.destination_var = tk.StringVar(value="")
        tk.Entry(controls, textvariable=self.destination_var, width=6).pack(
            side="left",
            padx=(4, 4),
        )
        tk.Button(
            controls,
            text="Assign",
            command=self.assign_destination,
        ).pack(side="left", padx=(0, 12))

        tk.Label(controls, text="Edge").pack(side="left")
        self.edge_var = tk.StringVar(value="")
        tk.Entry(controls, textvariable=self.edge_var, width=6).pack(
            side="left",
            padx=(4, 4),
        )
        tk.Button(
            controls,
            text="Block",
            command=self.block_edge,
        ).pack(side="left", padx=(0, 12))

        tk.Label(controls, text="Reposition").pack(side="left")
        self.reposition_var = tk.StringVar(value="")
        tk.Entry(controls, textvariable=self.reposition_var, width=6).pack(
            side="left",
            padx=(4, 4),
        )
        tk.Button(
            controls,
            text="Move",
            command=self.reposition_vehicle,
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            controls,
            text="Refresh",
            command=self.refresh,
        ).pack(side="left")

        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var, anchor="w").pack(
            fill="x",
            padx=12,
            pady=(0, 4),
        )

        self.metadata_var = tk.StringVar()
        tk.Label(
            self.root,
            textvariable=self.metadata_var,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=12, pady=(0, 4))

        self.message_var = tk.StringVar()
        tk.Label(
            self.root,
            textvariable=self.message_var,
            anchor="w",
            justify="left",
            fg="#92400e",
        ).pack(fill="x", padx=12, pady=(0, 8))

        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            background="#f8fafc",
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._render_current_state()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        self.root.mainloop()

    def refresh(self) -> None:
        self.controller.refresh()
        self.message_var.set("refreshed live visualization from session state")
        self._render_current_state()

    def select_vehicle(self) -> None:
        self._apply_action_from_entry(
            self.vehicle_var,
            lambda value: SelectVehicleViewerAction(vehicle_id=value),
        )

    def assign_destination(self) -> None:
        self._apply_action_from_entry(
            self.destination_var,
            lambda value: AssignSelectedDestinationViewerAction(
                destination_node_id=value
            ),
        )

    def block_edge(self) -> None:
        self._apply_action_from_entry(
            self.edge_var,
            lambda value: BlockEdgeViewerAction(edge_id=value),
        )

    def reposition_vehicle(self) -> None:
        self._apply_action_from_entry(
            self.reposition_var,
            lambda value: RepositionSelectedVehicleViewerAction(node_id=value),
        )

    def _apply_action_from_entry(
        self,
        field: Any,
        action_builder: Any,
    ) -> None:
        try:
            value = int(field.get())
            result = self.controller.apply_action(action_builder(value))
        except (TypeError, ValueError, LiveViewerActionValidationError) as exc:
            self.message_var.set(str(exc))
            return

        if result.command_record is None:
            self.message_var.set(
                f"selected vehicle {result.selected_vehicle_id}"
            )
        else:
            self.message_var.set(
                "applied "
                f"{result.command_record.command.command_type}"
            )
        self._render_current_state()

    def _render_current_state(self) -> None:
        state = self.controller.visualization_state
        frame_index = len(state.frames) - 1
        plan = build_frame_render_plan(
            state,
            frame_index=frame_index,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            selected_vehicle_id=self.controller.selected_vehicle_id,
        )
        render_frame_plan_to_canvas(self.canvas, plan)

        current_frame = state.frames[frame_index]
        selected_vehicle_text = (
            "none"
            if self.controller.selected_vehicle_id is None
            else str(self.controller.selected_vehicle_id)
        )
        self.status_var.set(
            f"time={current_frame.timestamp_s}s "
            f"selected_vehicle={selected_vehicle_text} "
            f"trigger={current_frame.trigger.source}:{current_frame.trigger.event_name}"
        )

        vehicle_state_counts: dict[str, int] = {}
        for vehicle in current_frame.vehicles:
            vehicle_state_counts[vehicle.operational_state] = (
                vehicle_state_counts.get(vehicle.operational_state, 0) + 1
            )
        state_counts = ", ".join(
            f"{name}={count}"
            for name, count in sorted(vehicle_state_counts.items())
        ) or "none"
        self.metadata_var.set(
            f"blocked_edges={list(current_frame.blocked_edge_ids)} "
            f"vehicles={len(current_frame.vehicles)} "
            f"states={state_counts}"
        )

    def _on_close(self) -> None:
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
