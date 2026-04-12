import type { LiveBundleViewModel, Point2 } from "./liveBundle";
import type { FrontendUiState } from "../state/frontendUiState";

export type SelectionTarget =
  | { kind: "vehicle"; vehicleId: number }
  | { kind: "road"; roadId: string }
  | { kind: "intersection"; intersectionId: string }
  | { kind: "area"; areaId: string };

export type SelectionDetail = {
  label: string;
  value: string;
};

export type SelectionPresentation = {
  target: SelectionTarget | null;
  title: string;
  badge: string;
  summary: string;
  context: string;
  details: SelectionDetail[];
  notes: string[];
  focusPoints: Point2[];
};

export type FleetVehicleContext = {
  vehicleId: number;
  selected: boolean;
  state: string;
  stateClass: "moving" | "waiting" | "idle";
  title: string;
  summary: string;
  context: string;
  detail: string;
};

export type FleetVehicleGroup = {
  key: string;
  label: string;
  summary: string;
  count: number;
  selectedCount: number;
  vehicleIds: number[];
  vehicleSummaries: string[];
};

export type FleetRosterSummary = {
  selectionSource: "local" | "bundle" | "none";
  selectedVehicleIds: number[];
  leadVehicleId: number | null;
  totalVehicleCount: number;
  selectedVehicleCount: number;
  visibleVehicles: FleetVehicleContext[];
  selectedVehicles: FleetVehicleContext[];
  groups: FleetVehicleGroup[];
  summary: string;
  context: string;
  notes: string[];
};

export function resolveActiveSelectionTarget(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): SelectionTarget | null {
  if (uiState.selection.target !== null) {
    return uiState.selection.target;
  }

  if (uiState.selection.vehicleIds.length > 0) {
    return { kind: "vehicle", vehicleId: uiState.selection.vehicleIds[0] };
  }

  if (bundle.selectedVehicleIds.length > 0) {
    return { kind: "vehicle", vehicleId: bundle.selectedVehicleIds[0] };
  }

  return null;
}

export function resolveSelectionVehicleIds(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): number[] {
  if (uiState.selection.vehicleIds.length > 0) {
    return uniqueNumbers(uiState.selection.vehicleIds);
  }

  if (uiState.selection.target?.kind === "vehicle") {
    return [uiState.selection.target.vehicleId];
  }

  if (uiState.selection.target !== null) {
    return [];
  }

  return uniqueNumbers(bundle.selectedVehicleIds);
}

export function buildSelectionPresentation(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): SelectionPresentation | null {
  const target = resolveActiveSelectionTarget(bundle, uiState);
  if (target === null) {
    return null;
  }

  switch (target.kind) {
    case "vehicle":
      return buildVehiclePresentation(bundle, target.vehicleId);
    case "road":
      return buildRoadPresentation(bundle, target.roadId);
    case "intersection":
      return buildIntersectionPresentation(bundle, target.intersectionId);
    case "area":
      return buildAreaPresentation(bundle, target.areaId);
    default:
      return null;
  }
}

