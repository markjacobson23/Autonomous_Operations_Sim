from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autonomous_ops_sim.api import (
    build_live_session_bundle,
    build_live_sync_bundle,
    build_replay_bundle,
    export_live_session_bundle_json,
    export_live_sync_bundle_json,
    export_replay_bundle_json,
    live_session_bundle_to_dict,
    live_sync_bundle_to_dict,
    replay_bundle_to_dict,
)
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_pack_runner import (
    aggregate_summary_to_dict,
    export_scenario_pack_json,
    run_scenario_pack,
)
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    LiveSimulationSession,
)
from autonomous_ops_sim.simulation.scenario_executor import (
    build_scenario_engine,
    execute_scenario,
)
from autonomous_ops_sim.visualization import (
    RoutePreviewRequest,
    export_serious_viewer_html,
)


SHOWCASE_EXPORT_SCHEMA_VERSION = 1
DEFAULT_SHOWCASE_PACK_DIRECTORY = Path("scenarios/showpiece_pack")
DEFAULT_SHOWCASE_FLAGSHIP_SCENARIO = (
    DEFAULT_SHOWCASE_PACK_DIRECTORY / "01_mine_ore_shift.json"
)

_FLAGSHIP_LOADING_NODE_ID = 120
_FLAGSHIP_CRUSHER_NODE_ID = 140
_FLAGSHIP_PREVIEW_BLOCK_EDGE_IDS = (1004, 1010, 1016)


@dataclass(frozen=True)
class ShowcaseArtifacts:
    """Stable file inventory for one generated Step 38 showcase export."""

    output_directory: Path
    replay_bundle_path: Path
    replay_viewer_path: Path
    live_session_bundle_path: Path
    live_session_viewer_path: Path
    live_sync_bundle_path: Path
    live_sync_viewer_path: Path
    scenario_pack_export_path: Path
    manifest_path: Path


def export_showcase_demo(
    output_directory: str | Path,
    *,
    flagship_scenario_path: str | Path = DEFAULT_SHOWCASE_FLAGSHIP_SCENARIO,
    pack_directory: str | Path = DEFAULT_SHOWCASE_PACK_DIRECTORY,
) -> ShowcaseArtifacts:
    """Export the Step 38 mining showpiece demo as replay/live/viewer artifacts."""

    output_root = Path(output_directory)
    output_root.mkdir(parents=True, exist_ok=True)

    flagship_scenario = load_scenario(flagship_scenario_path)
    flagship_execution = execute_scenario(flagship_scenario)
    replay_bundle = build_replay_bundle(
        flagship_execution.engine,
        summary=flagship_execution.summary,
    )

    live_session, selected_vehicle_ids, route_preview_requests = (
        _build_flagship_live_session(flagship_scenario)
    )
    live_session_bundle = build_live_session_bundle(
        live_session,
        selected_vehicle_ids=selected_vehicle_ids,
        route_preview_requests=route_preview_requests,
    )
    live_sync_bundle = build_live_sync_bundle(
        live_session,
        selected_vehicle_ids=selected_vehicle_ids,
        route_preview_requests=route_preview_requests,
    )

    pack_result = run_scenario_pack(pack_directory)

    replay_bundle_path = output_root / "mine_flagship_replay_bundle.json"
    replay_bundle_path.write_text(
        export_replay_bundle_json(replay_bundle),
        encoding="utf-8",
    )
    replay_viewer_path = output_root / "mine_flagship_replay.viewer.html"
    export_serious_viewer_html(
        replay_bundle_to_dict(replay_bundle),
        replay_viewer_path,
        title="Mine Operations Replay Showpiece",
    )

    live_session_bundle_path = output_root / "mine_flagship_live_session_bundle.json"
    live_session_bundle_path.write_text(
        export_live_session_bundle_json(live_session_bundle),
        encoding="utf-8",
    )
    live_session_viewer_path = output_root / "mine_flagship_live_session.viewer.html"
    export_serious_viewer_html(
        live_session_bundle_to_dict(live_session_bundle),
        live_session_viewer_path,
        title="Mine Operations Live Session Showpiece",
    )

    live_sync_bundle_path = output_root / "mine_flagship_live_sync_bundle.json"
    live_sync_bundle_path.write_text(
        export_live_sync_bundle_json(live_sync_bundle),
        encoding="utf-8",
    )
    live_sync_viewer_path = output_root / "mine_flagship_live_sync.viewer.html"
    export_serious_viewer_html(
        live_sync_bundle_to_dict(live_sync_bundle),
        live_sync_viewer_path,
        title="Mine Operations Live Sync Showpiece",
    )

    scenario_pack_export_path = output_root / "mine_showpiece_pack.json"
    scenario_pack_export_path.write_text(
        export_scenario_pack_json(pack_result),
        encoding="utf-8",
    )

    artifacts = ShowcaseArtifacts(
        output_directory=output_root,
        replay_bundle_path=replay_bundle_path,
        replay_viewer_path=replay_viewer_path,
        live_session_bundle_path=live_session_bundle_path,
        live_session_viewer_path=live_session_viewer_path,
        live_sync_bundle_path=live_sync_bundle_path,
        live_sync_viewer_path=live_sync_viewer_path,
        scenario_pack_export_path=scenario_pack_export_path,
        manifest_path=output_root / "showcase_manifest.json",
    )
    artifacts.manifest_path.write_text(
        export_showcase_manifest_json(
            artifacts,
            flagship_scenario=flagship_scenario,
            pack_result=pack_result,
        ),
        encoding="utf-8",
    )
    return artifacts


