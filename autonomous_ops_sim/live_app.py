from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import quote
import webbrowser

from autonomous_ops_sim.api import (
    build_live_session_bundle,
    export_live_session_bundle_json,
    live_session_bundle_to_dict,
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

    def __init__(self, directory: Path, *, host: str = DEFAULT_LIVE_HOST, port: int = 0) -> None:
        handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
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


def export_live_app_artifacts(
    *,
    scenario_path: str | Path,
    output_directory: str | Path = DEFAULT_LIVE_OUTPUT_DIRECTORY,
    frontend_dist_directory: str | Path = DEFAULT_LIVE_FRONTEND_DIST_DIRECTORY,
) -> LiveAppArtifacts:
    """Prepare the live-session bundle and launch surface for the serious UI."""

    scenario_file = Path(scenario_path)
    scenario = load_scenario(scenario_file)
    session = LiveSimulationSession(build_scenario_engine(scenario))
    bundle = build_live_session_bundle(session)

    output_root = Path(output_directory)
    output_root.mkdir(parents=True, exist_ok=True)

    live_session_bundle_path = output_root / "live_session_bundle.json"
    live_session_bundle_path.write_text(
        export_live_session_bundle_json(bundle),
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
            live_session_bundle_path=live_session_bundle_path,
            launch_path=copied_frontend_root / "index.html",
            launch_mode="frontend_dist",
            launch_relative_url=(
                f"/serious_ui/index.html?bundle={quote('/live_session_bundle.json')}"
            ),
        )

    launch_path = output_root / "live_session.viewer.html"
    export_serious_viewer_html(
        live_session_bundle_to_dict(bundle),
        launch_path,
        title=f"Autonomous Ops Live Session ({scenario.name})",
    )
    return LiveAppArtifacts(
        output_directory=output_root,
        scenario_path=scenario_file,
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
        server = LiveAppServer(artifacts.output_directory, host=host, port=port)
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
