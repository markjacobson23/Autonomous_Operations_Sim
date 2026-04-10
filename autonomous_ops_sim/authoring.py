from __future__ import annotations

from dataclasses import dataclass
import json

from autonomous_ops_sim.io.scenario_loader import validate_scenario_payload


Position = tuple[float, float, float]


@dataclass(frozen=True)
class GeometryEditOperation:
    """One deterministic geometry mutation requested by the live editor."""

    kind: str
    target_id: int | str
    position: Position | None = None
    points: tuple[Position, ...] = ()


@dataclass(frozen=True)
class GeometryEditTransaction:
    """Ordered set of live geometry edits to validate and persist together."""

    label: str
    operations: tuple[GeometryEditOperation, ...]


@dataclass(frozen=True)
class GeometryValidationMessage:
    """Stable validation message surfaced back to the live editor."""

    severity: str
    code: str
    message: str
    target_kind: str | None = None
    target_id: int | str | None = None


def geometry_edit_transaction_from_dict(data: dict[str, object]) -> GeometryEditTransaction:
    """Parse one JSON edit payload into a typed transaction."""

    if not isinstance(data, dict):
        raise ValueError("Geometry edit transaction must be an object.")
    operations_data = data.get("operations")
    if not isinstance(operations_data, list):
        raise ValueError("Geometry edit transaction 'operations' must be a list.")
    label = data.get("label", "live_geometry_edit")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("Geometry edit transaction 'label' must be a non-empty string.")
    return GeometryEditTransaction(
        label=label,
        operations=tuple(_parse_geometry_edit_operation(item) for item in operations_data),
    )


def geometry_edit_transaction_to_dict(
    transaction: GeometryEditTransaction,
) -> dict[str, object]:
    """Convert one transaction into a stable JSON-ready record."""

    return {
        "label": transaction.label,
        "operations": [
            {
                "kind": operation.kind,
                "target_id": operation.target_id,
                **(
                    {"position": list(operation.position)}
                    if operation.position is not None
                    else {}
                ),
                **(
                    {"points": [list(point) for point in operation.points]}
                    if operation.points
                    else {}
                ),
            }
            for operation in transaction.operations
        ],
    }


def validation_message_to_dict(
    message: GeometryValidationMessage,
) -> dict[str, object]:
    """Convert one validation message into a stable JSON-ready record."""

    return {
        "severity": message.severity,
        "code": message.code,
        "message": message.message,
        "target_kind": message.target_kind,
        "target_id": message.target_id,
    }


def validate_geometry_edit_transaction(
    scenario_data: dict[str, object],
    transaction: GeometryEditTransaction,
) -> tuple[GeometryValidationMessage, ...]:
    """Apply one transaction in-memory and return deterministic validation messages."""

    try:
        candidate = apply_geometry_edit_transaction(scenario_data, transaction)
        validate_scenario_payload(candidate)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return (
            GeometryValidationMessage(
                severity="error",
                code="invalid_geometry_edit",
                message=str(exc),
            ),
        )

    return ()


def apply_geometry_edit_transaction(
    scenario_data: dict[str, object],
    transaction: GeometryEditTransaction,
) -> dict[str, object]:
    """Return a new raw scenario record with one transaction applied."""

    candidate = json.loads(json.dumps(scenario_data))
    params = _graph_map_params(candidate)

    for operation in transaction.operations:
        if operation.kind == "move_node":
            _apply_move_node(params, operation)
        elif operation.kind == "set_road_centerline":
            _apply_set_road_centerline(params, operation)
        elif operation.kind == "set_area_polygon":
            _apply_set_area_polygon(params, operation)
        else:
            raise ValueError(f"Unsupported geometry edit kind: {operation.kind!r}")

    return candidate


def export_scenario_json(scenario_data: dict[str, object]) -> str:
    """Export scenario JSON with deterministic formatting for saved edits."""

    return json.dumps(scenario_data, indent=2, sort_keys=True) + "\n"


def _parse_geometry_edit_operation(data: object) -> GeometryEditOperation:
    if not isinstance(data, dict):
        raise ValueError("Geometry edit operation must be an object.")

    kind = data.get("kind")
    if not isinstance(kind, str):
        raise ValueError("Geometry edit operation 'kind' must be a string.")

    target_id = data.get("target_id")
    if kind == "move_node":
        if not isinstance(target_id, int):
            raise ValueError("Move-node edit 'target_id' must be an int.")
        return GeometryEditOperation(
            kind=kind,
            target_id=target_id,
            position=_parse_position(data.get("position"), context="move_node.position"),
        )

    if kind in {"set_road_centerline", "set_area_polygon"}:
        if not isinstance(target_id, str) or not target_id:
            raise ValueError(f"{kind} edit 'target_id' must be a non-empty string.")
        points = _parse_points(data.get("points"), context=f"{kind}.points")
        if kind == "set_road_centerline" and len(points) < 2:
            raise ValueError("Road centerline edits require at least two points.")
        if kind == "set_area_polygon" and len(points) < 3:
            raise ValueError("Area polygon edits require at least three points.")
        return GeometryEditOperation(
            kind=kind,
            target_id=target_id,
            points=points,
        )

    raise ValueError(f"Unsupported geometry edit kind: {kind!r}")


def _parse_position(raw: object, *, context: str) -> Position:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError(f"{context} must be a three-number position.")
    x, y, z = raw
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not isinstance(
        z, (int, float)
    ):
        raise ValueError(f"{context} must contain only numeric values.")
    return (float(x), float(y), float(z))


def _parse_points(raw: object, *, context: str) -> tuple[Position, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"{context} must be a list of positions.")
    return tuple(
        _parse_position(point, context=f"{context}[{index}]")
        for index, point in enumerate(raw)
    )


