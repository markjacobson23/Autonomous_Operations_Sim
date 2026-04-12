import type { Dispatch, MouseEvent, Ref, RefObject, SetStateAction } from "react";

import {
  buildRoutePreviewPoints,
  buildEnvironmentSurfaces,
  clientPointToScene,
  computeSceneBounds,
  describeSelectedTarget,
  describeLocationLabel,
  describeRoutePreviewDestination,
  describeVehicleName,
  describeVehicleOperationalSummary,
  describeSceneViewMode,
  findEdgeById,
  findNodePosition,
  findVehicleById,
  formatHeadingDegrees,
  formatMeters,
  formatMaybeNumber,
  formatSpeedPerSecond,
  formatSeconds,
  humanizeIdentifier,
  maxMotionTime,
  resolveScenePlaceDestination,
  spacingEnvelopeFromVehicle,
  renderVehicleEnvelope,
  renderVehicleGlyph,
  sampleDisplayedVehicles,
  sampleTrafficSnapshot,
  sceneProjectionTransform,
  sceneViewModes,
  scaleX,
  scaleY,
  toPointString,
  toScaledPointString,
  toSmoothPathString,
} from "../viewModel";
import { PanelHeader } from "./shared/PanelHeader";
import type {
  Bounds,
  BundlePayload,
  HoverTarget,
  LayerState,
  Position3,
  RouteDestinationMarker,
  RoutePlanDestination,
  SelectedTarget,
  SceneViewMode,
  RoutePreviewPayload,
  ViewportState,
} from "../types";

type SceneViewportProps = {
  bundle: BundlePayload | null;
  motionClockS: number;
  viewport: ViewportState;
  layers: LayerState;
  selectedTarget: SelectedTarget | null;
  selectedVehicleIds: number[];
  editorEnabled: boolean;
  hoverTarget: HoverTarget | null;
  setHoverTarget: Dispatch<SetStateAction<HoverTarget | null>>;
  sceneRef: RefObject<SVGSVGElement | null>;
  minimapRef: RefObject<SVGSVGElement | null>;
  onPan: (deltaX: number, deltaY: number) => void;
  onZoom: (factor: number) => void;
  onFit: () => void;
  onFocusSelected: () => void;
  onToggleLayer: (layer: keyof LayerState) => void;
  onSelectVehicle: (vehicleId: number | undefined, options?: { additive?: boolean }) => void;
  onSelectRoad: (roadId: string | undefined) => void;
  onSelectArea: (areaId: string | undefined) => void;
  onSelectQueue: (roadId: string | undefined) => void;
  onSelectHazard: (edgeId: number | undefined) => void;
  selectedRouteDestination: RoutePlanDestination | null;
  onSelectRouteDestination: (destination: RoutePlanDestination) => void;
  activeRoutePreview: RoutePreviewPayload | null;
  onMinimapClick: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseMove: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseUp: () => void;
  onSceneMouseLeave: () => void;
  onBeginNodeDrag: (event: MouseEvent<SVGCircleElement>, node: { node_id?: number; position?: Position3 }) => void;
  onBeginRoadPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    roadId: string,
    pointIndex: number,
    z: number,
  ) => void;
  onBeginAreaPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    areaId: string,
    pointIndex: number,
    z: number,
  ) => void;
  sceneViewMode: SceneViewMode;
  onSceneViewModeChange: (mode: SceneViewMode) => void;
};

