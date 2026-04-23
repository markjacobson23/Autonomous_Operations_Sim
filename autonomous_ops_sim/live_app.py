from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import quote, urlparse
import webbrowser

from autonomous_ops_sim.api import (
    apply_command_with_result,
    build_live_session_bundle,
    live_session_bundle_to_dict,
    SimulationCommandResult,
    simulation_command_result_to_dict,
)
from autonomous_ops_sim.authoring import (
    apply_geometry_edit_transaction,
    export_scenario_json,
    geometry_edit_transaction_from_dict,
    validate_geometry_edit_transaction,
    validation_message_to_dict,
)
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    ClearTemporaryHazardCommand,
    BlockEdgeCommand,
    DeclareTemporaryHazardCommand,
    InjectJobCommand,
    RemoveVehicleCommand,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SimulationCommand,
    SimulationEngine,
    SpawnVehicleCommand,
    UnblockEdgeCommand,
)
from autonomous_ops_sim.simulation.commands import job_from_dict
from autonomous_ops_sim.simulation.commands import command_to_dict
from autonomous_ops_sim.simulation.scenario_executor import build_scenario_engine
from autonomous_ops_sim.simulation.live_session import session_advance_to_dict
from autonomous_ops_sim.world import build_world_model_surface, world_model_surface_to_dict
from autonomous_ops_sim.visualization import export_serious_viewer_html
from autonomous_ops_sim.visualization.command_center import RoutePreviewRequest
from autonomous_ops_sim.visualization.state import VehicleSurfaceState


DEFAULT_LIVE_OUTPUT_DIRECTORY = Path("live_output")
DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY = Path("frontend/frontend_v2/dist")
DEFAULT_LIVE_HOST = "127.0.0.1"
DEFAULT_LIVE_SESSION_STEP_SECONDS = 0.5
UNITY_BRIDGE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class LiveAppArtifacts:
    """Stable file inventory for one prepared Step 42 live app launch."""

    output_directory: Path
    scenario_path: Path
    working_scenario_path: Path
    live_session_bundle_path: Path
    launch_path: Path
    launch_mode: str
    launch_relative_url: str


@dataclass(frozen=True)
class LiveAppLaunchResult:
    """Resolved launch target for one prepared live app run."""

    artifacts: LiveAppArtifacts
    launch_target: str
    served: bool


