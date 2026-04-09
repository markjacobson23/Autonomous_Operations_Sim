from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Callable

from autonomous_ops_sim.visualization.live_viewer import (
    AssignSelectedDestinationViewerAction,
    BlockEdgeViewerAction,
    LiveViewerAction,
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


CANVAS_BACKGROUND = "#f3f7fb"
PANEL_BACKGROUND = "#f8fafc"
PANEL_BORDER = "#d8e1eb"
TEXT_PRIMARY = "#0f172a"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748b"
ACCENT = "#0f766e"
SELECTION = "#f59e0b"
BLOCKED = "#dc2626"

NODE_TYPE_COLORS = {
    "depot": "#0f766e",
    "intersection": "#3b82f6",
    "loading_zone": "#f59e0b",
    "unloading_zone": "#f97316",
    "job_site": "#9333ea",
}

VEHICLE_STATE_COLORS = {
    "idle": "#2563eb",
    "moving": "#059669",
    "loading": "#ca8a04",
    "unloading": "#ea580c",
}

LIVE_INTERACTION_MODES = (
    "select_vehicle",
    "assign_destination",
    "reposition_vehicle",
    "block_edge",
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
    fill_color: str
    outline_color: str


@dataclass(frozen=True)
class RenderedEdge:
    edge_id: int
    start: CanvasPoint
    end: CanvasPoint
    midpoint: CanvasPoint
    blocked: bool
    stroke_color: str
    label: str


@dataclass(frozen=True)
class RenderedVehicle:
    vehicle_id: int
    node_id: int
    center: CanvasPoint
    operational_state: str
    color: str
    label: str
    state_badge: str
    selected: bool = False


@dataclass(frozen=True)
class FrameRenderPlan:
    frame_index: int
    timestamp_s: float
    frame_label: str
    frame_subtitle: str
    selected_vehicle_id: int | None
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
            f"{self.playback_state.title()}  "
            f"Frame {self.frame_index + 1} of {self.frame_count}  "
            f"Time {self.timestamp_s:.2f}s  "
            f"Trigger {self.trigger_source}:{self.trigger_event_name}  "
            f"Speed {self.playback_speed:.1f}x"
        )

    def metadata_text(self) -> str:
        state_counts = ", ".join(
            f"{state} {count}"
            for state, count in self.vehicle_states
        ) or "No vehicles"
        blocked_summary = (
            ", ".join(str(edge_id) for edge_id in self.blocked_edge_ids)
            if self.blocked_edge_ids
            else "none"
        )
        return (
            f"Vehicles {self.vehicle_count}  "
            f"States {state_counts}  "
            f"Blocked edges {blocked_summary}"
        )


@dataclass(frozen=True)
class FrameInspector:
    headline: str
    timeline_text: str
    trigger_text: str
    fleet_text: str
    blocked_text: str
    selection_title: str
    selection_details: str
    hint_text: str


@dataclass(frozen=True)
class CanvasHitTarget:
    target_type: str
    target_id: int
    distance_px: float


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
    padding: int = 56,
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

    selected_vehicle = next(
        (
            vehicle
            for vehicle in frame.vehicles
            if vehicle.vehicle_id == selected_vehicle_id
        ),
        None,
    )
    subtitle_parts = [
        f"{len(frame.vehicles)} vehicles",
        (
            f"{len(frame.blocked_edge_ids)} blocked edges"
            if frame.blocked_edge_ids
            else "no blocked edges"
        ),
    ]
    if selected_vehicle is not None:
        subtitle_parts.append(
            f"selected V{selected_vehicle.vehicle_id} at node {selected_vehicle.node_id}"
        )

    return FrameRenderPlan(
        frame_index=frame.frame_index,
        timestamp_s=frame.timestamp_s,
        frame_label=(
            f"Frame {frame.frame_index}  "
            f"{frame.trigger.source}:{frame.trigger.event_name}"
        ),
        frame_subtitle="  |  ".join(subtitle_parts),
        selected_vehicle_id=selected_vehicle_id,
        nodes=tuple(
            RenderedNode(
                node_id=node.node_id,
                center=layout[node.node_id],
                node_type=node.node_type,
                fill_color=_node_fill_color(node.node_type),
                outline_color="#ffffff",
            )
            for node in state.map_surface.nodes
        ),
        edges=tuple(
            RenderedEdge(
                edge_id=edge.edge_id,
                start=layout[edge.start_node_id],
                end=layout[edge.end_node_id],
                midpoint=_midpoint(layout[edge.start_node_id], layout[edge.end_node_id]),
                blocked=edge.edge_id in frame.blocked_edge_ids,
                stroke_color=BLOCKED if edge.edge_id in frame.blocked_edge_ids else "#94a3b8",
                label=f"E{edge.edge_id}",
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
                label=f"V{vehicle.vehicle_id}",
                state_badge=vehicle.operational_state.replace("_", " ").title(),
                selected=vehicle.vehicle_id == selected_vehicle_id,
            )
            for vehicle in frame.vehicles
        ),
    )


def build_frame_inspector(
    state: VisualizationState,
    *,
    frame_index: int,
    playback_state: str,
    playback_speed: float,
    selected_vehicle_id: int | None = None,
    interaction_mode: str | None = None,
) -> FrameInspector:
    """Build stable viewer-facing summary text for one frame."""

    frame = get_replay_frame(state, frame_index)
    vehicle_state_counts: dict[str, int] = {}
    for vehicle in frame.vehicles:
        vehicle_state_counts[vehicle.operational_state] = (
            vehicle_state_counts.get(vehicle.operational_state, 0) + 1
        )

    blocked_text = (
        ", ".join(f"E{edge_id}" for edge_id in frame.blocked_edge_ids)
        if frame.blocked_edge_ids
        else "None"
    )
    selected_vehicle = next(
        (
            vehicle
            for vehicle in frame.vehicles
            if vehicle.vehicle_id == selected_vehicle_id
        ),
        None,
    )
    if selected_vehicle is None:
        selection_title = "Selection"
        selection_details = "No vehicle selected."
    else:
        selection_title = f"Selected vehicle V{selected_vehicle.vehicle_id}"
        selection_details = (
            f"Node {selected_vehicle.node_id}\n"
            f"State {selected_vehicle.operational_state}\n"
            f"Position {selected_vehicle.position}"
        )

    hint_text = (
        _interaction_mode_hint(interaction_mode, selected_vehicle_id)
        if interaction_mode is not None
        else "Use playback controls or the timeline to inspect state changes."
    )
    return FrameInspector(
        headline=(
            f"{playback_state.title()}  "
            f"Frame {frame.frame_index + 1}/{len(state.frames)}  "
            f"Time {frame.timestamp_s:.2f}s"
        ),
        timeline_text=f"Seed {state.seed}  Final time {state.final_time_s:.2f}s",
        trigger_text=(
            f"Trigger {frame.trigger.source}:{frame.trigger.event_name}  "
            f"sequence {frame.trigger.sequence}"
        ),
        fleet_text=(
            ", ".join(
                f"{state_name} {count}"
                for state_name, count in sorted(vehicle_state_counts.items())
            )
            or "No vehicles"
        ),
        blocked_text=blocked_text,
        selection_title=selection_title,
        selection_details=selection_details,
        hint_text=(
            f"{hint_text}  Playback speed {playback_speed:.1f}x."
            if interaction_mode is None
            else hint_text
        ),
    )


def resolve_live_click_action(
    plan: FrameRenderPlan,
    click_point: CanvasPoint,
    *,
    interaction_mode: str,
    selected_vehicle_id: int | None,
) -> LiveViewerAction | None:
    """Resolve one canvas click into a stable live viewer action."""

    if interaction_mode not in LIVE_INTERACTION_MODES:
        raise ValueError(f"unsupported interaction mode: {interaction_mode}")

    if interaction_mode == "select_vehicle":
        target = _find_nearest_vehicle(plan, click_point, max_distance_px=28.0)
        if target is None:
            return None
        return SelectVehicleViewerAction(vehicle_id=target.target_id)

    if interaction_mode == "block_edge":
        target = _find_nearest_edge(plan, click_point, max_distance_px=18.0)
        if target is None:
            return None
        return BlockEdgeViewerAction(edge_id=target.target_id)

    if selected_vehicle_id is None:
        return None

    target = _find_nearest_node(plan, click_point, max_distance_px=24.0)
    if target is None:
        return None
    if interaction_mode == "assign_destination":
        return AssignSelectedDestinationViewerAction(destination_node_id=target.target_id)
    return RepositionSelectedVehicleViewerAction(node_id=target.target_id)


def render_frame_plan_to_canvas(
    canvas: Any,
    plan: FrameRenderPlan,
) -> None:
    """Draw one projected frame onto a Tk-compatible canvas."""

    width = int(float(canvas.cget("width")))
    height = int(float(canvas.cget("height")))

    canvas.delete("all")
    canvas.create_rectangle(
        0,
        0,
        width,
        height,
        fill=CANVAS_BACKGROUND,
        outline="",
    )
    _draw_grid(canvas, width=width, height=height)
    _draw_header_card(canvas, width=width, plan=plan)

    for edge in plan.edges:
        canvas.create_line(
            edge.start.x,
            edge.start.y,
            edge.end.x,
            edge.end.y,
            fill="#d4dde7",
            width=8,
            capstyle="round",
            tags=("edge-underlay", f"edge-{edge.edge_id}"),
        )
        canvas.create_line(
            edge.start.x,
            edge.start.y,
            edge.end.x,
            edge.end.y,
            fill=edge.stroke_color,
            width=4 if edge.blocked else 3,
            arrow="last",
            arrowshape=(10, 12, 4),
            dash=(8, 6) if edge.blocked else (),
            capstyle="round",
            tags=("edge", f"edge-{edge.edge_id}"),
        )
        canvas.create_text(
            edge.midpoint.x,
            edge.midpoint.y - 10,
            text=edge.label if not edge.blocked else f"{edge.label} blocked",
            fill=BLOCKED if edge.blocked else TEXT_MUTED,
            font=("TkDefaultFont", 9, "bold"),
            tags=("edge-label", f"edge-label-{edge.edge_id}"),
        )

    for node in plan.nodes:
        canvas.create_oval(
            node.center.x - 13,
            node.center.y - 13,
            node.center.x + 13,
            node.center.y + 13,
            fill=node.fill_color,
            outline=node.outline_color,
            width=3,
            tags=("node", f"node-{node.node_id}"),
        )
        canvas.create_text(
            node.center.x,
            node.center.y - 26,
            text=f"N{node.node_id}",
            fill=TEXT_PRIMARY,
            font=("TkDefaultFont", 10, "bold"),
            tags=("node-label", f"node-label-{node.node_id}"),
        )
        canvas.create_text(
            node.center.x,
            node.center.y + 24,
            text=node.node_type.replace("_", " "),
            fill=TEXT_MUTED,
            font=("TkDefaultFont", 9),
            tags=("node-type", f"node-type-{node.node_id}"),
        )

    for vehicle in plan.vehicles:
        if vehicle.selected:
            canvas.create_oval(
                vehicle.center.x - 22,
                vehicle.center.y - 22,
                vehicle.center.x + 22,
                vehicle.center.y + 22,
                fill="",
                outline=SELECTION,
                width=4,
                tags=("vehicle-selection", f"vehicle-selection-{vehicle.vehicle_id}"),
            )

        canvas.create_oval(
            vehicle.center.x - 14,
            vehicle.center.y - 14,
            vehicle.center.x + 14,
            vehicle.center.y + 14,
            fill=vehicle.color,
            outline="#ffffff",
            width=3,
            tags=("vehicle", f"vehicle-{vehicle.vehicle_id}"),
        )
        canvas.create_text(
            vehicle.center.x,
            vehicle.center.y,
            text=str(vehicle.vehicle_id),
            fill="#ffffff",
            font=("TkDefaultFont", 10, "bold"),
            tags=("vehicle-id", f"vehicle-id-{vehicle.vehicle_id}"),
        )
        canvas.create_text(
            vehicle.center.x,
            vehicle.center.y + 26,
            text=f"{vehicle.label}  {vehicle.state_badge}",
            fill=TEXT_PRIMARY,
            font=("TkDefaultFont", 10, "bold"),
            tags=("vehicle-label", f"vehicle-label-{vehicle.vehicle_id}"),
        )


class GraphicalReplayViewer:
    """Tk replay viewer with clearer visual hierarchy and playback inspection."""

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
        self._synchronizing_timeline = False

        self.root = tk.Tk()
        self.root.title("Autonomous Ops Replay Viewer")
        self.root.configure(bg=PANEL_BACKGROUND)
        self.root.minsize(1100, 760)

        self._build_replay_layout()
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
        self._render_current_frame()

    def last_frame(self) -> None:
        self.controller.last_frame()
        self._render_current_frame()

    def jump_to_frame(self) -> None:
        try:
            frame_index = int(self.jump_var.get())
            self.controller.jump_to_frame(frame_index)
        except (TypeError, ValueError, IndexError):
            self.status_var.set(
                f"Invalid frame index {self.jump_var.get()}. "
                f"Use 0 through {self.controller.last_frame_index}."
            )
            return
        self._render_current_frame()

    def reset(self) -> None:
        self.controller.reset()
        self._render_current_frame()

    def run(self) -> None:
        self.root.mainloop()

    def _build_replay_layout(self) -> None:
        tk = self._tk

        controls = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        controls.pack(fill="x", padx=16, pady=(16, 8))

        for label, command in (
            ("Play", self.play),
            ("Pause", self.pause),
            ("First", self.first_frame),
            ("Previous", self.previous_frame),
            ("Next", self.next_frame),
            ("Last", self.last_frame),
            ("Reset", self.reset),
        ):
            tk.Button(controls, text=label, command=command).pack(side="left", padx=(0, 6))

        tk.Label(controls, text="Jump", bg=PANEL_BACKGROUND, fg=TEXT_SECONDARY).pack(
            side="left",
            padx=(12, 4),
        )
        self.jump_var = tk.StringVar(value="0")
        tk.Entry(controls, textvariable=self.jump_var, width=7).pack(side="left")
        tk.Button(controls, text="Go", command=self.jump_to_frame).pack(
            side="left",
            padx=(6, 12),
        )

        self.speed_var = tk.StringVar(value="1.0x")
        tk.Label(controls, text="Speed", bg=PANEL_BACKGROUND, fg=TEXT_SECONDARY).pack(
            side="left",
            padx=(0, 4),
        )
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
        tk.Label(
            controls,
            textvariable=self.status_var,
            bg=PANEL_BACKGROUND,
            fg=TEXT_PRIMARY,
            font=("TkDefaultFont", 10, "bold"),
        ).pack(side="right")

        timeline_frame = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        timeline_frame.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(
            timeline_frame,
            text="Timeline",
            bg=PANEL_BACKGROUND,
            fg=TEXT_SECONDARY,
        ).pack(anchor="w")
        self.timeline_var = tk.IntVar(value=0)
        self.timeline_scale = tk.Scale(
            timeline_frame,
            from_=0,
            to=self.controller.last_frame_index,
            orient="horizontal",
            showvalue=False,
            variable=self.timeline_var,
            command=self._on_timeline_change,
            resolution=1,
            troughcolor="#d7e3f0",
            activebackground=ACCENT,
            highlightthickness=0,
            bg=PANEL_BACKGROUND,
        )
        self.timeline_scale.pack(fill="x")

        content = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.canvas = tk.Canvas(
            content,
            width=self.canvas_width,
            height=self.canvas_height,
            background=CANVAS_BACKGROUND,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        sidebar = tk.Frame(
            content,
            width=320,
            bg=PANEL_BACKGROUND,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        sidebar.pack(side="right", fill="y", padx=(16, 0))
        sidebar.pack_propagate(False)

        self.inspector_headline_var = tk.StringVar()
        self.inspector_timeline_var = tk.StringVar()
        self.inspector_trigger_var = tk.StringVar()
        self.inspector_fleet_var = tk.StringVar()
        self.inspector_blocked_var = tk.StringVar()
        self.inspector_selection_title_var = tk.StringVar()
        self.inspector_selection_var = tk.StringVar()
        self.inspector_hint_var = tk.StringVar()
        for title, variable in (
            ("Overview", self.inspector_headline_var),
            ("Run", self.inspector_timeline_var),
            ("Trigger", self.inspector_trigger_var),
            ("Fleet", self.inspector_fleet_var),
            ("Blocked edges", self.inspector_blocked_var),
            ("Selection", self.inspector_selection_var),
            ("Hint", self.inspector_hint_var),
        ):
            self._add_sidebar_section(
                sidebar,
                title=title,
                variable=variable,
                title_variable=(
                    self.inspector_selection_title_var if title == "Selection" else None
                ),
            )

    def _add_sidebar_section(
        self,
        parent: Any,
        *,
        title: str,
        variable: Any,
        title_variable: Any | None = None,
    ) -> None:
        tk = self._tk
        section = tk.Frame(parent, bg=PANEL_BACKGROUND)
        section.pack(fill="x", padx=12, pady=10)
        tk.Label(
            section,
            text=title,
            bg=PANEL_BACKGROUND,
            fg=TEXT_MUTED,
            font=("TkDefaultFont", 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        if title_variable is not None:
            tk.Label(
                section,
                textvariable=title_variable,
                bg=PANEL_BACKGROUND,
                fg=TEXT_PRIMARY,
                font=("TkDefaultFont", 11, "bold"),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=(4, 2))
        tk.Label(
            section,
            textvariable=variable,
            bg=PANEL_BACKGROUND,
            fg=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=280,
        ).pack(fill="x", pady=(4, 0))

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
        inspector = build_frame_inspector(
            self.state,
            frame_index=status.frame_index,
            playback_state=status.playback_state,
            playback_speed=status.playback_speed,
        )
        self.inspector_headline_var.set(inspector.headline)
        self.inspector_timeline_var.set(inspector.timeline_text)
        self.inspector_trigger_var.set(inspector.trigger_text)
        self.inspector_fleet_var.set(inspector.fleet_text)
        self.inspector_blocked_var.set(inspector.blocked_text)
        self.inspector_selection_title_var.set(inspector.selection_title)
        self.inspector_selection_var.set(inspector.selection_details)
        self.inspector_hint_var.set(inspector.hint_text)
        self._set_timeline_value(status.frame_index)

    def _set_timeline_value(self, value: int) -> None:
        self._synchronizing_timeline = True
        try:
            self.timeline_var.set(value)
        finally:
            self._synchronizing_timeline = False

    def _on_speed_change(self) -> None:
        speed_text = self.speed_var.get().removesuffix("x")
        try:
            speed = float(speed_text)
        except ValueError:
            self.status_var.set(f"Invalid speed {self.speed_var.get()}.")
            return
        self.controller.set_playback_speed(speed)
        self._update_status()

    def _on_timeline_change(self, _value: str) -> None:
        if self._synchronizing_timeline:
            return
        self.controller.jump_to_frame(self.timeline_var.get())
        self._render_current_frame()

    def _on_close(self) -> None:
        self.pause()
        self.root.destroy()


class GraphicalLiveViewer:
    """Tk live viewer with inspector sidebar and canvas-driven actions."""

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
        self._current_plan: FrameRenderPlan | None = None

        self.root = tk.Tk()
        self.root.title("Autonomous Ops Live Viewer")
        self.root.configure(bg=PANEL_BACKGROUND)
        self.root.minsize(1150, 780)

        self._build_live_layout()
        self._render_current_state()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        self.root.mainloop()

    def refresh(self) -> None:
        self.controller.refresh()
        self.message_var.set("Refreshed the viewer from authoritative live session state.")
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

    def _build_live_layout(self) -> None:
        tk = self._tk

        controls = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        controls.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            controls,
            text="Canvas mode",
            bg=PANEL_BACKGROUND,
            fg=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 8))
        self.interaction_mode_var = tk.StringVar(value="select_vehicle")
        for mode, label in (
            ("select_vehicle", "Select"),
            ("assign_destination", "Assign"),
            ("reposition_vehicle", "Reposition"),
            ("block_edge", "Block edge"),
        ):
            tk.Radiobutton(
                controls,
                text=label,
                value=mode,
                variable=self.interaction_mode_var,
                bg=PANEL_BACKGROUND,
                fg=TEXT_PRIMARY,
                selectcolor=PANEL_BACKGROUND,
                activebackground=PANEL_BACKGROUND,
                command=self._render_current_state,
            ).pack(side="left", padx=(0, 8))

        tk.Button(controls, text="Refresh", command=self.refresh).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar()
        tk.Label(
            controls,
            textvariable=self.status_var,
            bg=PANEL_BACKGROUND,
            fg=TEXT_PRIMARY,
            font=("TkDefaultFont", 10, "bold"),
        ).pack(side="right")

        self.message_var = tk.StringVar()
        tk.Label(
            self.root,
            textvariable=self.message_var,
            bg=PANEL_BACKGROUND,
            fg="#92400e",
            anchor="w",
            justify="left",
            wraplength=1100,
        ).pack(fill="x", padx=16, pady=(0, 8))

        manual = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        manual.pack(fill="x", padx=16, pady=(0, 12))

        self.vehicle_var = tk.StringVar(value="")
        self.destination_var = tk.StringVar(value="")
        self.edge_var = tk.StringVar(value="")
        self.reposition_var = tk.StringVar(value="")
        for label_text, variable, button_text, command in (
            ("Vehicle", self.vehicle_var, "Select", self.select_vehicle),
            ("Destination", self.destination_var, "Assign", self.assign_destination),
            ("Edge", self.edge_var, "Block", self.block_edge),
            ("Reposition", self.reposition_var, "Move", self.reposition_vehicle),
        ):
            tk.Label(
                manual,
                text=label_text,
                bg=PANEL_BACKGROUND,
                fg=TEXT_SECONDARY,
            ).pack(side="left", padx=(0, 4))
            tk.Entry(manual, textvariable=variable, width=7).pack(side="left", padx=(0, 6))
            tk.Button(manual, text=button_text, command=command).pack(
                side="left",
                padx=(0, 12),
            )

        content = tk.Frame(self.root, bg=PANEL_BACKGROUND)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.canvas = tk.Canvas(
            content,
            width=self.canvas_width,
            height=self.canvas_height,
            background=CANVAS_BACKGROUND,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        sidebar = tk.Frame(
            content,
            width=340,
            bg=PANEL_BACKGROUND,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
        )
        sidebar.pack(side="right", fill="y", padx=(16, 0))
        sidebar.pack_propagate(False)

        self.live_overview_var = tk.StringVar()
        self.live_trigger_var = tk.StringVar()
        self.live_fleet_var = tk.StringVar()
        self.live_blocked_var = tk.StringVar()
        self.live_selection_title_var = tk.StringVar()
        self.live_selection_var = tk.StringVar()
        self.live_hint_var = tk.StringVar()
        for title, variable in (
            ("Overview", self.live_overview_var),
            ("Trigger", self.live_trigger_var),
            ("Fleet", self.live_fleet_var),
            ("Blocked edges", self.live_blocked_var),
            ("Selection", self.live_selection_var),
            ("Interaction hint", self.live_hint_var),
        ):
            self._add_sidebar_section(
                sidebar,
                title=title,
                variable=variable,
                title_variable=(
                    self.live_selection_title_var if title == "Selection" else None
                ),
            )

    def _add_sidebar_section(
        self,
        parent: Any,
        *,
        title: str,
        variable: Any,
        title_variable: Any | None = None,
    ) -> None:
        tk = self._tk
        section = tk.Frame(parent, bg=PANEL_BACKGROUND)
        section.pack(fill="x", padx=12, pady=10)
        tk.Label(
            section,
            text=title,
            bg=PANEL_BACKGROUND,
            fg=TEXT_MUTED,
            font=("TkDefaultFont", 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        if title_variable is not None:
            tk.Label(
                section,
                textvariable=title_variable,
                bg=PANEL_BACKGROUND,
                fg=TEXT_PRIMARY,
                font=("TkDefaultFont", 11, "bold"),
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=(4, 2))
        tk.Label(
            section,
            textvariable=variable,
            bg=PANEL_BACKGROUND,
            fg=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=300,
        ).pack(fill="x", pady=(4, 0))

    def _apply_action_from_entry(
        self,
        field: Any,
        action_builder: Callable[[int], LiveViewerAction],
    ) -> None:
        try:
            value = int(field.get())
            result = self.controller.apply_action(action_builder(value))
        except (TypeError, ValueError, LiveViewerActionValidationError) as exc:
            self.message_var.set(str(exc))
            return

        self._set_result_message(result.action.action_type, result.selected_vehicle_id)
        self._render_current_state()

    def _on_canvas_click(self, event: Any) -> None:
        if self._current_plan is None:
            return

        action = resolve_live_click_action(
            self._current_plan,
            CanvasPoint(x=event.x, y=event.y),
            interaction_mode=self.interaction_mode_var.get(),
            selected_vehicle_id=self.controller.selected_vehicle_id,
        )
        if action is None:
            self.message_var.set(
                _interaction_miss_message(
                    self.interaction_mode_var.get(),
                    self.controller.selected_vehicle_id,
                )
            )
            return

        try:
            result = self.controller.apply_action(action)
        except LiveViewerActionValidationError as exc:
            self.message_var.set(str(exc))
            return

        self._set_result_message(result.action.action_type, result.selected_vehicle_id)
        self._render_current_state()

    def _set_result_message(
        self,
        action_type: str,
        selected_vehicle_id: int | None,
    ) -> None:
        if action_type == "select_vehicle":
            self.message_var.set(f"Selected vehicle V{selected_vehicle_id}.")
            return
        if action_type == "assign_destination":
            self.message_var.set("Assigned destination through the live session command surface.")
            return
        if action_type == "reposition_vehicle":
            self.message_var.set("Repositioned the selected vehicle through the live session.")
            return
        self.message_var.set("Blocked the selected edge through the live session.")

    def _render_current_state(self) -> None:
        state = self.controller.visualization_state
        frame_index = len(state.frames) - 1
        self._current_plan = build_frame_render_plan(
            state,
            frame_index=frame_index,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            selected_vehicle_id=self.controller.selected_vehicle_id,
        )
        render_frame_plan_to_canvas(self.canvas, self._current_plan)

        current_frame = state.frames[frame_index]
        selected_vehicle_text = (
            "none"
            if self.controller.selected_vehicle_id is None
            else f"V{self.controller.selected_vehicle_id}"
        )
        self.status_var.set(
            f"Live time {current_frame.timestamp_s:.2f}s  Selected {selected_vehicle_text}"
        )

        inspector = build_frame_inspector(
            state,
            frame_index=frame_index,
            playback_state="live",
            playback_speed=1.0,
            selected_vehicle_id=self.controller.selected_vehicle_id,
            interaction_mode=self.interaction_mode_var.get(),
        )
        self.live_overview_var.set(inspector.headline)
        self.live_trigger_var.set(inspector.trigger_text)
        self.live_fleet_var.set(inspector.fleet_text)
        self.live_blocked_var.set(inspector.blocked_text)
        self.live_selection_title_var.set(inspector.selection_title)
        self.live_selection_var.set(inspector.selection_details)
        self.live_hint_var.set(inspector.hint_text)

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
    positions = {node.node_id: node.position for node in map_surface.nodes}

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
    return VEHICLE_STATE_COLORS.get(operational_state, "#7c3aed")


def _node_fill_color(node_type: str) -> str:
    return NODE_TYPE_COLORS.get(node_type, "#334155")


def _midpoint(start: CanvasPoint, end: CanvasPoint) -> CanvasPoint:
    return CanvasPoint(x=(start.x + end.x) / 2.0, y=(start.y + end.y) / 2.0)


def _draw_grid(canvas: Any, *, width: int, height: int) -> None:
    step_x = max(80, width // 8)
    step_y = max(80, height // 6)
    for x in range(step_x, width, step_x):
        canvas.create_line(x, 0, x, height, fill="#e5edf5", width=1, tags=("grid",))
    for y in range(step_y, height, step_y):
        canvas.create_line(0, y, width, y, fill="#e5edf5", width=1, tags=("grid",))


def _draw_header_card(canvas: Any, *, width: int, plan: FrameRenderPlan) -> None:
    canvas.create_rectangle(
        20,
        18,
        min(width - 20, 500),
        82,
        fill="#ffffff",
        outline=PANEL_BORDER,
        width=1,
        tags=("header-card",),
    )
    canvas.create_text(
        36,
        34,
        anchor="nw",
        text=plan.frame_label,
        fill=TEXT_PRIMARY,
        font=("TkDefaultFont", 12, "bold"),
        tags=("frame-label",),
    )
    canvas.create_text(
        36,
        58,
        anchor="nw",
        text=plan.frame_subtitle,
        fill=TEXT_SECONDARY,
        font=("TkDefaultFont", 10),
        tags=("frame-subtitle",),
    )


def _find_nearest_vehicle(
    plan: FrameRenderPlan,
    point: CanvasPoint,
    *,
    max_distance_px: float,
) -> CanvasHitTarget | None:
    candidates = [
        CanvasHitTarget(
            target_type="vehicle",
            target_id=vehicle.vehicle_id,
            distance_px=_distance(point, vehicle.center),
        )
        for vehicle in plan.vehicles
    ]
    return _pick_hit_target(candidates, max_distance_px=max_distance_px)


def _find_nearest_node(
    plan: FrameRenderPlan,
    point: CanvasPoint,
    *,
    max_distance_px: float,
) -> CanvasHitTarget | None:
    candidates = [
        CanvasHitTarget(
            target_type="node",
            target_id=node.node_id,
            distance_px=_distance(point, node.center),
        )
        for node in plan.nodes
    ]
    return _pick_hit_target(candidates, max_distance_px=max_distance_px)


def _find_nearest_edge(
    plan: FrameRenderPlan,
    point: CanvasPoint,
    *,
    max_distance_px: float,
) -> CanvasHitTarget | None:
    candidates = [
        CanvasHitTarget(
            target_type="edge",
            target_id=edge.edge_id,
            distance_px=_distance_to_segment(point, edge.start, edge.end),
        )
        for edge in plan.edges
    ]
    return _pick_hit_target(candidates, max_distance_px=max_distance_px)


def _pick_hit_target(
    candidates: list[CanvasHitTarget],
    *,
    max_distance_px: float,
) -> CanvasHitTarget | None:
    viable = [
        candidate
        for candidate in candidates
        if candidate.distance_px <= max_distance_px
    ]
    if not viable:
        return None
    return min(viable, key=lambda candidate: (candidate.distance_px, candidate.target_id))


def _distance(point_a: CanvasPoint, point_b: CanvasPoint) -> float:
    return math.hypot(point_a.x - point_b.x, point_a.y - point_b.y)


def _distance_to_segment(
    point: CanvasPoint,
    start: CanvasPoint,
    end: CanvasPoint,
) -> float:
    segment_dx = end.x - start.x
    segment_dy = end.y - start.y
    if segment_dx == 0.0 and segment_dy == 0.0:
        return _distance(point, start)

    projection = (
        ((point.x - start.x) * segment_dx) + ((point.y - start.y) * segment_dy)
    ) / ((segment_dx * segment_dx) + (segment_dy * segment_dy))
    clamped = max(0.0, min(1.0, projection))
    closest = CanvasPoint(
        x=start.x + (segment_dx * clamped),
        y=start.y + (segment_dy * clamped),
    )
    return _distance(point, closest)


def _interaction_mode_hint(
    interaction_mode: str | None,
    selected_vehicle_id: int | None,
) -> str:
    if interaction_mode == "select_vehicle":
        return "Click a vehicle on the map to select it."
    if interaction_mode == "assign_destination":
        if selected_vehicle_id is None:
            return "Select a vehicle first, then click a destination node."
        return f"Click a node to assign a destination to V{selected_vehicle_id}."
    if interaction_mode == "reposition_vehicle":
        if selected_vehicle_id is None:
            return "Select a vehicle first, then click its current or adjacent node."
        return f"Click a node to reposition V{selected_vehicle_id} within bounded rules."
    if interaction_mode == "block_edge":
        return "Click an edge segment to block it through the live session."
    return "Use the viewer controls to inspect the scenario."


def _interaction_miss_message(
    interaction_mode: str,
    selected_vehicle_id: int | None,
) -> str:
    if interaction_mode in {"assign_destination", "reposition_vehicle"} and (
        selected_vehicle_id is None
    ):
        return "Select a vehicle before using node-based actions."
    if interaction_mode == "block_edge":
        return "Click closer to an edge to block it."
    if interaction_mode == "select_vehicle":
        return "Click directly on a vehicle to select it."
    return "Click directly on a node to apply that action."


if __name__ == "__main__":
    raise SystemExit(main())