def _graph_map_params(scenario_data: dict[str, object]) -> dict[str, object]:
    map_data = scenario_data.get("map")
    if not isinstance(map_data, dict):
        raise ValueError("Scenario is missing a valid top-level 'map' object.")
    if map_data.get("kind") != "graph":
        raise ValueError("Live geometry editing currently supports graph maps only.")
    params = map_data.get("params")
    if not isinstance(params, dict):
        raise ValueError("Graph map is missing a valid 'params' object.")
    return params


def _apply_move_node(params: dict[str, object], operation: GeometryEditOperation) -> None:
    nodes = _require_list(params.get("nodes"), context="Graph map nodes")
    target_node = _find_entry(nodes, "id", operation.target_id, label="graph node")
    old_position = _parse_position(
        target_node.get("position"),
        context=f"Graph node {operation.target_id} position",
    )
    assert operation.position is not None
    target_node["position"] = list(operation.position)
    _retarget_render_geometry_for_moved_node(
        params,
        node_id=int(operation.target_id),
        old_position=old_position,
        new_position=operation.position,
    )


def _apply_set_road_centerline(
    params: dict[str, object],
    operation: GeometryEditOperation,
) -> None:
    render_geometry = _require_dict(
        params.get("render_geometry"),
        context="Graph map render_geometry",
    )
    roads = _require_list(render_geometry.get("roads"), context="Render geometry roads")
    road = _find_entry(roads, "id", operation.target_id, label="road")
    road["centerline"] = [list(point) for point in operation.points]


def _apply_set_area_polygon(
    params: dict[str, object],
    operation: GeometryEditOperation,
) -> None:
    render_geometry = _require_dict(
        params.get("render_geometry"),
        context="Graph map render_geometry",
    )
    areas = _require_list(render_geometry.get("areas"), context="Render geometry areas")
    area = _find_entry(areas, "id", operation.target_id, label="area")
    polygon = [list(point) for point in operation.points]
    area["polygon"] = polygon
    _retarget_world_model_area_polygon(
        params,
        area_id=str(operation.target_id),
        polygon=polygon,
    )


def _retarget_render_geometry_for_moved_node(
    params: dict[str, object],
    *,
    node_id: int,
    old_position: Position,
    new_position: Position,
) -> None:
    render_geometry = params.get("render_geometry")
    if not isinstance(render_geometry, dict):
        return

    edges = _require_list(params.get("edges"), context="Graph map edges")
    connected_edge_ids = {
        int(edge["id"])
        for edge in edges
        if isinstance(edge, dict)
        and (
            edge.get("start_node_id") == node_id or edge.get("end_node_id") == node_id
        )
    }

    roads = render_geometry.get("roads")
    if isinstance(roads, list):
        for road in roads:
            if not isinstance(road, dict):
                continue
            edge_ids = road.get("edge_ids")
            if not isinstance(edge_ids, list) or not connected_edge_ids.intersection(
                int(edge_id) for edge_id in edge_ids if isinstance(edge_id, int)
            ):
                continue
            centerline = road.get("centerline")
            if not isinstance(centerline, list):
                continue
            for index, point in enumerate(centerline):
                parsed_point = _position_or_none(point)
                if parsed_point == old_position and index in {0, len(centerline) - 1}:
                    centerline[index] = list(new_position)

    intersections = render_geometry.get("intersections")
    if isinstance(intersections, list):
        delta_x = new_position[0] - old_position[0]
        delta_y = new_position[1] - old_position[1]
        delta_z = new_position[2] - old_position[2]
        for intersection in intersections:
            if not isinstance(intersection, dict) or intersection.get("node_id") != node_id:
                continue
            polygon = intersection.get("polygon")
            if not isinstance(polygon, list):
                continue
            intersection["polygon"] = [
                [
                    point[0] + delta_x,
                    point[1] + delta_y,
                    point[2] + delta_z,
                ]
                for point in polygon
                if isinstance(point, list) and len(point) == 3
            ]


def _retarget_world_model_area_polygon(
    params: dict[str, object],
    *,
    area_id: str,
    polygon: list[list[float]],
) -> None:
    world_model = params.get("world_model")
    if not isinstance(world_model, dict):
        return
    layers = world_model.get("layers")
    if not isinstance(layers, dict):
        return
    for layer_name in (
        "zones",
        "buildings",
        "sidewalks",
        "boundaries",
        "no_go_areas",
    ):
        features = layers.get(layer_name)
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            if feature.get("id") == area_id or feature.get("reference_id") == area_id:
                if "polygon" in feature:
                    feature["polygon"] = polygon


def _find_entry(
    records: list[object],
    id_field: str,
    target_id: int | str,
    *,
    label: str,
) -> dict[str, object]:
    for record in records:
        if isinstance(record, dict) and record.get(id_field) == target_id:
            return record
    raise ValueError(f"Unable to find {label} {target_id!r} in the scenario.")


def _require_dict(value: object, *, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object.")
    return value


def _require_list(value: object, *, context: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{context} must be a list.")
    return value


def _position_or_none(value: object) -> Position | None:
    if (
        isinstance(value, list)
        and len(value) == 3
        and all(isinstance(part, (int, float)) for part in value)
    ):
        x, y, z = value
        return (float(x), float(y), float(z))
    return None


__all__ = [
    "GeometryEditOperation",
    "GeometryEditTransaction",
    "GeometryValidationMessage",
    "apply_geometry_edit_transaction",
    "export_scenario_json",
    "geometry_edit_transaction_from_dict",
    "geometry_edit_transaction_to_dict",
    "validate_geometry_edit_transaction",
    "validation_message_to_dict",
]