@dataclass
class LiveSessionRuntime:
    """Mutable live session state backing the Frontend v2 command transport."""

    artifacts: LiveAppArtifacts
    session: LiveSimulationSession
    play_state: str = "paused"
    pending_route_commands: list[AssignVehicleDestinationCommand] = field(default_factory=list)
    latest_unity_telemetry_by_vehicle_id: dict[int, dict[str, object]] = field(
        default_factory=dict
    )
    unity_telemetry_history: list[dict[str, object]] = field(default_factory=list)
    playback_thread: threading.Thread | None = None
    playback_stop_event: threading.Event = field(default_factory=threading.Event)
    lock: threading.RLock = field(default_factory=threading.RLock)

    @classmethod
    def from_artifacts(cls, artifacts: LiveAppArtifacts) -> "LiveSessionRuntime":
        scenario = load_scenario(artifacts.working_scenario_path)
        session = LiveSimulationSession(build_scenario_engine(scenario))
        return cls(artifacts=artifacts, session=session)

    def refresh_bundle(
        self,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        with self.lock:
            bundle = _build_live_bundle_record(
                session=self.session,
                source_scenario_path=self.artifacts.scenario_path,
                working_scenario_path=self.artifacts.working_scenario_path,
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
                play_state=self.play_state,
                pending_route_commands=self.pending_route_commands,
            )
            self._write_bundle(bundle)
            return bundle

    def build_unity_bootstrap(self) -> dict[str, object]:
        """Build the Unity-facing bootstrap projection without mutating runtime truth."""

        with self.lock:
            return _build_unity_bootstrap_record(
                session=self.session,
                source_scenario_path=self.artifacts.scenario_path,
                working_scenario_path=self.artifacts.working_scenario_path,
                pending_route_commands=self.pending_route_commands,
                latest_unity_telemetry_by_vehicle_id=self.latest_unity_telemetry_by_vehicle_id,
            )

    def record_unity_telemetry(
        self,
        telemetry_samples: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        """Ingest Unity telemetry through one dedicated bridge update path."""

        with self.lock:
            normalized_samples = [
                _normalize_unity_telemetry_sample(sample)
                for sample in telemetry_samples
            ]
            for sample in normalized_samples:
                vehicle_id = int(sample["vehicle_id"])
                self.latest_unity_telemetry_by_vehicle_id[vehicle_id] = sample
            self.unity_telemetry_history.extend(normalized_samples)
            return {
                "ok": True,
                "telemetry_count": len(self.unity_telemetry_history),
                "received_samples": normalized_samples,
                "latest_telemetry_by_vehicle_id": [
                    self.latest_unity_telemetry_by_vehicle_id[vehicle_id]
                    for vehicle_id in sorted(self.latest_unity_telemetry_by_vehicle_id)
                ],
            }

    def apply_command(
        self,
        command: SimulationCommand,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> tuple[dict[str, object], dict[str, object]]:
        with self.lock:
            if isinstance(command, AssignVehicleDestinationCommand):
                self.session.controller.validate(command)
                self._queue_route_command(command)
                result = _build_live_command_result(
                    engine=self.session.engine,
                    command=command,
                )
            else:
                result = apply_command_with_result(self.session, command)
            bundle = self._refresh_locked(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )
            return simulation_command_result_to_dict(result), bundle

    def advance_session(
        self,
        *,
        delta_s: float,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> tuple[dict[str, object], dict[str, object]]:
        with self.lock:
            started_at_s = self.session.engine.simulated_time_s
            self._flush_pending_route_commands()
            target_time_s = started_at_s + delta_s
            if self.session.engine.simulated_time_s < target_time_s:
                self.session.engine.run(target_time_s)
            record = self.session._append_progress_record(
                started_at_s=started_at_s,
                completed_at_s=self.session.engine.simulated_time_s,
            )
            bundle = self._refresh_locked(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )
            return session_advance_to_dict(record), bundle

    def set_play_state(
        self,
        play_state: str,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        if play_state not in {"paused", "playing"}:
            raise ValueError(f"Unknown play_state: {play_state}")
        if play_state == "playing":
            return self.start_playback(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )
        return self.pause_playback(
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        )

    def start_playback(
        self,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        with self.lock:
            self.play_state = "playing"
            playback_thread = self.playback_thread
            if playback_thread is None or not playback_thread.is_alive():
                self.playback_stop_event = threading.Event()
                self.playback_thread = threading.Thread(
                    target=self._run_playback_loop,
                    name="autonomous_ops_live_session_playback",
                    daemon=True,
                )
                self.playback_thread.start()
            return self._refresh_locked(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )

    def pause_playback(
        self,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        playback_thread: threading.Thread | None = None
        with self.lock:
            self.play_state = "paused"
            self.playback_stop_event.set()
            playback_thread = self.playback_thread
        if playback_thread is not None and playback_thread.is_alive():
            playback_thread.join()
        with self.lock:
            if self.playback_thread is playback_thread and (
                playback_thread is None or not playback_thread.is_alive()
            ):
                self.playback_thread = None
            return self._refresh_locked(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )

    def reload_working_scenario(
        self,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        self.pause_playback()
        with self.lock:
            scenario = load_scenario(self.artifacts.working_scenario_path)
            self.session = LiveSimulationSession(build_scenario_engine(scenario))
            self.play_state = "paused"
            self.pending_route_commands = []
            return self._refresh_locked(
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )

    def _refresh_locked(
        self,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> dict[str, object]:
        bundle = _build_live_bundle_record(
            session=self.session,
            source_scenario_path=self.artifacts.scenario_path,
            working_scenario_path=self.artifacts.working_scenario_path,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
            play_state=self.play_state,
            pending_route_commands=self.pending_route_commands,
        )
        self._write_bundle(bundle)
        return bundle

    def _write_bundle(self, bundle: dict[str, object]) -> None:
        self.artifacts.live_session_bundle_path.write_text(
            json.dumps(bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _queue_route_command(
        self,
        command: AssignVehicleDestinationCommand,
    ) -> None:
        self.pending_route_commands = [
            queued_command
            for queued_command in self.pending_route_commands
            if queued_command.vehicle_id != command.vehicle_id
        ]
        self.pending_route_commands.append(command)

    def _flush_pending_route_commands(self) -> None:
        pending_commands = self.pending_route_commands
        if not pending_commands:
            return
        self.pending_route_commands = []
        for command in pending_commands:
            self.session.apply(command)

    def _run_playback_loop(self) -> None:
        current_thread = threading.current_thread()
        try:
            while not self.playback_stop_event.wait(DEFAULT_LIVE_SESSION_STEP_SECONDS):
                self.advance_session(delta_s=DEFAULT_LIVE_SESSION_STEP_SECONDS)
        except Exception:
            with self.lock:
                self.play_state = "paused"
                self.playback_stop_event.set()
            self._refresh_locked()
        finally:
            with self.lock:
                if self.playback_thread is current_thread:
                    self.playback_thread = None


class LiveAppServer:
    """Serve one prepared live app directory for browser access."""

    def __init__(
        self,
        directory: Path,
        *,
        artifacts: LiveAppArtifacts,
        runtime: LiveSessionRuntime | None = None,
        host: str = DEFAULT_LIVE_HOST,
        port: int = 0,
    ) -> None:
        session_runtime = runtime or LiveSessionRuntime.from_artifacts(artifacts)
        self._runtime = session_runtime
        handler = partial(
            LiveAppRequestHandler,
            directory=str(directory),
            artifacts=artifacts,
            runtime=session_runtime,
        )
        self._server = ThreadingHTTPServer((host, port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="autonomous_ops_live_app_server",
            daemon=True,
        )

    @property
    def host(self) -> str:
        return str(self._server.server_address[0])

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._runtime.pause_playback()
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=1.0)


class LiveAppRequestHandler(SimpleHTTPRequestHandler):
    """Serve the live app plus the small Step 49/50 authoring API."""

    def __init__(
        self,
        *args,
        directory: str,
        artifacts: LiveAppArtifacts,
        runtime: LiveSessionRuntime,
        **kwargs,
    ) -> None:
        self._artifacts = artifacts
        self._runtime = runtime
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/authoring/reload":
            self._write_json_response(
                200,
                {
                    "ok": True,
                    "bundle": self._runtime.reload_working_scenario(),
                    "working_scenario_path": str(self._artifacts.working_scenario_path),
                },
            )
            return
        if parsed.path == "/api/unity/bootstrap":
            self._write_json_response(
                200,
                {
                    "ok": True,
                    "bootstrap": self._runtime.build_unity_bootstrap(),
                    "working_scenario_path": str(self._artifacts.working_scenario_path),
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/authoring/validate",
            "/api/authoring/save",
            "/api/live/preview",
            "/api/live/command",
            "/api/live/session/control",
            "/api/unity/telemetry",
        }:
            self.send_error(404, "Unknown live authoring endpoint.")
            return

        try:
            payload = self._read_json_payload()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        if parsed.path == "/api/authoring/validate":
            self._handle_authoring_validate(payload)
            return
        if parsed.path == "/api/authoring/save":
            self._handle_authoring_save(payload)
            return
        if parsed.path == "/api/live/preview":
            self._handle_live_route_preview(payload)
            return
        if parsed.path == "/api/live/command":
            self._handle_live_command(payload)
            return
        if parsed.path == "/api/live/session/control":
            self._handle_live_session_control(payload)
            return
        if parsed.path == "/api/unity/telemetry":
            self._handle_unity_telemetry(payload)
            return

    def _read_json_payload(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Authoring request payload must be a JSON object.")
        return payload

    def _write_json_response(self, status_code: int, payload: dict[str, object]) -> None:
        response_body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def _handle_authoring_validate(self, payload: dict[str, object]) -> None:
        try:
            transaction = geometry_edit_transaction_from_dict(payload)
        except ValueError as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        scenario_data = _read_json_object(self._artifacts.working_scenario_path)
        messages = validate_geometry_edit_transaction(scenario_data, transaction)
        self._write_json_response(
            200,
            {
                "ok": len(messages) == 0,
                "validation_messages": [
                    validation_message_to_dict(message) for message in messages
                ],
            },
        )

    def _handle_authoring_save(self, payload: dict[str, object]) -> None:
        try:
            transaction = geometry_edit_transaction_from_dict(payload)
        except ValueError as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        scenario_data = _read_json_object(self._artifacts.working_scenario_path)
        messages = validate_geometry_edit_transaction(scenario_data, transaction)
        if messages:
            self._write_json_response(
                200,
                {
                    "ok": False,
                    "validation_messages": [
                        validation_message_to_dict(message) for message in messages
                    ],
                },
            )
            return

        updated_scenario = apply_geometry_edit_transaction(scenario_data, transaction)
        self._artifacts.working_scenario_path.write_text(
            export_scenario_json(updated_scenario),
            encoding="utf-8",
        )
        refreshed_bundle = self._runtime.reload_working_scenario()
        self._write_json_response(
            200,
            {
                "ok": True,
                "bundle": refreshed_bundle,
                "validation_messages": [],
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )

    def _handle_live_command(self, payload: dict[str, object]) -> None:
        try:
            commands = _simulation_commands_from_payload(payload)
            selected_vehicle_ids, route_preview_requests = _selection_requests_from_payload(
                payload
            )
        except (KeyError, TypeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        command_results: list[dict[str, object]] = []
        bundle: dict[str, object] | None = None
        for command in commands:
            command_result, bundle = self._runtime.apply_command(
                command,
                selected_vehicle_ids=selected_vehicle_ids,
                route_preview_requests=route_preview_requests,
            )
            command_results.append(command_result)
        assert bundle is not None
        if len(command_results) == 1:
            response_command_result: dict[str, object] | list[dict[str, object]] = command_results[0]
        else:
            response_command_result = command_results
        self._write_json_response(
            200,
            {
                "ok": all(result["status"] == "accepted" for result in command_results),
                "command_result": response_command_result,
                "command_results": command_results,
                "bundle": bundle,
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )

    def _handle_live_route_preview(self, payload: dict[str, object]) -> None:
        try:
            selected_vehicle_ids, route_preview_requests = _selection_requests_from_payload(
                payload
            )
            if route_preview_requests and not selected_vehicle_ids:
                selected_vehicle_ids = tuple(
                    request.vehicle_id for request in route_preview_requests
                )
            if not route_preview_requests:
                vehicle_ids = _payload_int_list(payload, "vehicle_ids")
                destination_node_id = _payload_int(payload, "destination_node_id")
                preview_vehicle_ids = vehicle_ids
                if not preview_vehicle_ids:
                    preview_vehicle_ids = (_payload_int(payload, "vehicle_id"),)
                route_preview_requests = tuple(
                    RoutePreviewRequest(
                        vehicle_id=preview_vehicle_id,
                        destination_node_id=destination_node_id,
                    )
                    for preview_vehicle_id in preview_vehicle_ids
                )
                if not selected_vehicle_ids:
                    selected_vehicle_ids = preview_vehicle_ids
        except (KeyError, TypeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        bundle = self._runtime.refresh_bundle(
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        )
        command_center = bundle.get("command_center")
        if not isinstance(command_center, dict):
            self._write_json_response(
                500,
                {
                    "ok": False,
                    "message": "Live bundle did not include command_center preview state.",
                    "validation_messages": [],
                },
            )
            return
        maybe_route_previews = command_center.get("route_previews", [])
        if not isinstance(maybe_route_previews, list) or len(maybe_route_previews) != len(
            route_preview_requests
        ):
            self._write_json_response(
                500,
                {
                    "ok": False,
                    "message": "Live bundle did not serialize route previews for every request.",
                    "validation_messages": [],
                },
            )
            return
        self._write_json_response(
            200,
            {
                "ok": True,
                "bundle": bundle,
                "route_previews": maybe_route_previews,
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )

    def _handle_live_session_control(self, payload: dict[str, object]) -> None:
        action = str(payload.get("action", "")).strip().lower()
        try:
            selected_vehicle_ids, route_preview_requests = _selection_requests_from_payload(
                payload
            )
            if action == "step":
                with self._runtime.lock:
                    if self._runtime.play_state == "playing":
                        self._write_json_response(
                            409,
                            {
                                "ok": False,
                                "message": "Cannot step while the session is playing.",
                                "validation_messages": [],
                            },
                        )
                        return
                delta_s_value = payload.get("delta_s", DEFAULT_LIVE_SESSION_STEP_SECONDS)
                if not isinstance(delta_s_value, (int, float, str)):
                    raise TypeError("delta_s must be numeric")
                delta_s = float(delta_s_value)
                session_advance, bundle = self._runtime.advance_session(
                    delta_s=delta_s,
                    selected_vehicle_ids=selected_vehicle_ids,
                    route_preview_requests=route_preview_requests,
                )
                self._write_json_response(
                    200,
                    {
                        "ok": True,
                        "session_advance": session_advance,
                        "bundle": bundle,
                        "working_scenario_path": str(
                            self._artifacts.working_scenario_path
                        ),
                    },
                )
                return
            if action in {"play", "pause"}:
                bundle = self._runtime.set_play_state(
                    "playing" if action == "play" else "paused",
                    selected_vehicle_ids=selected_vehicle_ids,
                    route_preview_requests=route_preview_requests,
                )
                self._write_json_response(
                    200,
                    {
                        "ok": True,
                        "bundle": bundle,
                        "working_scenario_path": str(
                            self._artifacts.working_scenario_path
                        ),
                    },
                )
                return
        except (TypeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        self._write_json_response(
            400,
            {
                "ok": False,
                "message": f"Unknown session control action: {action}",
                "validation_messages": [
                    {
                        "severity": "error",
                        "code": "invalid_request",
                        "message": f"Unknown session control action: {action}",
                    }
                ],
            },
        )

    def _handle_unity_telemetry(self, payload: dict[str, object]) -> None:
        try:
            telemetry_samples = _unity_telemetry_samples_from_payload(payload)
        except (KeyError, TypeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [
                        {
                            "severity": "error",
                            "code": "invalid_request",
                            "message": str(exc),
                        }
                    ],
                },
            )
            return

        response = self._runtime.record_unity_telemetry(telemetry_samples)
        self._write_json_response(
            200,
            {
                "ok": True,
                "bridge": {
                    "schema_version": UNITY_BRIDGE_SCHEMA_VERSION,
                    "transport": "http_json",
                    "authority": "python",
                    "telemetry_endpoint": "/api/unity/telemetry",
                    "bootstrap_endpoint": "/api/unity/bootstrap",
                },
                "telemetry": response,
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )


def export_live_app_artifacts(
    *,
    scenario_path: str | Path,
    output_directory: str | Path = DEFAULT_LIVE_OUTPUT_DIRECTORY,
    frontend_dist_directory: str | Path = DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY,
) -> LiveAppArtifacts:
    """Prepare the live-session bundle and launch surface for Frontend v2."""

    scenario_file = Path(scenario_path)
    output_root = Path(output_directory)
    output_root.mkdir(parents=True, exist_ok=True)

    working_scenario_path = output_root / "editable_scenario.json"
    shutil.copyfile(scenario_file, working_scenario_path)

    live_session_bundle_path = output_root / "live_session_bundle.json"
    initial_session = LiveSessionRuntime.from_artifacts(
        LiveAppArtifacts(
            output_directory=output_root,
            scenario_path=scenario_file,
            working_scenario_path=working_scenario_path,
            live_session_bundle_path=live_session_bundle_path,
            launch_path=output_root / "placeholder",
            launch_mode="frontend_dist",
            launch_relative_url="/",
        )
    )
    live_session_bundle_path.write_text(
        json.dumps(
            _build_live_bundle_record(
                session=initial_session.session,
                source_scenario_path=scenario_file,
                working_scenario_path=working_scenario_path,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    frontend_dist_root = Path(frontend_dist_directory)
    frontend_index = frontend_dist_root / "index.html"
    if frontend_index.exists():
        copied_frontend_root = output_root / "frontend_v2"
        shutil.copytree(frontend_dist_root, copied_frontend_root, dirs_exist_ok=True)
        return LiveAppArtifacts(
            output_directory=output_root,
            scenario_path=scenario_file,
            working_scenario_path=working_scenario_path,
            live_session_bundle_path=live_session_bundle_path,
            launch_path=copied_frontend_root / "index.html",
            launch_mode="frontend_dist",
            launch_relative_url=(f"/frontend_v2/index.html?bundle={quote('/live_session_bundle.json')}"),
        )

    launch_path = output_root / "live_session.viewer.html"
    export_serious_viewer_html(
        _build_live_bundle_record(
            session=initial_session.session,
            source_scenario_path=scenario_file,
            working_scenario_path=working_scenario_path,
        ),
        launch_path,
        title=f"Autonomous Ops Live Session ({load_scenario(scenario_file).name})",
    )
    return LiveAppArtifacts(
        output_directory=output_root,
        scenario_path=scenario_file,
        working_scenario_path=working_scenario_path,
        live_session_bundle_path=live_session_bundle_path,
        launch_path=launch_path,
        launch_mode="standalone_viewer_html",
        launch_relative_url="/live_session.viewer.html",
    )


def launch_live_app(
    artifacts: LiveAppArtifacts,
    *,
    open_browser: bool = True,
    host: str = DEFAULT_LIVE_HOST,
    port: int = 0,
    serve_seconds: float | None = None,
) -> LiveAppLaunchResult:
    """Open the prepared live app using the best available launch path."""

    if artifacts.launch_mode == "frontend_dist":
        server = LiveAppServer(
            artifacts.output_directory,
            artifacts=artifacts,
            host=host,
            port=port,
        )
        server.start()
        launch_url = build_live_app_url(artifacts, host=server.host, port=server.port)
        if open_browser:
            webbrowser.open(launch_url)
        if serve_seconds is None:
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                server.stop()
        else:
            try:
                time.sleep(max(0.0, serve_seconds))
            finally:
                server.stop()
        return LiveAppLaunchResult(
            artifacts=artifacts,
            launch_target=launch_url,
            served=True,
        )

    launch_target = artifacts.launch_path.resolve().as_uri()
    if open_browser:
        webbrowser.open(launch_target)
    return LiveAppLaunchResult(
        artifacts=artifacts,
        launch_target=launch_target,
        served=False,
    )


def build_live_app_url(artifacts: LiveAppArtifacts, *, host: str, port: int) -> str:
    """Return the browser URL for one served live app artifact set."""

    return f"http://{host}:{port}{artifacts.launch_relative_url}"


def _build_live_bundle_record(
    *,
    session: LiveSimulationSession,
    source_scenario_path: Path,
    working_scenario_path: Path,
    selected_vehicle_ids: tuple[int, ...] | list[int] = (),
    route_preview_requests: tuple[RoutePreviewRequest, ...]
    | list[RoutePreviewRequest] = (),
    play_state: str = "paused",
    pending_route_commands: tuple[AssignVehicleDestinationCommand, ...]
    | list[AssignVehicleDestinationCommand] = (),
) -> dict[str, object]:
    bundle = live_session_bundle_to_dict(
        build_live_session_bundle(
            session,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        )
    )
    if pending_route_commands:
        recent_commands = bundle.get("command_center", {}).get("recent_commands")
        if isinstance(recent_commands, list):
            recent_commands.extend(
                command_to_dict(command) for command in pending_route_commands
            )
    bundle["authoring"] = {
        "mode": "live_geometry_editing",
        "save_endpoint": "/api/authoring/save",
        "reload_endpoint": "/api/authoring/reload",
        "validate_endpoint": "/api/authoring/validate",
        "source_scenario_path": str(source_scenario_path),
        "working_scenario_path": str(working_scenario_path),
        "editable_node_count": len(bundle.get("map_surface", {}).get("nodes", [])),
        "editable_road_count": len(bundle.get("render_geometry", {}).get("roads", [])),
        "editable_area_count": len(bundle.get("render_geometry", {}).get("areas", [])),
    }
    bundle["session_control"] = {
        "play_state": play_state,
        "step_seconds": DEFAULT_LIVE_SESSION_STEP_SECONDS,
        "route_preview_endpoint": "/api/live/preview",
        "command_endpoint": "/api/live/command",
        "session_control_endpoint": "/api/live/session/control",
        "pending_route_commands": [
            command_to_dict(command) for command in pending_route_commands
        ],
    }
    return bundle


def _build_unity_bootstrap_record(
    *,
    session: LiveSimulationSession,
    source_scenario_path: Path,
    working_scenario_path: Path,
    pending_route_commands: tuple[AssignVehicleDestinationCommand, ...]
    | list[AssignVehicleDestinationCommand] = (),
    latest_unity_telemetry_by_vehicle_id: dict[int, dict[str, object]] | None = None,
) -> dict[str, object]:
    live_bundle = _build_live_bundle_record(
        session=session,
        source_scenario_path=source_scenario_path,
        working_scenario_path=working_scenario_path,
        pending_route_commands=pending_route_commands,
    )
    bootstrap = {
        "metadata": {
            "api_version": live_bundle["metadata"]["api_version"],
            "surface_name": "unity_bootstrap",
            "bridge_schema_version": UNITY_BRIDGE_SCHEMA_VERSION,
            "transport": "http_json",
        },
        "authority": {
            "runtime_owner": "python",
            "motion_authority": "python",
        },
        "session": {
            "seed": live_bundle["seed"],
            "simulated_time_s": live_bundle["simulated_time_s"],
            "play_state": live_bundle["session_control"]["play_state"],
        },
        "world": {
            "map_surface": live_bundle["map_surface"],
            "render_geometry": live_bundle["render_geometry"],
            "world_model": world_model_surface_to_dict(
                build_world_model_surface(session.engine.map)
            ),
        },
        "runtime_vehicle_snapshot": live_bundle["snapshot"]["vehicles"],
        "vehicle_identity_map": _unity_vehicle_identity_map(session),
        "pending_route_intents": [
            command_to_dict(command) for command in pending_route_commands
        ],
        "bridge_endpoints": {
            "bootstrap_endpoint": "/api/unity/bootstrap",
            "telemetry_endpoint": "/api/unity/telemetry",
        },
    }
    if latest_unity_telemetry_by_vehicle_id:
        bootstrap["latest_unity_telemetry_by_vehicle_id"] = [
            latest_unity_telemetry_by_vehicle_id[vehicle_id]
            for vehicle_id in sorted(latest_unity_telemetry_by_vehicle_id)
        ]
    return bootstrap


def _unity_vehicle_identity_map(session: LiveSimulationSession) -> list[dict[str, object]]:
    return [
        {
            "vehicle_id": vehicle.id,
            "vehicle_type": getattr(vehicle.vehicle_type, "name", str(vehicle.vehicle_type)),
            "current_node_id": vehicle.current_node_id,
            "operational_state": vehicle.operational_state,
            "is_active": getattr(vehicle, "is_active", True),
        }
        for vehicle in sorted(session.engine.vehicles, key=lambda vehicle: vehicle.id)
    ]


def _unity_telemetry_samples_from_payload(
    payload: dict[str, object],
) -> tuple[dict[str, object], ...]:
    if "telemetry_samples" in payload:
        telemetry_samples_payload = payload.get("telemetry_samples", ())
        if not isinstance(telemetry_samples_payload, list):
            raise ValueError("telemetry_samples must be a list of objects")
        return tuple(
            _unity_telemetry_sample_from_payload(sample, index=index)
            for index, sample in enumerate(telemetry_samples_payload)
        )
    if "telemetry" in payload:
        telemetry_payload = payload.get("telemetry")
        if not isinstance(telemetry_payload, dict):
            raise ValueError("telemetry must be an object")
        return (_unity_telemetry_sample_from_payload(telemetry_payload),)
    raise ValueError("Expected telemetry or telemetry_samples")


def _unity_telemetry_sample_from_payload(
    payload: dict[str, object],
    *,
    index: int | None = None,
) -> dict[str, object]:
    position = _payload_position(payload, "position")
    sample: dict[str, object] = {
        "vehicle_id": _payload_int(payload, "vehicle_id"),
        "timestamp_s": _payload_float(payload, "timestamp_s"),
        "position": list(position),
        "speed": _payload_float(payload, "speed"),
    }
    heading_rad = payload.get("heading_rad")
    if isinstance(heading_rad, (int, float)) and not isinstance(heading_rad, bool):
        sample["heading_rad"] = float(heading_rad)
    rotation = payload.get("rotation")
    if isinstance(rotation, list):
        sample["rotation"] = [
            float(component)
            for component in rotation
            if isinstance(component, (int, float)) and not isinstance(component, bool)
        ]
    current_node_id = _payload_optional_int(payload, "current_node_id")
    if current_node_id is not None:
        sample["current_node_id"] = current_node_id
    current_edge_id = _payload_optional_int(payload, "current_edge_id")
    if current_edge_id is not None:
        sample["current_edge_id"] = current_edge_id
    if index is not None:
        sample["sample_index"] = index
    return sample


def _normalize_unity_telemetry_sample(sample: dict[str, object]) -> dict[str, object]:
    normalized_sample = dict(sample)
    normalized_sample["vehicle_id"] = int(normalized_sample["vehicle_id"])
    normalized_sample["timestamp_s"] = float(normalized_sample["timestamp_s"])
    normalized_sample["position"] = [
        float(component) for component in normalized_sample["position"]  # type: ignore[arg-type]
    ]
    normalized_sample["speed"] = float(normalized_sample["speed"])
    if "heading_rad" in normalized_sample:
        normalized_sample["heading_rad"] = float(normalized_sample["heading_rad"])
    if "rotation" in normalized_sample:
        normalized_sample["rotation"] = [
            float(component) for component in normalized_sample["rotation"]  # type: ignore[arg-type]
        ]
    if "current_node_id" in normalized_sample:
        normalized_sample["current_node_id"] = int(normalized_sample["current_node_id"])
    if "current_edge_id" in normalized_sample:
        normalized_sample["current_edge_id"] = int(normalized_sample["current_edge_id"])
    if "sample_index" in normalized_sample:
        normalized_sample["sample_index"] = int(normalized_sample["sample_index"])
    return normalized_sample


def _payload_optional_int(payload: dict[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{key} must be numeric")
    return int(value)


def _payload_position(
    payload: dict[str, object],
    key: str,
) -> tuple[float, float, float]:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{key} must be a list of three numeric values")
    coordinates: list[float] = []
    for index, component in enumerate(value):
        if isinstance(component, bool) or not isinstance(component, (int, float, str)):
            raise ValueError(f"{key}[{index}] must be numeric")
        coordinates.append(float(component))
    return (coordinates[0], coordinates[1], coordinates[2])


def _build_live_command_result(
    *,
    engine: SimulationEngine,
    command: SimulationCommand,
) -> SimulationCommandResult:
    return SimulationCommandResult(
        status="accepted",
        command=command_to_dict(command),
        sequence=None,
        started_at_s=engine.simulated_time_s,
        completed_at_s=engine.simulated_time_s,
        result_timestamp_s=engine.simulated_time_s,
        emitted_update_indices=(),
        blocked_edge_ids=tuple(sorted(engine.world_state.blocked_edge_ids)),
        vehicles=_build_live_vehicle_surface_states(engine),
    )


def _read_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return data


def _build_live_vehicle_surface_states(
    engine: SimulationEngine,
) -> tuple[VehicleSurfaceState, ...]:
    return tuple(
        VehicleSurfaceState(
            vehicle_id=vehicle.id,
            node_id=vehicle.current_node_id,
            position=vehicle.position,
            operational_state=vehicle.operational_state,
        )
        for vehicle in engine.vehicles
        if getattr(vehicle, "is_active", True)
    )


def _selection_requests_from_payload(
    payload: dict[str, object],
) -> tuple[tuple[int, ...], tuple[RoutePreviewRequest, ...]]:
    selected_vehicle_ids_payload = payload.get("selected_vehicle_ids", ())
    if isinstance(selected_vehicle_ids_payload, list):
        selected_vehicle_ids = tuple(
            int(vehicle_id)
            for vehicle_id in selected_vehicle_ids_payload
            if isinstance(vehicle_id, (int, float))
        )
    else:
        selected_vehicle_ids = ()

    route_preview_requests = _route_preview_requests_from_payload(payload)
    return selected_vehicle_ids, route_preview_requests


def _route_preview_requests_from_payload(
    payload: dict[str, object],
) -> tuple[RoutePreviewRequest, ...]:
    if "route_preview_requests" not in payload:
        return ()

    route_preview_requests_payload = payload.get("route_preview_requests", ())
    if not isinstance(route_preview_requests_payload, list):
        raise ValueError("route_preview_requests must be a list of objects")

    route_preview_requests: list[RoutePreviewRequest] = []
    for index, request in enumerate(route_preview_requests_payload):
        if not isinstance(request, dict):
            raise ValueError(
                f"route_preview_requests[{index}] must be an object"
            )
        route_preview_requests.append(
            RoutePreviewRequest(
                vehicle_id=_payload_int(request, "vehicle_id"),
                destination_node_id=_payload_int(request, "destination_node_id"),
            )
        )
    return tuple(route_preview_requests)


def _payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{key} must be numeric")
    return int(value)


def _payload_float(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _payload_optional_float(
    payload: dict[str, object],
    key: str,
    default: float,
) -> float:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return default
    return float(value)


def _simulation_command_from_payload(payload: dict[str, object]) -> SimulationCommand:
    commands = _simulation_commands_from_payload(payload)
    if len(commands) != 1:
        raise ValueError("Expected exactly one command")
    return commands[0]


def _simulation_commands_from_payload(
    payload: dict[str, object],
) -> tuple[SimulationCommand, ...]:
    command_type = str(payload.get("command_type", "")).strip()
    selected_vehicle_ids = _payload_int_list(payload, "selected_vehicle_ids")
    explicit_vehicle_ids = _payload_int_list(payload, "vehicle_ids")
    vehicle_ids = explicit_vehicle_ids or selected_vehicle_ids
    if command_type == "block_edge":
        return (BlockEdgeCommand(edge_id=_payload_int(payload, "edge_id")),)
    if command_type == "unblock_edge":
        return (UnblockEdgeCommand(edge_id=_payload_int(payload, "edge_id")),)
    if command_type == "reposition_vehicle":
        target_vehicle_ids = vehicle_ids or (_payload_int(payload, "vehicle_id"),)
        return tuple(
            RepositionVehicleCommand(vehicle_id=vehicle_id, node_id=_payload_int(payload, "node_id"))
            for vehicle_id in target_vehicle_ids
        )
    if command_type == "assign_vehicle_destination":
        target_vehicle_ids = vehicle_ids or (_payload_int(payload, "vehicle_id"),)
        return tuple(
            AssignVehicleDestinationCommand(
                vehicle_id=vehicle_id,
                destination_node_id=_payload_int(payload, "destination_node_id"),
            )
            for vehicle_id in target_vehicle_ids
        )
    if command_type == "spawn_vehicle":
        return (
            SpawnVehicleCommand(
                vehicle_id=_payload_int(payload, "vehicle_id"),
                node_id=_payload_int(payload, "node_id"),
                max_speed=_payload_float(payload, "max_speed"),
                max_payload=_payload_float(payload, "max_payload"),
                vehicle_type=str(payload.get("vehicle_type", "GENERIC")),
                payload=_payload_optional_float(payload, "payload", 0.0),
                velocity=_payload_optional_float(payload, "velocity", 0.0),
            ),
        )
    if command_type == "remove_vehicle":
        return (
            RemoveVehicleCommand(vehicle_id=_payload_int(payload, "vehicle_id")),
        )
    if command_type == "inject_job":
        job_payload = payload.get("job")
        if not isinstance(job_payload, dict):
            raise ValueError("job must be an object")
        return (
            InjectJobCommand(
                vehicle_id=_payload_int(payload, "vehicle_id"),
                job=job_from_dict(job_payload),
            ),
        )
    if command_type == "declare_temporary_hazard":
        return (
            DeclareTemporaryHazardCommand(
                edge_id=_payload_int(payload, "edge_id"),
                hazard_label=str(payload.get("hazard_label", "")).strip(),
            ),
        )
    if command_type == "clear_temporary_hazard":
        return (
            ClearTemporaryHazardCommand(
                edge_id=_payload_int(payload, "edge_id"),
            ),
        )
    raise ValueError(f"Unknown command_type: {command_type}")


def _payload_int_list(payload: dict[str, object], key: str) -> tuple[int, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    numbers: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            continue
        numbers.append(int(item))
    return tuple(numbers)


__all__ = [
    "DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY",
    "DEFAULT_LIVE_HOST",
    "DEFAULT_LIVE_OUTPUT_DIRECTORY",
    "LiveAppArtifacts",
    "LiveAppLaunchResult",
    "LiveAppServer",
    "build_live_app_url",
    "export_live_app_artifacts",
    "launch_live_app",
]
