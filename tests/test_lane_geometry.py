import json

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import build_scenario_engine
from autonomous_ops_sim.visualization import build_render_geometry_surface


def test_graph_map_render_geometry_accepts_explicit_lane_connector_and_stopline_metadata(
    tmp_path,
) -> None:
    scenario_path = tmp_path / "lane_geometry.json"
    scenario_path.write_text(
        json.dumps(
            {
                "name": "lane-geometry",
                "seed": 7,
                "duration_s": 12,
                "map": {
                    "kind": "graph",
                    "params": {
                        "nodes": [
                            {"id": 1, "position": [0, 0, 0], "node_type": "INTERSECTION"},
                            {"id": 2, "position": [2, 0, 0], "node_type": "INTERSECTION"},
                            {"id": 3, "position": [2, 2, 0], "node_type": "DEPOT"},
                        ],
                        "edges": [
                            {
                                "id": 1,
                                "start_node_id": 1,
                                "end_node_id": 2,
                                "distance": 2,
                                "speed_limit": 4,
                            },
                            {
                                "id": 2,
                                "start_node_id": 2,
                                "end_node_id": 3,
                                "distance": 2,
                                "speed_limit": 4,
                            },
                        ],
                        "render_geometry": {
                            "roads": [
                                {
                                    "id": "r1",
                                    "edge_ids": [1],
                                    "centerline": [[0, 0, 0], [2, 0, 0]],
                                    "directionality": "one_way",
                                    "lane_count": 1,
                                    "width_m": 1.0,
                                },
                                {
                                    "id": "r2",
                                    "edge_ids": [2],
                                    "centerline": [[2, 0, 0], [2, 2, 0]],
                                    "directionality": "one_way",
                                    "lane_count": 1,
                                    "width_m": 1.0,
                                },
                            ],
                            "intersections": [],
                            "areas": [],
                            "lanes": [
                                {
                                    "id": "r1-l0",
                                    "road_id": "r1",
                                    "lane_index": 0,
                                    "directionality": "forward",
                                    "lane_role": "travel",
                                    "centerline": [[0, -0.2, 0], [2, -0.2, 0]],
                                },
                                {
                                    "id": "r2-l0",
                                    "road_id": "r2",
                                    "lane_index": 0,
                                    "directionality": "forward",
                                    "lane_role": "loading_approach",
                                    "centerline": [[2.2, 0, 0], [2.2, 2, 0]],
                                },
                            ],
                            "turn_connectors": [
                                {
                                    "id": "c1",
                                    "from_lane_id": "r1-l0",
                                    "to_lane_id": "r2-l0",
                                    "centerline": [[2, -0.2, 0], [2.2, 0, 0]],
                                }
                            ],
                            "stop_lines": [
                                {
                                    "id": "s1",
                                    "lane_id": "r2-l0",
                                    "segment": [[2.0, 1.8, 0], [2.4, 1.8, 0]],
                                }
                            ],
                            "merge_zones": [
                                {
                                    "id": "m1",
                                    "lane_ids": ["r1-l0", "r2-l0"],
                                    "polygon": [[1.8, -0.2, 0], [2.4, -0.2, 0], [2.4, 0.4, 0]],
                                }
                            ],
                        },
                    },
                },
                "vehicles": [
                    {
                        "id": 1,
                        "position": [0, 0, 0],
                        "velocity": 0,
                        "payload": 0,
                        "max_payload": 5,
                        "max_speed": 4,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    scenario = load_scenario(scenario_path)
    surface = build_render_geometry_surface(build_scenario_engine(scenario).map)

    assert [lane.lane_id for lane in surface.lanes] == ["r1-l0", "r2-l0"]
    assert surface.turn_connectors[0].connector_id == "c1"
    assert surface.stop_lines[0].stop_line_id == "s1"
    assert surface.merge_zones[0].merge_zone_id == "m1"
