import json
from typing import Any, cast

from autonomous_ops_sim.authoring import (
    apply_geometry_edit_transaction,
    geometry_edit_transaction_from_dict,
    validate_geometry_edit_transaction,
)
from autonomous_ops_sim.io.scenario_loader import (
    load_scenario,
    validate_scenario_payload,
)


def build_authoring_scenario() -> dict[str, object]:
    return {
        "name": "authoring-test",
        "seed": 11,
        "duration_s": 20,
        "map": {
            "kind": "graph",
            "params": {
                "nodes": [
                    {"id": 1, "position": [0, 0, 0], "node_type": "INTERSECTION"},
                    {"id": 2, "position": [10, 0, 0], "node_type": "INTERSECTION"},
                    {"id": 3, "position": [10, 8, 0], "node_type": "DEPOT"},
                ],
                "edges": [
                    {
                        "id": 1,
                        "start_node_id": 1,
                        "end_node_id": 2,
                        "distance": 10,
                        "speed_limit": 4,
                    },
                    {
                        "id": 2,
                        "start_node_id": 2,
                        "end_node_id": 3,
                        "distance": 8,
                        "speed_limit": 4,
                    },
                ],
                "render_geometry": {
                    "roads": [
                        {
                            "id": "road-a",
                            "edge_ids": [1],
                            "centerline": [[0, 0, 0], [10, 0, 0]],
                            "road_class": "primary",
                            "directionality": "one_way",
                            "lane_count": 1,
                            "width_m": 2.0,
                        }
                    ],
                    "intersections": [
                        {
                            "id": "int-1",
                            "node_id": 1,
                            "polygon": [[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]],
                            "intersection_type": "junction",
                        }
                    ],
                    "areas": [
                        {
                            "id": "yard-zone",
                            "kind": "depot",
                            "label": "Main Yard",
                            "polygon": [[7, 4, 0], [12, 4, 0], [12, 9, 0], [7, 9, 0]],
                        }
                    ],
                },
                "world_model": {
                    "environment": {
                        "family": "construction_yard",
                        "archetype": "yard",
                    },
                    "layers": {
                        "roads": [
                            {
                                "id": "road-a",
                                "kind": "road",
                                "reference_id": "road-a",
                            }
                        ],
                        "intersections": [
                            {
                                "id": "int-1",
                                "kind": "junction",
                                "reference_id": "int-1",
                            }
                        ],
                        "zones": [
                            {
                                "id": "yard-zone",
                                "kind": "yard",
                                "polygon": [[7, 4, 0], [12, 4, 0], [12, 9, 0], [7, 9, 0]],
                            }
                        ],
                    },
                    "asset_layers": [],
                },
            },
        },
        "vehicles": [
            {
                "id": 1,
                "position": [0, 0, 0],
                "velocity": 0,
                "payload": 0,
                "max_payload": 10,
                "max_speed": 4,
            }
        ],
    }


def test_geometry_edit_transaction_moves_node_and_related_geometry() -> None:
    scenario_data = build_authoring_scenario()
    transaction = geometry_edit_transaction_from_dict(
        {
            "label": "move-first-node",
            "operations": [
                {
                    "kind": "move_node",
                    "target_id": 1,
                    "position": [2, 3, 0],
                }
            ],
        }
    )

    updated = apply_geometry_edit_transaction(scenario_data, transaction)
    params = cast(dict[str, Any], updated["map"])["params"]
    render_geometry = cast(dict[str, Any], params["render_geometry"])
    roads = cast(list[dict[str, Any]], render_geometry["roads"])
    intersections = cast(list[dict[str, Any]], render_geometry["intersections"])

    assert cast(list[dict[str, Any]], params["nodes"])[0]["position"] == [2.0, 3.0, 0.0]
    assert roads[0]["centerline"][0] == [2.0, 3.0, 0.0]
    assert intersections[0]["polygon"][0] == [
        1.0,
        2.0,
        0.0,
    ]


def test_geometry_edit_transaction_updates_area_and_world_model_zone() -> None:
    scenario_data = build_authoring_scenario()
    transaction = geometry_edit_transaction_from_dict(
        {
            "label": "reshape-zone",
            "operations": [
                {
                    "kind": "set_area_polygon",
                    "target_id": "yard-zone",
                    "points": [[8, 4, 0], [13, 4, 0], [13, 10, 0], [8, 10, 0]],
                }
            ],
        }
    )

    updated = apply_geometry_edit_transaction(scenario_data, transaction)
    params = cast(dict[str, Any], updated["map"])["params"]
    render_geometry = cast(dict[str, Any], params["render_geometry"])
    world_model = cast(dict[str, Any], params["world_model"])
    layers = cast(dict[str, Any], world_model["layers"])

    assert cast(list[dict[str, Any]], render_geometry["areas"])[0]["polygon"][0] == [
        8.0,
        4.0,
        0.0,
    ]
    assert cast(list[dict[str, Any]], layers["zones"])[0]["polygon"][0] == [
        8.0,
        4.0,
        0.0,
    ]


def test_geometry_edit_validation_rejects_duplicate_node_position() -> None:
    scenario_data = build_authoring_scenario()
    transaction = geometry_edit_transaction_from_dict(
        {
            "label": "overlap-node",
            "operations": [
                {
                    "kind": "move_node",
                    "target_id": 1,
                    "position": [10, 0, 0],
                }
            ],
        }
    )

    messages = validate_geometry_edit_transaction(scenario_data, transaction)

    assert len(messages) == 1
    assert messages[0].severity == "error"
    assert "positions must be unique" in messages[0].message


def test_validate_scenario_payload_accepts_a_valid_authoring_scenario() -> None:
    validate_scenario_payload(build_authoring_scenario())


def test_saved_authoring_scenario_round_trips_through_loader(tmp_path) -> None:
    scenario_path = tmp_path / "authoring.json"
    scenario_path.write_text(json.dumps(build_authoring_scenario(), indent=2), encoding="utf-8")
    transaction = geometry_edit_transaction_from_dict(
        {
            "label": "road-edit",
            "operations": [
                {
                    "kind": "set_road_centerline",
                    "target_id": "road-a",
                    "points": [[0, 0, 0], [4, 1, 0], [10, 0, 0]],
                }
            ],
        }
    )

    updated = apply_geometry_edit_transaction(build_authoring_scenario(), transaction)
    scenario_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")

    loaded = load_scenario(scenario_path)
    render_geometry = cast(dict[str, Any], loaded.map_spec.params["render_geometry"])
    roads = cast(list[dict[str, Any]], render_geometry["roads"])

    assert loaded.map_spec.kind == "graph"
    assert roads[0]["centerline"][1] == [4.0, 1.0, 0.0]