export function buildFleetRosterSummary(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): FleetRosterSummary {
  const selectedVehicleIds = resolveSelectionVehicleIds(bundle, uiState);
  const selectionSource = resolveSelectionSource(bundle, uiState);
  const selectedVehicleIdSet = new Set(selectedVehicleIds);
  const visibleVehicles = bundle.map.vehicles
    .map((vehicle) => buildFleetVehicleContext(bundle, vehicle.vehicleId, selectedVehicleIdSet.has(vehicle.vehicleId)))
    .sort((left, right) => {
      const selectedRank = Number(right.selected) - Number(left.selected);
      if (selectedRank !== 0) {
        return selectedRank;
      }

      const stateRank = fleetStateRank(left.stateClass) - fleetStateRank(right.stateClass);
      if (stateRank !== 0) {
        return stateRank;
      }

      return left.vehicleId - right.vehicleId;
    });
  const selectedVehicles = visibleVehicles.filter((vehicle) => vehicle.selected);
  const groups = groupFleetVehicles(visibleVehicles);
  const totalVehicleCount = visibleVehicles.length;
  const selectedVehicleCount = selectedVehicles.length;
  const leadVehicleId = selectedVehicleIds[0] ?? null;

  return {
    selectionSource,
    selectedVehicleIds,
    leadVehicleId,
    totalVehicleCount,
    selectedVehicleCount,
    visibleVehicles,
    selectedVehicles,
    groups,
    summary:
      selectedVehicleCount > 0
        ? `${selectedVehicleCount} selected from ${totalVehicleCount} visible vehicle(s)`
        : `${totalVehicleCount} visible vehicle(s) with no current fleet selection`,
    context:
      selectionSource === "local"
        ? "Frontend selection is carrying the current fleet focus."
        : selectionSource === "bundle"
          ? "Simulator bundle selection is driving the current fleet focus."
          : "No fleet selection is active yet.",
    notes: [
      `${groups.length} context group(s) across the visible fleet.`,
      selectedVehicleCount > 0 ? `Lead vehicle ${leadVehicleId}` : "Use the map to select one or more vehicles.",
    ],
  };
}

export function focusPointsForSelection(
  bundle: LiveBundleViewModel,
  selection: SelectionTarget | null,
): Point2[] {
  if (selection === null) {
    return [];
  }

  switch (selection.kind) {
    case "vehicle": {
      const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === selection.vehicleId);
      return vehicle === undefined ? [] : [vehicle.position];
    }
    case "road": {
      const road = bundle.map.roads.find((entry) => entry.roadId === selection.roadId);
      return road === undefined ? [] : road.centerline;
    }
    case "intersection": {
      const intersection = bundle.map.intersections.find((entry) => entry.intersectionId === selection.intersectionId);
      return intersection === undefined ? [] : intersection.polygon;
    }
    case "area": {
      const area = bundle.map.areas.find((entry) => entry.areaId === selection.areaId);
      return area === undefined ? [] : area.polygon;
    }
    default:
      return [];
  }
}

function buildFleetVehicleContext(
  bundle: LiveBundleViewModel,
  vehicleId: number,
  selected: boolean,
): FleetVehicleContext {
  const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const inspection = bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const preview = bundle.commandCenter.routePreviews.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const title = vehicle === null ? `Vehicle ${vehicleId}` : `Vehicle ${vehicle.vehicleId}`;
  const stateClass = vehicle?.stateClass ?? "idle";
  const state = vehicle?.state ?? inspection?.operationalState ?? "unknown";
  const summary = `${humanize(stateClass)} · ${humanize(state)}`;
  const contextParts = [
    inspection !== null && inspection.currentNodeId !== null ? `Node ${inspection.currentNodeId}` : null,
    inspection !== null && inspection.currentTaskType !== null ? humanize(inspection.currentTaskType) : null,
    inspection !== null && inspection.waitReason !== null ? `Wait ${humanize(inspection.waitReason)}` : null,
    inspection !== null && inspection.trafficControlState !== null ? humanize(inspection.trafficControlState) : null,
    inspection !== null && inspection.etaSeconds !== null ? `ETA ${inspection.etaSeconds.toFixed(1)}s` : null,
    preview !== null
      ? preview.isActionable
        ? `Preview to node ${preview.destinationNodeId}`
        : `Preview blocked: ${humanize(preview.reason ?? "unavailable")}`
      : null,
  ].filter((part): part is string => part !== null);
  const detail = contextParts.length > 0 ? contextParts.join(" · ") : "No additional vehicle context available.";

  return {
    vehicleId,
    selected,
    state,
    stateClass,
    title,
    summary,
    context: detail,
    detail,
  };
}