export function SceneViewport({
  bundle,
  motionClockS,
  viewport,
  layers,
  selectedTarget,
  selectedVehicleIds,
  editorEnabled,
  hoverTarget,
  setHoverTarget,
  sceneRef,
  minimapRef,
  onPan,
  onZoom,
  onFit,
  onFocusSelected,
  onToggleLayer,
  onSelectVehicle,
  onSelectRoad,
  onSelectArea,
  onSelectQueue,
  onSelectHazard,
  selectedRouteDestination,
  onSelectRouteDestination,
  activeRoutePreview,
  onMinimapClick,
  onSceneMouseMove,
  onSceneMouseUp,
  onSceneMouseLeave,
  onBeginNodeDrag,
  onBeginRoadPointDrag,
  onBeginAreaPointDrag,
  sceneViewMode,
  onSceneViewModeChange,
}: SceneViewportProps): JSX.Element {
  const bounds = computeSceneBounds(bundle);
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const trafficRoadById = new Map(
    trafficRoadStates
      .filter((state) => state.road_id)
      .map((state) => [state.road_id as string, state]),
  );
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle"
      ? selectedTarget.vehicleId
      : selectedVehicleIds[0] ??
        bundle?.command_center?.vehicle_inspections?.[0]?.vehicle_id ??
        null;
  const selectedVehicle = findVehicleById(bundle, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? (bundle?.command_center?.vehicle_inspections ?? []).find(
        (inspection) => inspection.vehicle_id === selectedVehicleId,
      ) ?? null
    : null;
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedArea =
    selectedTarget?.kind === "area"
      ? (bundle?.render_geometry?.areas ?? []).find(
          (area) => area.area_id === selectedTarget.areaId,
        ) ?? null
      : null;
  const selectedQueueRecord =
    selectedTarget?.kind === "queue"
      ? (bundle?.traffic_baseline?.queue_records ?? []).find(
          (record) => record.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedHazardEdge =
    selectedTarget?.kind === "hazard"
      ? findEdgeById(bundle?.map_surface?.edges ?? [], selectedTarget.edgeId)
      : null;
  const blockedEdgeIds = [...(bundle?.snapshot?.blocked_edge_ids ?? [])].sort(
    (left, right) => left - right,
  );
  const routePreviews = activeRoutePreview !== null ? [activeRoutePreview] : bundle?.command_center?.route_previews ?? [];
  const movingVehicleCount = displayedVehicles.filter(
    (vehicle) => (vehicle.speed ?? 0) > 0.05 || vehicle.operational_state === "moving",
  ).length;
  const waitingVehicleCount = displayedVehicles.filter(
    (vehicle) => vehicle.operational_state === "waiting" || vehicle.operational_state === "queued",
  ).length;
  const selectedRoutePreviewRoadIds = new Set(
    (bundle?.render_geometry?.roads ?? [])
      .filter((road) =>
        routePreviews.some(
          (preview) =>
            selectedVehicleIds.includes(preview.vehicle_id ?? -1) &&
            (preview.edge_ids ?? []).some((edgeId) => (road.edge_ids ?? []).includes(edgeId)),
        ),
      )
      .map((road) => road.road_id)
      .filter((roadId): roadId is string => Boolean(roadId)),
  );
  const routeDestinationMarkers = [...routePreviews.reduce((markers, preview) => {
    const destinationNodeId = preview.destination_node_id;
    if (destinationNodeId === undefined) {
      return markers;
    }
    const position = findNodePosition(bundle?.map_surface?.nodes ?? [], destinationNodeId);
    if (!position) {
      return markers;
    }
    const selected = routePreviews[0]?.vehicle_id !== undefined
      ? routePreviews[0].vehicle_id === preview.vehicle_id
      : false;
    const label = describeRoutePreviewDestination(bundle, preview, {
      includeNodeId: false,
    }).replace(/ · [0-9.]+m$/, "");
    const existingMarker = markers.get(destinationNodeId);
    if (!existingMarker || (!existingMarker.selected && selected)) {
      markers.set(destinationNodeId, {
        destinationNodeId,
        position,
        selected,
        previewVehicleId: preview.vehicle_id,
        label,
        detail: `V${preview.vehicle_id ?? "?"}`,
      });
    }
    return markers;
  }, new Map<number, RouteDestinationMarker>()).values()];
  const selectedRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === selectedVehicleId) ??
    routePreviews[0] ??
    null;
  const selectedVehicleStatusSummary = describeVehicleOperationalSummary(
    bundle,
    selectedVehicle,
    selectedInspection,
    selectedRoutePreview,
  );
  const selectedRoutePreviewSummary = describeRoutePreviewDestination(bundle, selectedRoutePreview, {
    includeNodeId: true,
  });
  const sceneSelectionHoverTarget = (() => {
    if (!selectedTarget) {
      return null;
    }
    if (selectedTarget.kind === "vehicle") {
      return {
        label: describeVehicleName(selectedVehicle),
        detail: selectedVehicleStatusSummary,
      };
    }
    if (selectedTarget.kind === "road") {
      return {
        label: humanizeIdentifier(selectedTarget.roadId),
        detail:
          selectedRoad !== null
            ? `${selectedRoad.road_class ?? "road"} · ${selectedRoad.directionality ?? "unknown"} · ${
                selectedRoad.lane_count ?? 0
              } lane(s)`
            : "Road selected",
      };
    }
    if (selectedTarget.kind === "area") {
      return {
        label: humanizeIdentifier(selectedArea?.area_id ?? selectedTarget.areaId),
        detail: selectedArea?.kind ?? "area",
      };
    }
    if (selectedTarget.kind === "queue") {
      return {
        label: `Queue ${humanizeIdentifier(selectedTarget.roadId)}`,
        detail: `${selectedQueueRecord?.vehicle_ids?.length ?? 0} vehicle(s) queued`,
      };
    }
    if (selectedTarget.kind === "hazard") {
      return {
        label: `Blocked edge ${selectedTarget.edgeId}`,
        detail:
          selectedHazardEdge !== null
            ? `Edge ${selectedHazardEdge.edge_id} · temporary closure`
            : "Conflict / hazard overlay",
      };
    }
    return null;
  })();
  const sceneSurfaceTransform = sceneProjectionTransform(sceneViewMode, bounds);
  const sceneModeSummary = describeSceneViewMode(sceneViewMode);
  const environmentSurfaces = buildEnvironmentSurfaces(bundle, selectedTarget);
  const shouldShowRoutes = layers.routes || routePreviews.length > 0;

  function midpointFromPoints(points: Position3[] | undefined): Position3 | null {
    if (!points || points.length === 0) {
      return null;
    }
    const [sumX, sumY, sumZ] = points.reduce(
      (accumulator, [x, y, z = 0]) => [accumulator[0] + x, accumulator[1] + y, accumulator[2] + z],
      [0, 0, 0],
    );
    return [sumX / points.length, sumY / points.length, sumZ / points.length];
  }

  const selectedTargetAnchor = (() => {
    if (!selectedTarget) {
      return null;
    }
    if (selectedTarget.kind === "vehicle") {
      return selectedVehicle?.position ?? null;
    }
    if (selectedTarget.kind === "road") {
      return midpointFromPoints(selectedRoad?.centerline);
    }
    if (selectedTarget.kind === "area") {
      return midpointFromPoints(selectedArea?.polygon);
    }
    if (selectedTarget.kind === "queue") {
      const queueRoad = (bundle?.render_geometry?.roads ?? []).find(
        (road) => road.road_id === selectedTarget.roadId,
      );
      return midpointFromPoints(queueRoad?.centerline);
    }
    if (selectedTarget.kind === "hazard") {
      if (selectedHazardEdge === null) {
        return null;
      }
      const start = findNodePosition(bundle?.map_surface?.nodes ?? [], selectedHazardEdge.start_node_id);
      const end = findNodePosition(bundle?.map_surface?.nodes ?? [], selectedHazardEdge.end_node_id);
      if (!start || !end) {
        return null;
      }
      return [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2];
    }
    return null;
  })();

  const minimapRect = {
    x: ((viewport.x - bounds.minX) / bounds.width) * 100,
    y: ((viewport.y - bounds.minY) / bounds.height) * 100,
    width: (viewport.width / bounds.width) * 100,
    height: (viewport.height / bounds.height) * 100,
  };
  const minimapViewportCoverage = `${Math.max(1, Math.round((viewport.width / bounds.width) * 100))}% wide · ${Math.max(
    1,
    Math.round((viewport.height / bounds.height) * 100),
  )}% tall`;
  const minimapSelectedVehicleLabel =
    selectedVehicle !== null
      ? `Selected ${describeVehicleName(selectedVehicle)}`
      : selectedVehicleIds.length > 0
        ? `Fleet ${selectedVehicleIds.length} selected`
        : "No selected vehicle yet";
  const minimapBlockedContextLabel =
    selectedTarget?.kind === "hazard"
      ? `Blocked edge ${selectedTarget.edgeId}`
      : blockedEdgeIds.length > 0
        ? `${blockedEdgeIds.length} blocked edge${blockedEdgeIds.length === 1 ? "" : "s"}`
        : "No blocked edges yet";
  const operateSelectedVehicleSummary =
    selectedVehicle !== null
      ? selectedVehicleStatusSummary
      : selectedVehicleIds.length > 0
        ? `Fleet selection active · ${selectedVehicleIds.length} vehicle(s)`
        : "No vehicle selected yet";
  const operateSelectedContextSummary =
    selectedInspection !== null
      ? `${describeLocationLabel(bundle, selectedInspection.current_node_id ?? null, {
          includeNodeId: true,
        })} · ETA ${formatSeconds(selectedInspection.eta_s ?? null)} · ${
          selectedInspection.current_job_id ?? "no job"
        }`
      : "Select a vehicle on the map or from the roster to open inspection details.";
  const operateSelectedTargetSummary = describeSelectedTarget(selectedTarget, selectedVehicleId);
  const operateRoutePreviewSummary =
    selectedRoutePreview !== null
      ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id ?? null)} · ${describeLocationLabel(
          bundle,
          selectedRoutePreview.destination_node_id ?? null,
          { includeNodeId: true },
        )} · ${
          selectedRoutePreview.is_actionable ? "actionable" : "pending"
        }`
      : "Waiting for route preview";
  const operateRoutePreviewDetail =
    selectedRoutePreview !== null
      ? `${selectedRoutePreview.reason ?? "No reason provided"}${
          selectedRoutePreview.total_distance !== undefined
            ? ` · ${formatMeters(selectedRoutePreview.total_distance)}`
            : ""
        }`
      : "Choose a vehicle and destination, then preview the route to populate node, edge, and distance details.";

  function stopDragging(): void {
    setHoverTarget(null);
  }

  return (
    <section className="stage panel" aria-labelledby="scene-title">
      <PanelHeader
        eyebrow="Scene Region"
        title="Operations Viewport"
        titleId="scene-title"
        lede="Projected scene surface with quiet defaults. Hover or select a surface for detail."
        meta={
          <div className="status-stack">
            <span className="status-pill">{sceneModeSummary}</span>
            <span className="status-pill secondary">Quiet default</span>
            <span className="status-pill accent">Select for details</span>
          </div>
        }
      />

      <div className="scene-toolbar" aria-label="Scene toolbar">
        <div className="tool-group">
          <button className="scene-button" type="button" onClick={() => onPan(0, -0.18)}>
            Pan Up
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(-0.18, 0)}>
            Pan Left
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(0.18, 0)}>
            Pan Right
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(0, 0.18)}>
            Pan Down
          </button>
        </div>
        <div className="tool-group">
          <button className="scene-button" type="button" onClick={() => onZoom(0.82)}>
            Zoom In
          </button>
          <button className="scene-button" type="button" onClick={() => onZoom(1.2)}>
            Zoom Out
          </button>
          <button className="scene-button" type="button" onClick={onFit}>
            Fit Scene
          </button>
          <button
            className="scene-button"
            type="button"
            onClick={onFocusSelected}
            disabled={selectedVehicle === null}
          >
            Focus Selected
          </button>
        </div>
        <div className="tool-group" aria-label="Scene projection modes">
          {sceneViewModes.map((mode) => (
            <button
              key={mode.id}
              className={`scene-button scene-button-mode ${
                sceneViewMode === mode.id ? "scene-button-active" : ""
              }`}
              type="button"
              aria-pressed={sceneViewMode === mode.id}
              onClick={() => onSceneViewModeChange(mode.id)}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      <div className="layer-toolbar" aria-label="Layer toggles">
        {([
          ["roads", "Roads"],
          ["vehicles", "Vehicles"],
          ["routes", "Routes"],
          ["areas", "Areas"],
          ["intersections", "Intersections"],
          ["reservations", "Reservations"],
          ["hazards", "Hazards"],
        ] as Array<[keyof LayerState, string]>).map(([layer, label]) => (
          <button
            key={layer}
            className={`layer-chip ${layers[layer] ? "layer-chip-active" : ""}`}
            type="button"
            aria-pressed={layers[layer]}
            onClick={() => onToggleLayer(layer)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="stage-grid">
        <div className="stage-canvas-frame">
          <div className="scene-rim scene-rim-top" aria-hidden="true" />
          <div className="scene-rim scene-rim-bottom" aria-hidden="true" />
          <svg
            ref={sceneRef as unknown as Ref<SVGSVGElement>}
            className={`stage-canvas scene-canvas scene-canvas-${sceneViewMode}`}
            viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
            aria-label="Simulation scene graph"
            onMouseLeave={() => {
              setHoverTarget(null);
              stopDragging();
              onSceneMouseLeave();
            }}
            onMouseMove={onSceneMouseMove}
            onMouseUp={onSceneMouseUp}
          >
            <g className={`scene-surface scene-surface-${sceneViewMode}`} transform={sceneSurfaceTransform || undefined}>
              <rect
                x={bounds.minX}
                y={bounds.minY}
                width={bounds.width}
                height={bounds.height}
                className="scene-backdrop"
              />

              <g className="scene-environment scene-environment-base">
                {environmentSurfaces.map((surface) => {
                  const points = toPointString(surface.polygon);
                  if (!points) {
                    return null;
                  }
                  const shadowTransform =
                    surface.formKind === "recessed"
                      ? "translate(-0.06 -0.08)"
                      : surface.formKind === "raised"
                        ? "translate(0.08 0.1)"
                        : "translate(0.04 0.05)";
                  const selectable = surface.selectable ?? false;
                  const surfacePosition = midpointFromPoints(surface.polygon) ?? [0, 0, 0];
                  return (
                    <g
                      key={surface.surfaceId}
                      className={[
                        "scene-environment-form",
                        `scene-environment-form-${surface.formKind}`,
                        surface.selected ? "selected" : "",
                        selectable ? "scene-environment-form-selectable" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={
                        selectable
                          ? () => {
                              onSelectArea(surface.surfaceId);
                              const destination = resolveScenePlaceDestination(bundle, {
                                kind: "area",
                                label: surface.label ?? humanizeIdentifier(surface.surfaceId),
                                detail: surface.detail ?? "area",
                                position: surfacePosition,
                              });
                              if (destination) {
                                onSelectRouteDestination(destination);
                              }
                            }
                          : undefined
                      }
                      onMouseEnter={() =>
                        setHoverTarget({
                          label: surface.label ?? surface.surfaceId,
                          detail: surface.detail ?? "environment surface",
                        })
                      }
                    >
                      <polygon
                        points={points}
                        className={`scene-environment-shadow scene-environment-shadow-${surface.formKind}`}
                        transform={shadowTransform}
                      />
                      <polygon
                        points={points}
                        className={`scene-environment-surface scene-environment-surface-${surface.formKind} ${
                          surface.selected ? "selected" : ""
                        }`}
                      />
                      <polygon
                        points={points}
                        className={`scene-environment-silhouette scene-environment-silhouette-${surface.formKind}`}
                      />
                    </g>
                  );
                })}
              </g>

              {layers.areas &&
                environmentSurfaces
                  .filter((surface) => surface.selectable)
                  .map((surface) => {
                    const points = toPointString(surface.polygon);
                    if (!points) {
                      return null;
                    }
                    return (
                      <polygon
                        key={`area-overlay-${surface.surfaceId}`}
                        points={points}
                        className={`scene-environment-overlay scene-environment-overlay-area ${
                          surface.selected ? "selected" : ""
                        }`}
                      />
                    );
                  })}

              {layers.roads &&
                (bundle?.render_geometry?.roads ?? []).map((road, index) => {
                  const roadPath = toSmoothPathString(road.centerline);
                  if (!roadPath) {
                    return null;
                  }
                  const roadWidth = Math.min(Math.max((road.width_m ?? 1.4) * 0.34, 0.4), 1.72);
                  const roadTraffic = trafficRoadById.get(road.road_id ?? "");
                  return (
                    <g key={road.road_id ?? `road-${index}`}>
                      <path
                        d={roadPath}
                        className="scene-road-shadow"
                        strokeWidth={roadWidth + 0.34}
                      />
                      <path
                        d={roadPath}
                        className={`scene-road scene-road-${road.road_class ?? "connector"} ${
                          selectedTarget?.kind === "road" && selectedTarget.roadId === road.road_id
                            ? "selected"
                            : ""
                        }`}
                        strokeWidth={roadWidth}
                        onClick={() => {
                          onSelectRoad(road.road_id);
                          const destination = resolveScenePlaceDestination(bundle, {
                            kind: "road",
                            label: humanizeIdentifier(road.road_id),
                            detail: road.road_class ?? "road",
                            position: midpointFromPoints(road.centerline) ?? [0, 0, 0],
                          });
                          if (destination) {
                            onSelectRouteDestination(destination);
                          }
                        }}
                        onMouseEnter={() => {
                          setHoverTarget({
                            label: humanizeIdentifier(road.road_id),
                            detail: roadTraffic
                              ? `${road.directionality ?? "unknown"} · ${
                                  road.lane_count ?? 0
                                } lane(s) · ${roadTraffic.congestion_level} · ${
                                  roadTraffic.queued_vehicle_ids?.length ?? 0
                                } queued`
                              : `${road.directionality ?? "unknown"} · ${
                                  road.lane_count ?? 0
                                } lane(s)`,
                          });
                        }}
                      />
                      <path
                        d={roadPath}
                        className="scene-road-ribbon"
                        strokeWidth={Math.max(roadWidth * 0.42, 0.14)}
                      />
                    </g>
                  );
                })}

              {layers.intersections &&
                environmentSurfaces
                  .filter((surface) => !surface.selectable)
                  .map((surface) => {
                    const intersectionPath = toPointString(surface.polygon);
                    if (!intersectionPath) {
                      return null;
                    }
                    return (
                      <polygon
                        key={`intersection-overlay-${surface.surfaceId}`}
                        points={intersectionPath}
                        className="scene-environment-overlay scene-environment-overlay-intersection"
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: surface.label ?? surface.surfaceId,
                            detail: surface.detail ?? "intersection",
                          })
                        }
                      />
                    );
                  })}

              {layers.roads &&
                (bundle?.render_geometry?.lanes ?? []).map((lane, index) => (
                  <polyline
                    key={lane.lane_id ?? `lane-${index}`}
                    points={toPointString(lane.centerline)}
                    className={`scene-lane scene-lane-${lane.directionality ?? "forward"}`}
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: lane.lane_id ?? "lane",
                        detail: `${lane.lane_role ?? "travel"} · ${lane.directionality ?? "forward"}`,
                      })
                    }
                  />
                ))}

              {layers.roads &&
                (bundle?.render_geometry?.turn_connectors ?? []).map((connector, index) => (
                  <polyline
                    key={connector.connector_id ?? `connector-${index}`}
                    points={toPointString(connector.centerline)}
                    className="scene-turn-connector"
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: connector.connector_id ?? "connector",
                        detail: connector.connector_type ?? "turn connector",
                      })
                    }
                  />
                ))}

              {layers.roads &&
                (bundle?.render_geometry?.stop_lines ?? []).map((stopLine, index) => (
                  <line
                    key={stopLine.stop_line_id ?? `stop-line-${index}`}
                    x1={stopLine.segment?.[0]?.[0] ?? 0}
                    y1={stopLine.segment?.[0]?.[1] ?? 0}
                    x2={stopLine.segment?.[1]?.[0] ?? 0}
                    y2={stopLine.segment?.[1]?.[1] ?? 0}
                    className="scene-stop-line"
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: stopLine.stop_line_id ?? "stop line",
                        detail: stopLine.control_kind ?? "stop control",
                      })
                    }
                  />
                ))}

              {layers.roads &&
                (bundle?.render_geometry?.merge_zones ?? []).map((zone, index) => (
                  <polygon
                    key={zone.merge_zone_id ?? `merge-zone-${index}`}
                    points={toPointString(zone.polygon)}
                    className="scene-merge-zone"
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: zone.merge_zone_id ?? "merge zone",
                        detail: `${zone.kind ?? "merge"} · ${(zone.lane_ids ?? []).length} lane(s)`,
                      })
                    }
                  />
                ))}

              {layers.reservations &&
                (bundle?.traffic_baseline?.queue_records ?? []).map((record, queueIndex) => {
                  const road = (bundle?.render_geometry?.roads ?? []).find(
                    (entry) => entry.road_id === record.road_id,
                  );
                  const roadTraffic =
                    typeof record.road_id === "string"
                      ? trafficRoadById.get(record.road_id) ?? null
                      : null;
                  const roadPath = toSmoothPathString(road?.centerline);
                  if (!roadPath) {
                    return null;
                  }
                  const roadWidth = Math.min(Math.max((road?.width_m ?? 1.4) * 0.34, 0.4), 1.72);
                  return (
                    <path
                      key={`reservation-${queueIndex}`}
                      d={roadPath}
                      className={`scene-reservation scene-queue-overlay ${
                        selectedTarget?.kind === "queue" &&
                        selectedTarget.roadId === record.road_id
                          ? "selected"
                          : selectedRoutePreviewRoadIds.has(record.road_id ?? "")
                            ? "selected preview"
                            : ""
                      }`}
                      strokeWidth={roadWidth + 0.42}
                      onClick={() => onSelectQueue(record.road_id ?? undefined)}
                      onMouseEnter={() =>
                        setHoverTarget({
                          label: `Queue ${humanizeIdentifier(record.road_id)}`,
                          detail: `${roadTraffic?.queued_vehicle_ids?.length ?? 0} vehicle(s) queued`,
                        })
                      }
                    />
                  );
                })}

              {layers.vehicles &&
                displayedVehicles.map((vehicle, vehicleIndex) => {
                  const position = vehicle.position ?? [0, 0, 0];
                  const isSelected = selectedVehicleIds.includes(vehicle.vehicle_id ?? -1);
                  const vehicleSpeed = vehicle.speed ?? 0;
                  const isMoving = vehicleSpeed > 0.05 || vehicle.operational_state === "moving";
                  const isWaiting =
                    vehicle.operational_state === "waiting" || vehicle.operational_state === "queued";
                  const isRouteTracked = selectedRoutePreview?.vehicle_id === vehicle.vehicle_id;
                  const selectionEnvelopeLength = Math.max(
                    vehicle.spacing_envelope_m ?? spacingEnvelopeFromVehicle(vehicle),
                    0.9,
                  );
                  const selectionEnvelopeWidth = Math.max((vehicle.body_width_m ?? 0.62) * 1.9, 1);
                  return (
                    <g
                      key={vehicle.vehicle_id ?? `vehicle-${vehicleIndex}`}
                      className={[
                        "scene-vehicle",
                        isSelected ? "selected" : "",
                        isMoving ? "moving" : "settled",
                        isWaiting ? "waiting" : "",
                        isRouteTracked ? "route-following" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={(event) =>
                        onSelectVehicle(vehicle.vehicle_id, {
                          additive: event.shiftKey || event.metaKey || event.ctrlKey,
                        })
                      }
                      onMouseEnter={() =>
                        setHoverTarget({
                          label: `${describeVehicleName(vehicle)} · V${vehicle.vehicle_id ?? vehicleIndex}`,
                          detail: `${humanizeIdentifier(vehicle.operational_state ?? "unknown_state").toLowerCase()} · ${
                            vehicle.lane_id ?? "lane-unassigned"
                          } · ${formatMeters(vehicle.spacing_envelope_m ?? null)} envelope`,
                        })
                      }
                    >
                      {isSelected ? (
                        <rect
                          x={position[0] - selectionEnvelopeLength * 0.56}
                          y={position[1] - selectionEnvelopeWidth * 0.5}
                          width={selectionEnvelopeLength * 1.12}
                          height={selectionEnvelopeWidth}
                          rx={0.28}
                          className="vehicle-selection-ring"
                        />
                      ) : null}
                      <g
                        transform={`translate(${position[0]} ${position[1]}) rotate(${((vehicle.heading_rad ?? 0) * 180) / Math.PI})`}
                      >
                        {isMoving ? (
                          <line
                            x1={-Math.max((vehicle.body_length_m ?? 1.12) * 0.42, 0.42)}
                            y1={0}
                            x2={Math.max((vehicle.body_length_m ?? 1.12) * 0.24, 0.26)}
                            y2={0}
                            className="vehicle-motion-trail"
                          />
                        ) : null}
                        {renderVehicleEnvelope(vehicle)}
                        {renderVehicleGlyph(vehicle)}
                      </g>
                    </g>
                  );
                })}

              {shouldShowRoutes &&
                routeDestinationMarkers.map((marker) => (
                  <g
                    key={`route-destination-${marker.destinationNodeId}`}
                    className={`scene-destination scene-route-endpoint ${
                      marker.selected ? "selected" : ""
                    }`}
                    transform={`translate(${marker.position[0]} ${marker.position[1]})`}
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: marker.label,
                        detail: marker.detail ?? "Route destination",
                      })
                    }
                  >
                    <circle r={marker.selected ? 1.08 : 0.86} className="scene-destination-threshold" />
                    <circle r={marker.selected ? 0.38 : 0.3} className="scene-destination-core" />
                  </g>
                ))}

              {shouldShowRoutes &&
                routePreviews.map((preview, previewIndex) => {
                  const routePoints = buildRoutePreviewPoints(
                    preview,
                    bundle?.map_surface?.nodes ?? [],
                  );
                  const routePath = toSmoothPathString(routePoints);
                  if (!routePath) {
                    return null;
                  }
                  return (
                    <path
                      key={`route-preview-${previewIndex}`}
                      d={routePath}
                      className={`scene-route-preview ${
                        preview.vehicle_id === selectedVehicleId ? "selected" : ""
                      }`}
                      onMouseEnter={() =>
                        setHoverTarget({
                          label: `Route preview V${preview.vehicle_id ?? "?"}`,
                          detail: preview.reason ?? "actionable preview",
                        })
                      }
                    />
                  );
                })}

              {selectedTargetAnchor && sceneSelectionHoverTarget ? (
                <g
                  className="scene-selection-popup"
                  transform={`translate(${selectedTargetAnchor[0]} ${selectedTargetAnchor[1] - 1.15})`}
                  aria-label="Map selection popup"
                >
                  <rect
                    x={-2.8}
                    y={-1.12}
                    width={5.6}
                    height={1.28}
                    rx={0.22}
                    className="scene-selection-popup-card"
                  />
                  <text x={-2.42} y={-0.64} className="scene-selection-popup-title">
                    {sceneSelectionHoverTarget.label}
                  </text>
                  <text x={-2.42} y={-0.26} className="scene-selection-popup-detail">
                    {sceneSelectionHoverTarget.detail}
                  </text>
                </g>
              ) : null}

              {layers.hazards &&
                blockedEdgeIds.map((edgeId, blockedIndex) => {
                  const edge = findEdgeById(bundle?.map_surface?.edges ?? [], edgeId);
                  const start = edge
                    ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                    : null;
                  const end = edge
                    ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                    : null;
                  if (!start || !end) {
                    return null;
                  }
                  return (
                    <line
                      key={`hazard-${blockedIndex}`}
                      x1={start[0]}
                      y1={start[1]}
                      x2={end[0]}
                      y2={end[1]}
                      className={`scene-hazard ${
                        selectedTarget?.kind === "hazard" &&
                        selectedTarget.edgeId === edgeId
                          ? "selected"
                          : ""
                      }`}
                      onClick={() => onSelectHazard(edgeId)}
                      onMouseEnter={() =>
                        setHoverTarget({
                          label: `Blocked edge ${edgeId}`,
                          detail: "Conflict / hazard overlay",
                        })
                      }
                    />
                  );
                })}

              {editorEnabled &&
                (bundle?.map_surface?.nodes ?? []).map((node, index) => {
                  if (node.node_id === undefined || !node.position) {
                    return null;
                  }
                  return (
                    <circle
                      key={node.node_id ?? `node-handle-${index}`}
                      cx={node.position[0]}
                      cy={node.position[1]}
                      r={0.32}
                      className="scene-edit-handle node"
                      onMouseDown={(event) => onBeginNodeDrag(event, node)}
                    />
                  );
                })}

              {editorEnabled &&
                selectedRoad?.centerline?.map((point, index) => (
                  <circle
                    key={`${selectedRoad.road_id ?? "road"}-point-${index}`}
                    cx={point[0]}
                    cy={point[1]}
                    r={0.3}
                    className="scene-edit-handle road"
                    onMouseDown={(event) =>
                      onBeginRoadPointDrag(
                        event,
                        selectedRoad.road_id ?? "road",
                        index,
                        point[2] ?? 0,
                      )
                    }
                  />
                ))}

              {editorEnabled &&
                selectedArea?.polygon?.map((point, index) => (
                  <circle
                    key={`${selectedArea.area_id ?? "area"}-point-${index}`}
                    cx={point[0]}
                    cy={point[1]}
                    r={0.3}
                    className="scene-edit-handle area"
                    onMouseDown={(event) =>
                      onBeginAreaPointDrag(
                        event,
                        selectedArea.area_id ?? "area",
                        index,
                        point[2] ?? 0,
                      )
                    }
                  />
                ))}
            </g>
          </svg>

          <div className="scene-overlay-shell">
            <div className="scene-overlay-minimap">
              <div className="scene-minimap-frame">
                <div className="scene-minimap-head">
                  <span className="scene-minimap-label">Minimap</span>
                  <span className="minimap-orientation-pill">{sceneViewMode === "iso" ? "Iso" : "Birdseye"}</span>
                </div>
                <svg
                  ref={minimapRef as unknown as Ref<SVGSVGElement>}
                  className="minimap"
                  viewBox={`0 0 100 100`}
                  aria-label="Scene minimap"
                  onClick={onMinimapClick}
                >
                  <rect x={0} y={0} width={100} height={100} className="minimap-bg" />
                  {(bundle?.render_geometry?.roads ?? []).map((road, index) => (
                    <polyline
                      key={road.road_id ?? `minimap-road-${index}`}
                      points={toScaledPointString(road.centerline, bounds)}
                      className="minimap-road"
                    />
                  ))}
                  {layers.hazards &&
                    blockedEdgeIds.map((edgeId) => {
                      const edge = findEdgeById(bundle?.map_surface?.edges ?? [], edgeId);
                      const start = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                        : null;
                      const end = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                        : null;
                      if (!start || !end) {
                        return null;
                      }
                      return (
                        <line
                          key={`minimap-hazard-${edgeId}`}
                          x1={scaleX(start[0], bounds)}
                          y1={scaleY(start[1], bounds)}
                          x2={scaleX(end[0], bounds)}
                          y2={scaleY(end[1], bounds)}
                          className={`minimap-hazard ${
                            selectedTarget?.kind === "hazard" && selectedTarget.edgeId === edgeId
                              ? "selected"
                              : ""
                          }`}
                        />
                      );
                    })}
                  {displayedVehicles.map((vehicle, index) => {
                    const isPrimarySelected = vehicle.vehicle_id === selectedVehicleId;
                    const isSelectedFleetVehicle = selectedVehicleIds.includes(vehicle.vehicle_id ?? -1);
                    const isMoving = (vehicle.speed ?? 0) > 0.05 || vehicle.operational_state === "moving";
                    const isWaiting =
                      vehicle.operational_state === "waiting" || vehicle.operational_state === "queued";
                    const isRouteTracked = selectedRoutePreview?.vehicle_id === vehicle.vehicle_id;
                    return (
                      <g
                        key={vehicle.vehicle_id ?? `minimap-vehicle-${index}`}
                        className={`minimap-vehicle ${isPrimarySelected ? "selected" : isSelectedFleetVehicle ? "fleet-selected" : ""} ${
                          isMoving ? "moving" : "settled"
                        } ${isWaiting ? "waiting" : ""} ${isRouteTracked ? "route-following" : ""}`}
                      >
                        {isPrimarySelected ? (
                          <circle
                            cx={scaleX(vehicle.position?.[0] ?? 0, bounds)}
                            cy={scaleY(vehicle.position?.[1] ?? 0, bounds)}
                            r={3.1}
                            className="minimap-vehicle-halo"
                          />
                        ) : null}
                        <circle
                          cx={scaleX(vehicle.position?.[0] ?? 0, bounds)}
                          cy={scaleY(vehicle.position?.[1] ?? 0, bounds)}
                          r={isPrimarySelected ? 2.05 : isSelectedFleetVehicle ? 1.75 : 1.25}
                          className="minimap-vehicle-core"
                        />
                      </g>
                    );
                  })}
                  {routeDestinationMarkers.map((marker) => (
                    <g
                      key={`minimap-route-destination-${marker.destinationNodeId}`}
                      className={`minimap-destination ${marker.selected ? "selected" : ""}`}
                    >
                      <circle
                        cx={scaleX(marker.position[0], bounds)}
                        cy={scaleY(marker.position[1], bounds)}
                        r={marker.selected ? 2.0 : 1.55}
                        className="minimap-destination-threshold"
                      />
                      <circle
                        cx={scaleX(marker.position[0], bounds)}
                        cy={scaleY(marker.position[1], bounds)}
                        r={marker.selected ? 0.85 : 0.62}
                        className="minimap-destination-core"
                      />
                    </g>
                  ))}
                  <rect
                    x={minimapRect.x}
                    y={minimapRect.y}
                    width={minimapRect.width}
                    height={minimapRect.height}
                    rx={1.1}
                    ry={1.1}
                    className="minimap-viewport minimap-viewport-shadow"
                  />
                  <rect
                    x={minimapRect.x}
                    y={minimapRect.y}
                    width={minimapRect.width}
                    height={minimapRect.height}
                    rx={1.1}
                    ry={1.1}
                    className="minimap-viewport"
                  />
                </svg>
                <div className="scene-minimap-meta" aria-label="Minimap context">
                  <span className="selection-pill minimap-context-pill">{minimapSelectedVehicleLabel}</span>
                  <span className="selection-pill minimap-context-pill">
                    Fleet {displayedVehicles.length} · Moving {movingVehicleCount}
                  </span>
                  <span className="selection-pill minimap-context-pill">{minimapViewportCoverage}</span>
                  <span
                    className={`selection-pill minimap-context-pill ${
                      blockedEdgeIds.length > 0 || selectedTarget?.kind === "hazard"
                        ? "minimap-context-pill-alert"
                        : ""
                    }`}
                  >
                    {minimapBlockedContextLabel}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <aside className="overview-panel">
          <div className="overview-card operate-route-planning">
            <p className="eyebrow">Selection</p>
            <h3>Operator Context</h3>
            <div className="selection-strip">
              <span className="selection-pill">
                Fleet selection: {selectedVehicleIds.length} vehicle(s)
              </span>
              <span className="selection-pill">Current target: {operateSelectedTargetSummary}</span>
              <span className="selection-pill">
                Route preview:{" "}
                {selectedRoutePreview?.vehicle_id !== undefined
                  ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id)}`
                  : "waiting for preview"}
              </span>
            </div>
            <div className="operate-summary-grid">
              <section className="operate-context-card operate-context-card-compact">
                <p className="operate-card-label">Selected Context</p>
                <strong>{operateSelectedVehicleSummary}</strong>
                <p>{operateSelectedContextSummary}</p>
                <p className="operate-card-note">Target: {operateSelectedTargetSummary}</p>
              </section>
              <section className="operate-context-card operate-context-card-compact">
                <p className="operate-card-label">Route Preview</p>
                <strong>{operateRoutePreviewSummary}</strong>
                <p>{operateRoutePreviewDetail}</p>
                <p className="operate-card-note">Destination: {selectedRoutePreviewSummary}</p>
              </section>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