def build_showcase_manifest(
    artifacts: ShowcaseArtifacts,
    *,
    flagship_scenario,
    pack_result,
) -> dict[str, Any]:
    """Return a deterministic manifest for the generated showcase artifacts."""

    return {
        "schema_version": SHOWCASE_EXPORT_SCHEMA_VERSION,
        "flagship_scenario": {
            "name": flagship_scenario.name,
            "source_path": _scenario_source_path(flagship_scenario),
        },
        "artifacts": {
            "replay_bundle": artifacts.replay_bundle_path.name,
            "replay_viewer_html": artifacts.replay_viewer_path.name,
            "live_session_bundle": artifacts.live_session_bundle_path.name,
            "live_session_viewer_html": artifacts.live_session_viewer_path.name,
            "live_sync_bundle": artifacts.live_sync_bundle_path.name,
            "live_sync_viewer_html": artifacts.live_sync_viewer_path.name,
            "scenario_pack_export": artifacts.scenario_pack_export_path.name,
        },
        "scenario_pack": {
            "directory": DEFAULT_SHOWCASE_PACK_DIRECTORY.as_posix(),
            "aggregate_summary": aggregate_summary_to_dict(pack_result.aggregate_summary),
        },
    }


def export_showcase_manifest_json(
    artifacts: ShowcaseArtifacts,
    *,
    flagship_scenario,
    pack_result,
) -> str:
    """Return deterministic JSON for the showpiece artifact manifest."""

    return json.dumps(
        build_showcase_manifest(
            artifacts,
            flagship_scenario=flagship_scenario,
            pack_result=pack_result,
        ),
        indent=2,
        sort_keys=True,
    ) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for Step 38 showcase export."""

    parser = argparse.ArgumentParser(
        prog="autonomous-ops-showcase",
        description="Export the Step 38 mining showpiece replay/live viewer artifacts.",
    )
    parser.add_argument(
        "--output-dir",
        default="showcase_output",
        help="Directory to receive exported replay/live/showpiece artifacts.",
    )
    parser.add_argument(
        "--flagship-scenario",
        default=str(DEFAULT_SHOWCASE_FLAGSHIP_SCENARIO),
        help="Optional flagship scenario JSON path override.",
    )
    parser.add_argument(
        "--pack-directory",
        default=str(DEFAULT_SHOWCASE_PACK_DIRECTORY),
        help="Optional scenario pack directory override.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the Step 38 showcase exporter."""

    parser = build_parser()
    args = parser.parse_args(argv)
    artifacts = export_showcase_demo(
        args.output_dir,
        flagship_scenario_path=args.flagship_scenario,
        pack_directory=args.pack_directory,
    )
    print(artifacts.manifest_path)
    return 0


def _build_flagship_live_session(
    flagship_scenario,
) -> tuple[LiveSimulationSession, tuple[int, ...], tuple[RoutePreviewRequest, ...]]:
    if flagship_scenario.execution is None:
        raise ValueError("flagship scenario must define execution")

    session = LiveSimulationSession(build_scenario_engine(flagship_scenario))
    vehicle_id = flagship_scenario.execution.vehicle_id
    session.apply(
        AssignVehicleDestinationCommand(
            vehicle_id=vehicle_id,
            destination_node_id=_FLAGSHIP_LOADING_NODE_ID,
        )
    )
    for edge_id in _FLAGSHIP_PREVIEW_BLOCK_EDGE_IDS:
        session.apply(BlockEdgeCommand(edge_id=edge_id))
    return (
        session,
        (vehicle_id,),
        (
            RoutePreviewRequest(
                vehicle_id=vehicle_id,
                destination_node_id=_FLAGSHIP_CRUSHER_NODE_ID,
            ),
        ),
    )


def _scenario_source_path(scenario) -> str | None:
    if scenario.source_path is None:
        return None
    return scenario.source_path.as_posix()