function groupFleetVehicles(vehicles: FleetVehicleContext[]): FleetVehicleGroup[] {
  const groups = new Map<string, FleetVehicleContext[]>();
  for (const vehicle of vehicles) {
    const entries = groups.get(vehicle.stateClass);
    if (entries === undefined) {
      groups.set(vehicle.stateClass, [vehicle]);
    } else {
      entries.push(vehicle);
    }
  }

  const orderedKeys: Array<FleetVehicleContext["stateClass"]> = ["moving", "waiting", "idle"];
  return orderedKeys
    .filter((key) => groups.has(key))
    .map((key) => {
      const entries = [...(groups.get(key) ?? [])].sort((left, right) => left.vehicleId - right.vehicleId);
      const selectedCount = entries.filter((entry) => entry.selected).length;
      return {
        key,
        label: humanize(key),
        summary:
          selectedCount > 0
            ? `${selectedCount} selected of ${entries.length}`
            : `${entries.length} vehicle(s) in ${humanize(key)} state`,
        count: entries.length,
        selectedCount,
        vehicleIds: entries.map((entry) => entry.vehicleId),
        vehicleSummaries: entries.map((entry) => `${entry.vehicleId} · ${entry.state}`),
      };
    });
}

function resolveSelectionSource(bundle: LiveBundleViewModel, uiState: FrontendUiState): "local" | "bundle" | "none" {
  if (uiState.selection.target !== null || uiState.selection.vehicleIds.length > 0 || uiState.selection.hoveredTarget !== null) {
    return "local";
  }

  if (bundle.selectedVehicleIds.length > 0) {
    return "bundle";
  }

  return "none";
}

function fleetStateRank(stateClass: FleetVehicleContext["stateClass"]): number {
  switch (stateClass) {
    case "moving":
      return 0;
    case "waiting":
      return 1;
    case "idle":
      return 2;
    default:
      return 3;
  }
}

function buildVehiclePresentation(bundle: LiveBundleViewModel, vehicleId: number): SelectionPresentation {
  const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const inspection = bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const routePreview = bundle.commandCenter.routePreviews.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const hasInspection = inspection !== null;
  const hasRoutePreview = routePreview !== null;
  const title = vehicle === null ? `Vehicle ${vehicleId}` : `Vehicle ${vehicle.vehicleId}`;
  const badge = inspection?.operationalState ?? vehicle?.state ?? "unknown";
  const summary =
    hasInspection && inspection.currentTaskType !== null
      ? humanize(inspection.currentTaskType)
      : hasRoutePreview
        ? routePreview.isActionable
          ? `Route preview to node ${routePreview.destinationNodeId}`
          : `Route preview blocked: ${humanize(routePreview.reason ?? "not available")}`
        : "No active route preview.";

  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "State", value: badge },
  ];
  if (hasInspection && inspection.currentTaskType !== null) {
    details.push({ label: "Task", value: humanize(inspection.currentTaskType) });
  }
  if (hasInspection && inspection.currentJobId !== null) {
    details.push({ label: "Job", value: inspection.currentJobId });
  }
  if (hasInspection && inspection.etaSeconds !== null) {
    details.push({ label: "ETA", value: `${inspection.etaSeconds.toFixed(1)}s` });
  }

  const notes = [
    hasInspection && inspection.currentNodeId !== null ? `Node ${inspection.currentNodeId}` : null,
    hasInspection && inspection.waitReason !== null ? `Waiting because of ${humanize(inspection.waitReason)}` : null,
    hasInspection && inspection.trafficControlDetail !== null ? inspection.trafficControlDetail : null,
    hasRoutePreview && routePreview.reason !== null ? `Preview: ${humanize(routePreview.reason)}` : null,
    hasRoutePreview && routePreview.renderDiagnostics.length > 0 ? routePreview.renderDiagnostics[0] : null,
  ].filter((item): item is string => item !== null);

  const context = [
    hasInspection && inspection.currentNodeId !== null ? `Node ${inspection.currentNodeId}` : null,
    hasInspection && inspection.assignedResourceId !== null ? `Resource ${inspection.assignedResourceId}` : null,
    hasInspection && inspection.waitReason !== null ? `Wait ${humanize(inspection.waitReason)}` : null,
  ]
    .filter((item): item is string => item !== null)
    .join(" · ");

  return {
    target: { kind: "vehicle", vehicleId },
    title,
    badge,
    summary,
    context: context.length > 0 ? context : "No extra context available.",
    details,
    notes,
    focusPoints: vehicle === null ? [] : [vehicle.position],
  };
}

