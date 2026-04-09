from __future__ import annotations

from dataclasses import dataclass
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
    build_live_session_bundle,
    live_session_bundle_to_dict,
)
from autonomous_ops_sim.authoring import (
    apply_geometry_edit_transaction,
    export_scenario_json,
    geometry_edit_transaction_from_dict,
    validate_geometry_edit_transaction,
    validation_message_to_dict,
)
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation import LiveSimulationSession
from autonomous_ops_sim.simulation.scenario_executor import build_scenario_engine
from autonomous_ops_sim.visualization import export_serious_viewer_html


DEFAULT_LIVE_OUTPUT_DIRECTORY = Path("live_output")
DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY = Path("frontend/serious_ui/dist")
DEFAULT_LIVE_HOST = "127.0.0.1"


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


class LiveAppServer:
    """Serve one prepared live app directory for browser access."""

    def __init__(
        self,
        directory: Path,
        *,
        artifacts: LiveAppArtifacts,
        host: str = DEFAULT_LIVE_HOST,
        port: int = 0,
    ) -> None:
        handler = partial(
            LiveAppRequestHandler,
            directory=str(directory),
            artifacts=artifacts,
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
        **kwargs,
    ) -> None:
        self._artifacts = artifacts
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/authoring/reload":
            self._write_json_response(
                200,
                {
                    "ok": True,
                    "bundle": _refresh_live_bundle(self._artifacts),
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
        }:
            self.send_error(404, "Unknown live authoring endpoint.")
            return

        try:
            payload = self._read_json_payload()
            transaction = geometry_edit_transaction_from_dict(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._write_json_response(
                400,
                {
                    "ok": False,
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
        if parsed.path == "/api/authoring/validate":
            self._write_json_response(
                200,
                {
                    "ok": len(messages) == 0,
                    "validation_messages": [
                        validation_message_to_dict(message) for message in messages
                    ],
                },
            )
            return

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
        refreshed_bundle = _refresh_live_bundle(self._artifacts)
        self._write_json_response(
            200,
            {
                "ok": True,
                "bundle": refreshed_bundle,
                "validation_messages": [],
                "working_scenario_path": str(self._artifacts.working_scenario_path),
            },
        )

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
    live_session_bundle_path.write_text(
        json.dumps(
            _build_live_bundle_record(
                scenario_path=working_scenario_path,
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
            scenario_path=working_scenario_path,
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
    scenario_path: Path,
    source_scenario_path: Path,
    working_scenario_path: Path,
) -> dict[str, object]:
    scenario = load_scenario(scenario_path)
    session = LiveSimulationSession(build_scenario_engine(scenario))
    bundle = live_session_bundle_to_dict(build_live_session_bundle(session))
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
    return bundle


def _refresh_live_bundle(artifacts: LiveAppArtifacts) -> dict[str, object]:
    bundle = _build_live_bundle_record(
        scenario_path=artifacts.working_scenario_path,
        source_scenario_path=artifacts.scenario_path,
        working_scenario_path=artifacts.working_scenario_path,
    )
    artifacts.live_session_bundle_path.write_text(
        json.dumps(bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return bundle


def _read_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return data


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
