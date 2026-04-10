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
    BlockEdgeCommand,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SimulationCommand,
    UnblockEdgeCommand,
)
from autonomous_ops_sim.simulation.scenario_executor import build_scenario_engine
from autonomous_ops_sim.simulation.live_session import session_advance_to_dict
from autonomous_ops_sim.visualization import export_serious_viewer_html
from autonomous_ops_sim.visualization.command_center import RoutePreviewRequest


DEFAULT_LIVE_OUTPUT_DIRECTORY = Path("live_output")
DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY = Path("frontend/serious_ui/dist")
DEFAULT_LIVE_HOST = "127.0.0.1"
DEFAULT_LIVE_SESSION_STEP_SECONDS = 0.5


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
    """Mutable live session state backing the serious UI command transport."""

    artifacts: LiveAppArtifacts
    session: LiveSimulationSession
    play_state: str = "paused"
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
            )
            self._write_bundle(bundle)
            return bundle

    def apply_command(
        self,
        command: SimulationCommand,
        *,
        selected_vehicle_ids: tuple[int, ...] | list[int] = (),
        route_preview_requests: tuple[RoutePreviewRequest, ...]
        | list[RoutePreviewRequest] = (),
    ) -> tuple[dict[str, object], dict[str, object]]:
        with self.lock:
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
            record = self.session.advance_by(delta_s)
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
        with self.lock:
            self.play_state = play_state
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
        with self.lock:
            scenario = load_scenario(self.artifacts.working_scenario_path)
            self.session = LiveSimulationSession(build_scenario_engine(scenario))
            self.play_state = "paused"
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
        )
        self._write_bundle(bundle)
        return bundle

    def _write_bundle(self, bundle: dict[str, object]) -> None:
        self.artifacts.live_session_bundle_path.write_text(
            json.dumps(bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


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
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/authoring/validate",
            "/api/authoring/save",
            "/api/live/command",
            "/api/live/session/control",
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
        if parsed.path == "/api/live/command":
            self._handle_live_command(payload)
            return
        if parsed.path == "/api/live/session/control":
            self._handle_live_session_control(payload)
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
            command = _simulation_command_from_payload(payload)
        except (KeyError, TypeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
                    "message": str(exc),
                    "validation_messages": [],
                },
            )
            return

        selected_vehicle_ids, route_preview_requests = _selection_requests_from_payload(
            payload
        )
        command_result, bundle = self._runtime.apply_command(
            command,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        )
        self._write_json_response(
            200,
            {
                "ok": command_result["status"] == "accepted",
                "command_result": command_result,
                "bundle": bundle,
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )

    def _handle_live_session_control(self, payload: dict[str, object]) -> None:
        action = str(payload.get("action", "")).strip().lower()
        selected_vehicle_ids, route_preview_requests = _selection_requests_from_payload(
            payload
        )
        try:
            if action == "step":
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
                    "validation_messages": [],
                },
            )
            return

        self._write_json_response(
            400,
            {
                "ok": False,
                "message": f"Unknown session control action: {action}",
                "validation_messages": [],
            },
        )


def export_live_app_artifacts(
    *,
    scenario_path: str | Path,
    output_directory: str | Path = DEFAULT_LIVE_OUTPUT_DIRECTORY,
    frontend_dist_directory: str | Path = DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY,
) -> LiveAppArtifacts:
    """Prepare the live-session bundle and launch surface for the serious UI."""

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
        copied_frontend_root = output_root / "serious_ui"
        shutil.copytree(frontend_dist_root, copied_frontend_root, dirs_exist_ok=True)
        return LiveAppArtifacts(
            output_directory=output_root,
            scenario_path=scenario_file,
            working_scenario_path=working_scenario_path,
            live_session_bundle_path=live_session_bundle_path,
            launch_path=copied_frontend_root / "index.html",
            launch_mode="frontend_dist",
            launch_relative_url=(
                f"/serious_ui/index.html?bundle={quote('/live_session_bundle.json')}"
            ),
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
) -> dict[str, object]:
    bundle = live_session_bundle_to_dict(
        build_live_session_bundle(
            session,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        )
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
        "command_endpoint": "/api/live/command",
        "session_control_endpoint": "/api/live/session/control",
    }
    return bundle


def _read_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return data


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

    route_preview_requests_payload = payload.get("route_preview_requests", ())
    if not isinstance(route_preview_requests_payload, list):
        return selected_vehicle_ids, ()

    route_preview_requests = tuple(
        RoutePreviewRequest(
            vehicle_id=int(vehicle_id),
            destination_node_id=int(destination_node_id),
        )
        for request in route_preview_requests_payload
        if isinstance(request, dict)
        and isinstance((vehicle_id := request.get("vehicle_id")), (int, float))
        and isinstance(
            (destination_node_id := request.get("destination_node_id")),
            (int, float),
        )
    )
    return selected_vehicle_ids, route_preview_requests


def _payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{key} must be numeric")
    return int(value)


def _simulation_command_from_payload(payload: dict[str, object]) -> SimulationCommand:
    command_type = str(payload.get("command_type", "")).strip()
    if command_type == "block_edge":
        return BlockEdgeCommand(edge_id=_payload_int(payload, "edge_id"))
    if command_type == "unblock_edge":
        return UnblockEdgeCommand(edge_id=_payload_int(payload, "edge_id"))
    if command_type == "reposition_vehicle":
        return RepositionVehicleCommand(
            vehicle_id=_payload_int(payload, "vehicle_id"),
            node_id=_payload_int(payload, "node_id"),
        )
    if command_type == "assign_vehicle_destination":
        return AssignVehicleDestinationCommand(
            vehicle_id=_payload_int(payload, "vehicle_id"),
            destination_node_id=_payload_int(payload, "destination_node_id"),
        )
    raise ValueError(f"Unknown command_type: {command_type}")


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