function buildRoadPresentation(bundle: LiveBundleViewModel, roadId: string): SelectionPresentation {
  const road = bundle.map.roads.find((entry) => entry.roadId === roadId) ?? null;
  const title = road === null ? `Road ${roadId}` : formatRoadLabel(road);
  const badge = road?.blocked === true ? "Blocked" : "Open";
  const summary = road === null ? "Road geometry" : describeRoadImportance(road);
  const context = road === null ? "Road detail unavailable." : describeRoadContext(bundle, road);
  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "State", value: badge },
  ];

  if (road !== null) {
    details.push({ label: "Class", value: humanize(road.roadClass) });
    details.push({ label: "Direction", value: humanize(road.directionality) });
    details.push({ label: "Lanes", value: String(road.laneCount) });
    if (road.edgeIds.length > 0) {
      details.push({ label: "Edges", value: summarizeIdList(road.edgeIds, 4) });
    }
  }

  const notes =
    road === null
      ? []
      : [
          describeRoadImportance(road),
          describeRoadContext(bundle, road),
          road.edgeIds.length > 0
            ? `Road edge entry points: ${summarizeIdList(road.edgeIds, 4)}`
            : "No edge entry points are available for this road.",
        ];

  return {
    target: { kind: "road", roadId },
    title,
    badge,
    summary,
    context,
    details,
    notes,
    focusPoints: road === null ? [] : road.centerline,
  };
}

function buildIntersectionPresentation(bundle: LiveBundleViewModel, intersectionId: string): SelectionPresentation {
  const intersection = bundle.map.intersections.find((entry) => entry.intersectionId === intersectionId) ?? null;
  const title = intersection === null ? `Intersection ${intersectionId}` : formatIntersectionLabel(intersection);
  const badge = intersection === null ? "Intersection" : humanize(intersection.intersectionType);
  const summary =
    intersection === null
      ? "Junction geometry"
      : describeIntersectionImportance(intersection.intersectionType, intersection.polygon.length);
  const context =
    intersection === null
      ? "Intersection detail unavailable."
      : `${humanize(intersection.intersectionType)} junction in ${bundle.map.environment.displayName}`;
  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "Role", value: badge },
  ];

  if (intersection !== null) {
    details.push({ label: "Feature", value: "Control-relevant junction" });
    details.push({ label: "Vertices", value: String(intersection.polygon.length) });
  }

  const notes =
    intersection === null
      ? []
      : [
          describeIntersectionImportance(intersection.intersectionType, intersection.polygon.length),
          `Part of the ${bundle.map.environment.displayName} junction network.`,
        ];

  return {
    target: { kind: "intersection", intersectionId },
    title,
    badge,
    summary,
    context,
    details,
    notes,
    focusPoints: intersection === null ? [] : intersection.polygon,
  };
}

function buildAreaPresentation(bundle: LiveBundleViewModel, areaId: string): SelectionPresentation {
  const area = bundle.map.areas.find((entry) => entry.areaId === areaId) ?? null;
  const title = area === null ? `Area ${areaId}` : formatAreaLabel(area);
  const badge = area === null ? "Area" : humanize(area.category);
  const summary = area === null ? "Environmental context" : describeAreaImportance(area.category, area.kind);
  const context =
    area === null
      ? "Area detail unavailable."
      : `${humanize(area.category)} surface in ${bundle.map.environment.displayName}`;
  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "Role", value: badge },
  ];

  if (bundle.map.environment.displayName !== "unknown environment") {
    details.push({ label: "Environment", value: bundle.map.environment.displayName });
  }
  if (area !== null) {
    details.push({ label: "Kind", value: humanize(area.kind) });
  }
  if (area !== null && area.groupId !== null) {
    details.push({ label: "Group", value: humanize(area.groupId) });
  }

  const notes =
    area === null
      ? []
      : [
          describeAreaImportance(area.category, area.kind),
          `Part of the ${bundle.map.environment.displayName} surface.`,
        ];

  return {
    target: { kind: "area", areaId },
    title,
    badge,
    summary,
    context,
    details,
    notes,
    focusPoints: area === null ? [] : area.polygon,
  };
}

function describeRoadImportance(road: {
  blocked: boolean;
  directionality: string;
  laneCount: number;
  roadClass: string;
}): string {
  if (road.blocked) {
    return "Blocked roadway matters because it can redirect live traffic.";
  }
  if (road.directionality === "two_way") {
    return "Bidirectional roadway matters because it carries live traffic both ways.";
  }
  if (road.laneCount > 1) {
    return "Multi-lane roadway matters because it carries more operational flow.";
  }
  return `This ${humanize(road.roadClass)} is part of the live routing surface.`;
}

function describeRoadContext(bundle: LiveBundleViewModel, road: { blocked: boolean }): string {
  const blockedCount = bundle.map.blockedEdgeIds.length;
  if (road.blocked) {
    return `Current context: blocked, with ${blockedCount} blocked edge(s) in the bundle.`;
  }
  return blockedCount > 0
    ? `Current context: ${blockedCount} blocked edge(s) elsewhere in the bundle.`
    : "Current context: open and available for routing.";
}

function describeIntersectionImportance(intersectionType: string, vertices: number): string {
  const normalized = intersectionType.toLowerCase();
  if (normalized.includes("signal")) {
    return "Signalized junction that controls movement through the scene.";
  }
  if (normalized.includes("yard") || normalized.includes("staging")) {
    return "Operational junction that organizes access through the work site.";
  }
  return vertices > 4
    ? "Control-relevant junction with a larger footprint than a simple crossing."
    : "Control-relevant junction that anchors the road network.";
}

function describeAreaImportance(category: string, kind: string): string {
  const normalizedKind = kind.toLowerCase();
  if (category === "structure") {
    return "Built mass that gives the scene a real-world envelope.";
  }
  if (category === "terrain") {
    return "Terrain form that shapes the worksite and the map’s spatial depth.";
  }
  if (category === "boundary") {
    return "Boundary surface that frames the environment and protects the site edge.";
  }
  if (category === "hazard") {
    return "Restricted surface that stays visible without dominating the scene.";
  }
  if (category === "surface") {
    return "Movement surface that supports pedestrian or shared-site circulation.";
  }
  if (normalizedKind.includes("depot") || normalizedKind.includes("yard") || normalizedKind.includes("loading")) {
    return "Operational area that usually frames staging or loading activity.";
  }
  if (normalizedKind.includes("building") || normalizedKind.includes("office") || normalizedKind.includes("warehouse")) {
    return "Built area that gives the map its world form and local context.";
  }
  return "Context surface that helps anchor the world form around the route network.";
}

function formatIntersectionLabel(intersection: { intersectionType: string; polygon: Point2[]; intersectionId: string }): string {
  return `${humanize(intersection.intersectionType)} junction`;
}

function formatRoadLabel(road: { roadClass: string; directionality: string }): string {
  return `${humanize(road.roadClass)} ${humanize(road.directionality)} road`;
}

function formatAreaLabel(area: { kind: string; label: string | null; areaId: string }): string {
  return area.label ?? `${humanize(area.kind)} ${area.areaId}`;
}

function humanize(value: string): string {
  return value.replace(/[_-]+/gu, " ").replace(/\s+/gu, " ").trim();
}

function summarizeIdList(values: number[], limit: number): string {
  const visibleValues = values.slice(0, limit).join(", ");
  if (values.length <= limit) {
    return visibleValues;
  }
  return `${visibleValues}, …`;
}

function uniqueNumbers(values: number[]): number[] {
  const result: number[] = [];
  const seen = new Set<number>();
  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }
  return result;
}
