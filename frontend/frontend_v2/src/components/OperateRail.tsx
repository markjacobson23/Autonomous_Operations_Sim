import { useEffect, useMemo, useState } from "react";

import type { JsonRecord, LiveBundleViewModel, LiveRoutePreviewViewModel } from "../adapters/liveBundle";
import { buildSelectionPresentation, resolveSelectionVehicleIds } from "../adapters/selectionModel";
import type { FrontendUiState } from "../state/frontendUiState";

type OperateRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  refreshBundle: () => void;
  activeRoutePreview: LiveRoutePreviewViewModel | null;
  setActiveRoutePreview: (preview: LiveRoutePreviewViewModel | null) => void;
};

type CommandFeedbackTone = "idle" | "pending" | "success" | "error";

type CommandFeedback = {
  tone: CommandFeedbackTone;
  title: string;
  message: string;
  detail: string | null;
};

type RoutePlanEntry = {
  id: string;
  vehicleIds: number[];
  vehicleSummary: string;
  targetSummary: string;
  destinationNodeId: number;
  preview: LiveRoutePreviewViewModel | null;
  committed: boolean;
  note: string | null;
};

const initialCommandFeedback: CommandFeedback = {
  tone: "idle",
  title: "Command center ready",
  message: "Use the typed command groups below. Selection stays map-driven and previewable.",
  detail: null,
};

export function OperateRail({
  bundle,
  uiState,
  refreshBundle,
  activeRoutePreview,
  setActiveRoutePreview,
}: OperateRailProps): JSX.Element {
  const [destinationNodeId, setDestinationNodeId] = useState("");
  const [repositionNodeId, setRepositionNodeId] = useState("");
  const [roadEdgeId, setRoadEdgeId] = useState("");
  const [routePlans, setRoutePlans] = useState<RoutePlanEntry[]>([]);
  const [activeRoutePlanId, setActiveRoutePlanId] = useState<string | null>(null);
  const initialStepSeconds = Number.parseFloat(bundle.sessionIdentity.stepSeconds);
  const [sessionStepSeconds, setSessionStepSeconds] = useState(
    Number.isFinite(initialStepSeconds) ? String(initialStepSeconds) : "",
  );
  const [commandFeedback, setCommandFeedback] = useState<CommandFeedback>(initialCommandFeedback);

  const selectionPresentation = buildSelectionPresentation(bundle, uiState);
  const selectedVehicleIds = useMemo(() => resolveSelectionVehicleIds(bundle, uiState), [bundle, uiState]);
  const selectedVehicleLead = selectedVehicleIds[0] ?? null;
  const selectedTarget = uiState.selection.target;
  const selectedVehicles = useMemo(() => {
    return selectedVehicleIds.flatMap((vehicleId) => {
      const inspection = bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === vehicleId) ?? null;
      const liveVehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId) ?? null;
      if (inspection === null && liveVehicle === null) {
        return [];
      }

      return [
        {
          vehicleId,
          state: inspection?.operationalState ?? liveVehicle?.state ?? "unknown",
          waitReason: inspection?.waitReason ?? null,
          summary:
            inspection !== null && inspection.currentTaskType !== null
              ? inspection.currentTaskType
              : inspection?.trafficControlDetail ?? liveVehicle?.state ?? "unknown",
        },
      ];
    });
  }, [bundle.commandCenter.vehicleInspections, bundle.map.vehicles, selectedVehicleIds]);

  const selectedRoad =
    selectedTarget?.kind === "road"
      ? bundle.map.roads.find((entry) => entry.roadId === selectedTarget.roadId) ?? null
      : null;
  const selectedVehicleCount = selectedVehicleIds.length;
  const selectedRoadEdgeIds = selectedRoad?.edgeIds ?? [];
  const selectedRoadPrimaryEdgeId = selectedRoadEdgeIds[0] ?? null;
  const selectedVehicleInspection =
    selectedVehicleLead !== null
      ? bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === selectedVehicleLead) ?? null
      : null;
  const selectedPlan =
    routePlans.find((entry) => entry.id === activeRoutePlanId) ?? routePlans[0] ?? null;

  useEffect(() => {
    if (activeRoutePlanId === null && routePlans.length > 0) {
      setActiveRoutePlanId(routePlans[0].id);
    }
  }, [activeRoutePlanId, routePlans]);

  useEffect(() => {
    if (selectedPlan !== null) {
      setActiveRoutePreview(selectedPlan.preview);
    }
  }, [selectedPlan, setActiveRoutePreview]);

  const hasVehicleSelection = selectedVehicleCount > 0;
  const canPreviewRoutes = bundle.commandSurface.previewEndpoint !== "unknown" && hasVehicleSelection;
  const canIssueCommands = bundle.commandSurface.commandEndpoint !== "unknown";
  const canControlSession = bundle.commandSurface.sessionControlEndpoint !== "unknown";

  const queueCount = selectedVehicles.filter((vehicle) => vehicle.waitReason !== null).length;
  const blockedEdges = bundle.map.blockedEdgeIds.length;
  const hazardSignals = bundle.alerts.filter((alert) => alert.toLowerCase().includes("anomaly"));
  const congestionSignals = bundle.alerts.filter((alert) => alert.toLowerCase().includes("congested"));
  const selectedVehicleSummary = summarizeVehicleIds(selectedVehicleIds);
  const selectedRoadSummary =
    selectedRoad === null
      ? "Select a road on the map to prime the road control entry point."
      : selectedRoad.edgeIds.length > 0
        ? `Selected road ${selectedRoad.roadId} exposes ${selectedRoad.edgeIds.length} edge(s).`
        : `Selected road ${selectedRoad.roadId} has no edge entry points in the bundle.`;
  const routeDestinationPlaceholder =
    selectedVehicleLead !== null
      ? bundle.commandCenter.routePreviews.find((preview) => preview.vehicleId === selectedVehicleLead)?.destinationNodeId?.toString() ??
        "Enter node id"
      : "Enter node id";
  const repositionPlaceholder =
    selectedVehicleInspection?.currentNodeId != null
      ? String(selectedVehicleInspection.currentNodeId)
      : "Enter node id";
  const roadEdgePlaceholder =
    selectedRoadPrimaryEdgeId !== null ? String(selectedRoadPrimaryEdgeId) : "Enter edge id";

  async function handlePreviewRoute(): Promise<void> {
    if (!canPreviewRoutes) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Route preview unavailable",
          "Select one or more vehicles on the map before previewing a route.",
          null,
        ),
      );
      return;
    }

    const destinationNode = parseTypedInteger(destinationNodeId);
    if (destinationNode === null) {
      setCommandFeedback(
        createCommandFeedback("error", "Route preview blocked", "Enter a valid destination node.", null),
      );
      return;
    }

    const vehicleIds = selectedVehicleIds;
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        "Previewing route",
        "Requesting a route preview from the Python session.",
        `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.previewEndpoint, {
      selected_vehicle_ids: vehicleIds,
      vehicle_ids: vehicleIds,
      destination_node_id: destinationNode,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Route preview failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
        ),
      );
      return;
    }

    refreshBundle();
    const previewCount = countPreviewResults(response.payload, vehicleIds.length);
    const preview = extractRoutePreview(response.payload, vehicleIds[0] ?? null, destinationNode);
    if (preview !== null) {
      setActiveRoutePreview(preview);
    }
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Route preview loaded",
        previewCount === 1 ? "One authoritative preview returned from the Python session." : `${previewCount} authoritative previews returned from the Python session.`,
        describeRoutePreviewResponse(response.payload) ??
          `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
      ),
    );
  }

  async function handleAssignDestination(): Promise<void> {
    if (!canIssueCommands) {
      setCommandFeedback(
        createCommandFeedback("error", "Destination command unavailable", "The command endpoint is not bound.", null),
      );
      return;
    }
    if (!hasVehicleSelection) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Destination command blocked",
          "Select one or more vehicles on the map before assigning a destination.",
          null,
        ),
      );
      return;
    }

    const destinationNode = parseTypedInteger(destinationNodeId);
    if (destinationNode === null) {
      setCommandFeedback(
        createCommandFeedback("error", "Destination command blocked", "Enter a valid destination node.", null),
      );
      return;
    }

    const vehicleIds = selectedVehicleIds;
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        "Assigning destination",
        "Sending a typed destination assignment to the Python session.",
        `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.commandEndpoint, {
      command_type: "assign_vehicle_destination",
      selected_vehicle_ids: vehicleIds,
      vehicle_ids: vehicleIds,
      destination_node_id: destinationNode,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Destination command failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
        ),
      );
      return;
    }

    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Destination command accepted",
        "The simulator accepted the destination assignment and the live bundle will refresh.",
        describeCommandResult(response.payload) ??
          `Vehicles: ${selectedVehicleSummary} · Destination node: ${destinationNode}`,
      ),
    );
  }

  async function handleRepositionVehicle(): Promise<void> {
    if (!canIssueCommands) {
      setCommandFeedback(
        createCommandFeedback("error", "Reposition unavailable", "The command endpoint is not bound.", null),
      );
      return;
    }
    if (!hasVehicleSelection) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Reposition blocked",
          "Select one or more vehicles on the map before repositioning.",
          null,
        ),
      );
      return;
    }

    const nodeId = parseTypedInteger(repositionNodeId);
    if (nodeId === null) {
      setCommandFeedback(
        createCommandFeedback("error", "Reposition blocked", "Enter a valid reposition node.", null),
      );
      return;
    }

    const vehicleIds = selectedVehicleIds;
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        "Repositioning vehicles",
        "Sending a typed reposition command to the Python session.",
        `Vehicles: ${selectedVehicleSummary} · Node: ${nodeId}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.commandEndpoint, {
      command_type: "reposition_vehicle",
      selected_vehicle_ids: vehicleIds,
      vehicle_ids: vehicleIds,
      node_id: nodeId,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Reposition failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Vehicles: ${selectedVehicleSummary} · Node: ${nodeId}`,
        ),
      );
      return;
    }

    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Reposition accepted",
        "The simulator accepted the reposition command and the live bundle will refresh.",
        describeCommandResult(response.payload) ?? `Vehicles: ${selectedVehicleSummary} · Node: ${nodeId}`,
      ),
    );
  }

  async function handleRoadCommand(commandType: "block_edge" | "unblock_edge"): Promise<void> {
    if (!canIssueCommands) {
      setCommandFeedback(
        createCommandFeedback("error", "Road control unavailable", "The command endpoint is not bound.", null),
      );
      return;
    }

    const edgeId = parseTypedInteger(roadEdgeId) ?? selectedRoadPrimaryEdgeId;
    if (edgeId === null) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          commandType === "block_edge" ? "Block road blocked" : "Unblock road blocked",
          "Select a road or enter a valid edge id first.",
          null,
        ),
      );
      return;
    }

    setCommandFeedback(
      createCommandFeedback(
        "pending",
        commandType === "block_edge" ? "Blocking road" : "Unblocking road",
        "Sending a typed road-control command to the Python session.",
        `Edge: ${edgeId}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.commandEndpoint, {
      command_type: commandType,
      edge_id: edgeId,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          commandType === "block_edge" ? "Block road failed" : "Unblock road failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Edge: ${edgeId}`,
        ),
      );
      return;
    }

    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        commandType === "block_edge" ? "Road blocked" : "Road unblocked",
        "The simulator accepted the road control command and the live bundle will refresh.",
        describeCommandResult(response.payload) ?? `Edge: ${edgeId}`,
      ),
    );
  }

  async function handleSessionAction(action: "play" | "pause" | "step"): Promise<void> {
    if (!canControlSession) {
      setCommandFeedback(
        createCommandFeedback("error", "Session control unavailable", "The session-control endpoint is not bound.", null),
      );
      return;
    }

    const stepSeconds = parseTypedFloat(sessionStepSeconds) ?? (Number.isFinite(initialStepSeconds) ? initialStepSeconds : 0.5);
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        action === "step" ? "Stepping session" : action === "play" ? "Starting session" : "Pausing session",
        "Sending a session-control command to the Python session.",
        action === "step" ? `Step size: ${stepSeconds.toFixed(2)}s` : null,
      ),
    );

    const payload: JsonRecord = { action };
    if (action === "step") {
      payload.delta_s = stepSeconds;
    }

    const response = await submitJson(bundle.commandSurface.sessionControlEndpoint, payload);
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          action === "step" ? "Step failed" : action === "play" ? "Play failed" : "Pause failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          action === "step" ? `Step size: ${stepSeconds.toFixed(2)}s` : null,
        ),
      );
      return;
    }

    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        action === "step" ? "Session stepped" : action === "play" ? "Session playing" : "Session paused",
        action === "step"
          ? `Advanced the live session by ${stepSeconds.toFixed(2)}s.`
          : action === "play"
            ? "The simulator accepted play mode."
            : "The simulator accepted pause mode.",
        describeSessionControlResult(response.payload) ?? `Mode: ${bundle.sessionIdentity.playState}`,
      ),
    );
  }

  function handleCreateRoutePlan(): void {
    if (!hasVehicleSelection) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Plan creation blocked",
          "Select one or more vehicles on the map before creating a plan entry.",
          null,
        ),
      );
      return;
    }
    const destinationNode = parseTypedInteger(destinationNodeId);
    if (destinationNode === null) {
      setCommandFeedback(
        createCommandFeedback("error", "Plan creation blocked", "Enter a valid destination node first.", null),
      );
      return;
    }
    if (selectionPresentation === null) {
      setCommandFeedback(
        createCommandFeedback("error", "Plan creation blocked", "Select a map target before creating a plan entry.", null),
      );
      return;
    }

    const nextPlanId = createRoutePlanId(routePlans.length);
    const nextPlan: RoutePlanEntry = {
      id: nextPlanId,
      vehicleIds: selectedVehicleIds,
      vehicleSummary: selectedVehicleSummary,
      targetSummary: selectionPresentation.title,
      destinationNodeId: destinationNode,
      preview: null,
      committed: false,
      note: selectionPresentation.summary,
    };
    setRoutePlans((current) => [nextPlan, ...current]);
    setActiveRoutePlanId(nextPlanId);
    setActiveRoutePreview(null);
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Plan entry created",
        "The plan is staged locally. Preview it to paint the route on the map.",
        `Target: ${nextPlan.targetSummary} · Destination node: ${nextPlan.destinationNodeId}`,
      ),
    );
  }

  async function handlePreviewRoutePlan(planId: string): Promise<void> {
    const plan = routePlans.find((entry) => entry.id === planId) ?? null;
    if (plan === null) {
      return;
    }

    setActiveRoutePlanId(planId);
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        "Previewing plan",
        "Requesting an authoritative route preview for the selected plan.",
        `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.previewEndpoint, {
      selected_vehicle_ids: plan.vehicleIds,
      vehicle_ids: plan.vehicleIds,
      destination_node_id: plan.destinationNodeId,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Plan preview failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
        ),
      );
      return;
    }

    const preview = extractRoutePreview(response.payload, plan.vehicleIds[0] ?? null, plan.destinationNodeId);
    if (preview === null) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Plan preview incomplete",
          "The backend returned a response without a route preview.",
          `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
        ),
      );
      return;
    }

    setRoutePlans((current) =>
      current.map((entry) =>
        entry.id === planId
          ? {
              ...entry,
              preview,
              committed: false,
              note: buildPlanPreviewNote(preview, plan),
            }
          : entry,
      ),
    );
    setActiveRoutePreview(preview);
    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Plan preview loaded",
        buildPlanPreviewSummary(preview),
        buildPlanPreviewDetail({ ...plan, preview }),
      ),
    );
  }

  async function handleCommitRoutePlan(planId: string): Promise<void> {
    const plan = routePlans.find((entry) => entry.id === planId) ?? null;
    if (plan === null) {
      return;
    }
    if (plan.preview === null) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Plan commit blocked",
          "Preview the plan first so the command stays understandable and map-linked.",
          `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
        ),
      );
      return;
    }

    setActiveRoutePlanId(planId);
    setCommandFeedback(
      createCommandFeedback(
        "pending",
        "Committing plan",
        "Sending the selected plan back to the Python simulator.",
        `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
      ),
    );

    const response = await submitJson(bundle.commandSurface.commandEndpoint, {
      command_type: "assign_vehicle_destination",
      selected_vehicle_ids: plan.vehicleIds,
      vehicle_ids: plan.vehicleIds,
      destination_node_id: plan.destinationNodeId,
    });
    if (!response.ok) {
      setCommandFeedback(
        createCommandFeedback(
          "error",
          "Plan commit failed",
          extractResponseMessage(response.payload) ?? `Request failed with HTTP ${response.status}.`,
          `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
        ),
      );
      return;
    }

    setRoutePlans((current) =>
      current.map((entry) => (entry.id === planId ? { ...entry, committed: true } : entry)),
    );
    setActiveRoutePreview(plan.preview);
    refreshBundle();
    setCommandFeedback(
      createCommandFeedback(
        "success",
        "Plan committed",
        "The simulator accepted the plan entry and the live bundle will refresh.",
        describeCommandResult(response.payload) ??
          `Target: ${plan.targetSummary} · Destination node: ${plan.destinationNodeId}`,
      ),
    );
  }

  function handleActivateRoutePlan(planId: string): void {
    setActiveRoutePlanId(planId);
    const plan = routePlans.find((entry) => entry.id === planId) ?? null;
    setActiveRoutePreview(plan?.preview ?? null);
  }

  function buildRawRoutePreviewSummary(preview: LiveRoutePreviewViewModel | null): string {
    if (preview === null) {
      return "Preview pending.";
    }

    const path = preview.nodeIds.length > 0 ? preview.nodeIds.join(" -> ") : "path unavailable";
    const distance =
      preview.totalDistance !== null && preview.totalDistance !== undefined
        ? ` · ${preview.totalDistance.toFixed(1)}m`
        : "";
    return `${preview.isActionable ? "Actionable" : "Blocked"} · node ${preview.destinationNodeId}${distance} · ${path}`;
  }

  function buildPlanPreviewSummary(preview: LiveRoutePreviewViewModel | null): string {
    if (preview === null) {
      return "Preview pending. Click preview to render the route on the map.";
    }

    const path = preview.nodeIds.length > 0 ? preview.nodeIds.join(" -> ") : "no path returned";
    const distance =
      preview.totalDistance !== null && preview.totalDistance !== undefined
        ? ` · ${preview.totalDistance.toFixed(1)}m`
        : "";
    const actionability = preview.isActionable ? "Actionable" : "Blocked";
    return `${actionability}${distance} · ${path}`;
  }

  function buildPlanPreviewDetail(plan: RoutePlanEntry): string {
    if (plan.preview === null) {
      return plan.note ?? "Preview requested from the Python session.";
    }

    const reason = plan.preview.reason !== null ? ` · ${humanizePreviewReason(plan.preview.reason)}` : "";
    const congestion =
      bundle.alerts.find((alert) => alert.toLowerCase().includes("congested")) ?? null;
    const congestionDetail = congestion !== null ? ` · ${congestion}` : "";
    return `${plan.preview.isActionable ? "Preview ready" : "Preview blocked"}${reason}${congestionDetail}`;
  }

  function buildPlanPreviewNote(
    preview: LiveRoutePreviewViewModel,
    plan: RoutePlanEntry,
  ): string {
    const path = preview.nodeIds.length > 0 ? preview.nodeIds.join(" -> ") : "path unavailable";
    return `${plan.targetSummary} · ${preview.isActionable ? "actionable" : "blocked"} · ${path}`;
  }

  function describePlanPreviewSummary(preview: LiveRoutePreviewViewModel | null): string {
    if (preview === null) {
      return "Preview pending";
    }

    const path = preview.nodeIds.length > 0 ? preview.nodeIds.join(" -> ") : "route path unavailable";
    const distance =
      preview.totalDistance !== null && preview.totalDistance !== undefined
        ? ` · ${preview.totalDistance.toFixed(1)}m`
        : "";
    return `${preview.isActionable ? "Actionable" : "Blocked"} · ${path}${distance}`;
  }

  function describePlanPreviewDetail(plan: RoutePlanEntry): string {
    if (plan.preview === null) {
      return plan.note ?? "Preview not requested yet.";
    }

    const reason = plan.preview.reason !== null ? ` · ${humanizePreviewReason(plan.preview.reason)}` : "";
    const conflict = bundle.map.blockedEdgeIds.length > 0 ? ` · ${bundle.map.blockedEdgeIds.length} blocked edge(s)` : "";
    return `${plan.preview.isActionable ? "Route available" : "Route blocked"}${reason}${conflict}`;
  }

function extractRoutePreview(
  payload: JsonRecord | null,
  vehicleId: number | null,
  destinationNodeId: number,
): LiveRoutePreviewViewModel | null {
    if (payload === null) {
      return null;
    }

    const routePreviews = payload.route_previews;
    if (!Array.isArray(routePreviews) || routePreviews.length === 0) {
      return null;
    }

  const previewRecord =
      vehicleId !== null
        ? routePreviews.find(
            (entry) => isRecord(entry) && entry.vehicle_id === vehicleId && entry.destination_node_id === destinationNodeId,
          )
        : routePreviews[0];
  if (!isRecord(previewRecord)) {
    return null;
  }

  const nodeIds = Array.isArray(previewRecord.node_ids)
    ? previewRecord.node_ids.flatMap((value) => (typeof value === "number" ? [value] : []))
    : [];
  const edgeIds = Array.isArray(previewRecord.edge_ids)
    ? previewRecord.edge_ids.flatMap((value) => (typeof value === "number" ? [value] : []))
    : [];
  const reason = typeof previewRecord.reason === "string" ? previewRecord.reason : null;
  const reasonCode = typeof previewRecord.reason_code === "string" ? previewRecord.reason_code : null;
  const totalDistance =
    typeof previewRecord.total_distance === "number" && Number.isFinite(previewRecord.total_distance)
      ? previewRecord.total_distance
      : null;

  return {
    vehicleId: typeof previewRecord.vehicle_id === "number" ? previewRecord.vehicle_id : vehicleId ?? -1,
    destinationNodeId:
      typeof previewRecord.destination_node_id === "number" ? previewRecord.destination_node_id : destinationNodeId,
    isActionable: Boolean(previewRecord.is_actionable),
    reason,
    reasonCode,
    nodeIds,
    edgeIds,
    totalDistance,
  };
}

function createRoutePlanId(planIndex: number): string {
  const timestamp = Date.now().toString(36);
  return `plan-${timestamp}-${planIndex + 1}`;
}

function humanizePreviewReason(reason: string): string {
  const trimmed = reason.trim();
  if (trimmed.length === 0) {
    return "No additional detail";
  }

  return trimmed
    .replace(/[_-]+/gu, " ")
    .replace(/\s+/gu, " ")
    .replace(/(^|\s)([a-z])/gu, (match) => match.toUpperCase());
}

  return (
    <>
    <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Planning</p>
            <h2>Compact plan stack</h2>
          </div>
          <div className="panel-metrics">
            <span>{routePlans.length} plans</span>
            <span>{activeRoutePlanId !== null ? "Plan active" : "No active plan"}</span>
            <span>{activeRoutePreview !== null ? "Preview on map" : "Preview hidden"}</span>
          </div>
        </div>
        <p className="stack-copy">
          Create a plan from the current vehicle selection and map target, preview it to paint the route, then commit it from the stack. The typed destination stays as the bridge, not the whole workflow.
        </p>

        <div className="command-center-context">
          <span className="command-context-chip">
            Vehicle: {hasVehicleSelection ? selectedVehicleSummary : "select a vehicle"}
          </span>
          <span className="command-context-chip">Target: {selectionPresentation?.title ?? "select a map target"}</span>
          <span className="command-context-chip">
            Destination bridge: {destinationNodeId.trim().length > 0 ? `node ${destinationNodeId}` : "enter in command center"}
          </span>
        </div>

        <div className="route-plan-builder">
          <div className="route-plan-builder-copy">
            <strong>Build a plan from the current selection.</strong>
            <p>Preview and commit actions stay attached to the selected plan entry so the map can stay primary.</p>
          </div>
          <button
            type="button"
            className="scene-button-primary"
            onClick={handleCreateRoutePlan}
            disabled={!hasVehicleSelection || selectionPresentation === null || destinationNodeId.trim().length === 0}
          >
            Create plan entry
          </button>
        </div>

        {routePlans.length > 0 ? (
          <div className="route-plan-list">
            {routePlans.map((plan, index) => {
              const isActive = plan.id === activeRoutePlanId;
              const previewSummary = describePlanPreviewSummary(plan.preview);
              const previewDetail = describePlanPreviewDetail(plan);
              return (
                <article
                  key={plan.id}
                  className={`route-plan-card ${isActive ? "selected" : ""} ${plan.committed ? "committed" : ""}`}
                >
                  <button
                    type="button"
                    className="route-plan-card-main"
                    onClick={() => handleActivateRoutePlan(plan.id)}
                    aria-pressed={isActive}
                  >
                    <div className="route-plan-card-head">
                      <span className="operate-card-label">Plan {index + 1}</span>
                      <span className="selection-popup-badge">
                        {plan.committed ? "Committed" : plan.preview !== null ? "Previewed" : "Draft"}
                      </span>
                    </div>
                    <strong>
                      {plan.vehicleSummary} → {plan.targetSummary}
                    </strong>
                    <p>{previewSummary}</p>
                    <p className="route-plan-card-detail">{previewDetail}</p>
                  </button>
                  <div className="route-plan-card-actions">
                    <span className="selection-pill">
                      Destination node {plan.destinationNodeId}
                      {plan.preview?.totalDistance !== null && plan.preview?.totalDistance !== undefined
                        ? ` · ${plan.preview.totalDistance.toFixed(1)}m`
                        : ""}
                    </span>
                    <button
                      type="button"
                      className="scene-button"
                      onClick={() => void handlePreviewRoutePlan(plan.id)}
                      disabled={bundle.commandSurface.previewEndpoint === "unknown"}
                    >
                      Preview route
                    </button>
                    <button
                      type="button"
                      className="scene-button-primary"
                      onClick={() => void handleCommitRoutePlan(plan.id)}
                      disabled={plan.preview === null || plan.committed || !canIssueCommands}
                    >
                      Commit plan
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="operate-empty-plan-list">
            <strong>No plans yet.</strong>
            <p>
              Select a vehicle and a map target, type a destination node in the command center, and create the first plan entry here.
            </p>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Command center</p>
            <h2>Typed operator commands</h2>
          </div>
          <span className={`status-badge command-feedback-pill command-feedback-pill-${commandFeedback.tone}`}>
            {commandFeedback.title}
          </span>
        </div>
        <p className="stack-copy">
          Route preview, destination assignment, repositioning, road control, and session playback stay grouped by typed command. The map selection still drives the workflow.
        </p>

        <div className="command-center-context">
          <span className="command-context-chip">
            Selection: {selectedVehicleCount > 0 ? selectedVehicleSummary : selectionPresentation?.title ?? "none"}
          </span>
          <span className="command-context-chip">
            Road: {selectedRoad === null ? "none" : selectedRoad.edgeIds.length > 0 ? `${selectedRoad.roadId} · ${selectedRoad.edgeIds.length} edge(s)` : selectedRoad.roadId}
          </span>
          <span className="command-context-chip">Session: {bundle.sessionIdentity.playState}</span>
          <span className="command-context-chip">Step: {bundle.sessionIdentity.stepSeconds}s</span>
        </div>

        <div className="command-center-grid">
          <article className="command-card command-card-preview">
            <div className="command-card-head">
              <div>
                <p className="panel-kicker">Preview / Commit</p>
                <h3>Destination assignment</h3>
              </div>
              <span className="selection-popup-badge">{hasVehicleSelection ? "Selection-linked" : "Select vehicles"}</span>
            </div>
            <p className="stack-copy">
              Preview a route first, then commit the same typed destination back through the Python simulator.
            </p>
            <label className="operate-field">
              <span>Destination node</span>
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={destinationNodeId}
                onChange={(event) => setDestinationNodeId(event.currentTarget.value)}
                placeholder={routeDestinationPlaceholder}
              />
            </label>
            <div className="command-card-actions">
              <button type="button" className="scene-button-primary" onClick={() => void handlePreviewRoute()} disabled={!canPreviewRoutes}>
                Preview route
              </button>
              <button type="button" className="scene-button-primary" onClick={() => void handleAssignDestination()} disabled={!canIssueCommands || !hasVehicleSelection}>
                Assign destination
              </button>
            </div>
            <p className="command-card-note">
              Preview stays separate from commit. The backend remains authoritative for both route and command truth.
            </p>
          </article>

          <article className="command-card command-card-move">
            <div className="command-card-head">
              <div>
                <p className="panel-kicker">Typed command</p>
                <h3>Reposition vehicles</h3>
              </div>
              <span className="selection-popup-badge">{hasVehicleSelection ? `${selectedVehicleCount} selected` : "Needs vehicles"}</span>
            </div>
            <p className="stack-copy">
              Move the selected vehicle(s) directly to an explicit node without changing the preview workflow.
            </p>
            <label className="operate-field">
              <span>Reposition node</span>
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={repositionNodeId}
                onChange={(event) => setRepositionNodeId(event.currentTarget.value)}
                placeholder={repositionPlaceholder}
              />
            </label>
            <div className="command-card-actions">
              <button type="button" className="scene-button-primary" onClick={() => void handleRepositionVehicle()} disabled={!canIssueCommands || !hasVehicleSelection}>
                Reposition vehicle(s)
              </button>
            </div>
            <p className="command-card-note">
              The typed node stays explicit, but the target list remains map-selected and bundle-derived.
            </p>
          </article>

          <article className="command-card command-card-road">
            <div className="command-card-head">
              <div>
                <p className="panel-kicker">Traffic control</p>
                <h3>Block or unblock road</h3>
              </div>
              <span className="selection-popup-badge">{selectedRoad === null ? "Select a road" : "Road-linked"}</span>
            </div>
            <p className="stack-copy">{selectedRoadSummary}</p>
            <label className="operate-field">
              <span>Road edge id</span>
              <input
                type="number"
                min="0"
                inputMode="numeric"
                value={roadEdgeId}
                onChange={(event) => setRoadEdgeId(event.currentTarget.value)}
                placeholder={roadEdgePlaceholder}
              />
            </label>
            <div className="command-card-actions">
              <button type="button" className="scene-button-primary" onClick={() => void handleRoadCommand("block_edge")} disabled={!canIssueCommands || (roadEdgeId.trim() === "" && selectedRoadPrimaryEdgeId === null)}>
                Block road
              </button>
              <button type="button" className="scene-button-primary" onClick={() => void handleRoadCommand("unblock_edge")} disabled={!canIssueCommands || (roadEdgeId.trim() === "" && selectedRoadPrimaryEdgeId === null)}>
                Unblock road
              </button>
            </div>
            <p className="command-card-note">
              If no edge id is typed, the selected road’s first edge entry point is used.
            </p>
          </article>

          <article className="command-card command-card-session">
            <div className="command-card-head">
              <div>
                <p className="panel-kicker">Session control</p>
                <h3>Play, pause, step</h3>
              </div>
              <span className="selection-popup-badge">{bundle.sessionIdentity.playState}</span>
            </div>
            <p className="stack-copy">Playback stays adjacent to the command center so the operator can keep the map primary.</p>
            <label className="operate-field operate-field-inline">
              <span>Step seconds</span>
              <input
                type="number"
                min="0.1"
                step="0.1"
                inputMode="decimal"
                value={sessionStepSeconds}
                onChange={(event) => setSessionStepSeconds(event.currentTarget.value)}
                placeholder={bundle.sessionIdentity.stepSeconds}
              />
            </label>
            <div className="command-card-actions">
              <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("play")} disabled={!canControlSession}>
                Play
              </button>
              <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("pause")} disabled={!canControlSession}>
                Pause
              </button>
              <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("step")} disabled={!canControlSession}>
                Step
              </button>
              <button type="button" className="scene-button-primary" onClick={refreshBundle}>
                Refresh bundle
              </button>
            </div>
            <p className="command-card-note">
              Session control remains explicit and bundle-backed. Refresh is still available as a manual check.
            </p>
          </article>
        </div>

        <div className={`command-feedback command-feedback-${commandFeedback.tone}`} aria-live="polite">
          <div className="command-feedback-head">
            <p className="panel-kicker">Feedback</p>
            <span className="command-feedback-status">{commandFeedback.tone}</span>
          </div>
          <strong>{commandFeedback.title}</strong>
          <p>{commandFeedback.message}</p>
          {commandFeedback.detail !== null ? <p className="command-feedback-detail">{commandFeedback.detail}</p> : null}
        </div>
      </section>

      <section className="panel">
        <h2>Inspector</h2>
        {selectionPresentation === null ? (
          <p className="stack-copy">
            Click a vehicle, road, or area to inspect it. The command center will stay aligned with the same selection state.
          </p>
        ) : (
          <>
            <div className="selection-inspector-head">
              <div>
                <p className="panel-kicker">Selected</p>
                <h3>{selectionPresentation.title}</h3>
              </div>
              <span className="selection-popup-badge">{selectionPresentation.badge}</span>
            </div>
            <p className="stack-copy">{selectionPresentation.summary}</p>
            <p className="selection-inspector-context">{selectionPresentation.context}</p>
            <dl className="selection-inspector-details">
              {selectionPresentation.details.map((detail) => (
                <div key={detail.label}>
                  <dt>{detail.label}</dt>
                  <dd>{detail.value}</dd>
                </div>
              ))}
            </dl>
            {selectionPresentation.notes.length > 0 ? (
              <ul className="list-copy">
                {selectionPresentation.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
          </>
        )}
      </section>

      <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Live context</p>
            <h2>Operator state</h2>
          </div>
          <span className="status-badge">{bundle.sessionIdentity.playState}</span>
        </div>
        <p className="stack-copy">
          The command center stays grounded in the current bundle, selection, and authoritative session state.
        </p>
        <div className="operate-chip-row">
          {selectedVehicles.length > 0 ? (
            selectedVehicles.map((vehicle) => (
              <span key={vehicle.vehicleId} className="operate-chip">
                Vehicle {vehicle.vehicleId} · {vehicle.state}
              </span>
            ))
          ) : (
            <span className="operate-chip operate-chip-muted">Select vehicles on the map to start typed command workflows.</span>
          )}
        </div>
        <div className="minimap-context-strip">
          {bundle.alerts.length > 0 ? <span>{bundle.alerts[0]}</span> : <span>No active alerts.</span>}
          {congestionSignals.length > 0 ? <span>{congestionSignals[0]}</span> : null}
          {hazardSignals.length > 0 ? <span>{hazardSignals[0]}</span> : null}
          <span>{queueCount > 0 ? `${queueCount} selected vehicle(s) waiting` : "No selected queue pressure."}</span>
          <span>{blockedEdges > 0 ? `${blockedEdges} blocked edge(s)` : "No blocked edges."}</span>
        </div>
      </section>
    </>
  );
}

function createCommandFeedback(
  tone: CommandFeedbackTone,
  title: string,
  message: string,
  detail: string | null,
): CommandFeedback {
  return {
    tone,
    title,
    message,
    detail,
  };
}

async function submitJson(endpoint: string, payload: JsonRecord): Promise<{
  ok: boolean;
  payload: JsonRecord | null;
  status: number;
}> {
  try {
    const response = await fetch(new URL(endpoint, window.location.origin), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    return {
      ok: response.ok,
      payload: await readJsonResponse(response),
      status: response.status,
    };
  } catch {
    return {
      ok: false,
      payload: null,
      status: 0,
    };
  }
}

async function readJsonResponse(response: Response): Promise<JsonRecord | null> {
  try {
    const payload: unknown = await response.json();
    return isRecord(payload) ? payload : null;
  } catch {
    return null;
  }
}

function extractResponseMessage(payload: JsonRecord | null): string | null {
  if (payload === null) {
    return null;
  }

  if (typeof payload.message === "string" && payload.message.trim().length > 0) {
    return payload.message;
  }

  const validationMessages = payload.validation_messages;
  if (Array.isArray(validationMessages)) {
    for (const message of validationMessages) {
      if (isRecord(message) && typeof message.message === "string" && message.message.trim().length > 0) {
        return message.message;
      }
    }
  }

  const commandResultDescription = describeCommandResult(payload);
  if (commandResultDescription !== null) {
    return commandResultDescription;
  }

  return null;
}

function describeCommandResult(payload: JsonRecord | null): string | null {
  if (payload === null) {
    return null;
  }

  const result = payload.command_result;
  if (Array.isArray(result)) {
    const descriptions = result.flatMap((entry) => (isRecord(entry) ? [describeCommandResultRecord(entry)] : [])).filter(
      (entry): entry is string => entry !== null,
    );
    if (descriptions.length > 0) {
      return descriptions.join(" · ");
    }
    return `${result.length} command acknowledgement(s) returned.`;
  }

  if (isRecord(result)) {
    return describeCommandResultRecord(result);
  }

  return null;
}

function describeCommandResultRecord(record: JsonRecord): string | null {
  if (typeof record.message === "string" && record.message.trim().length > 0) {
    return record.message;
  }

  const commandDescription = isRecord(record.command) ? describeCommandPayload(record.command) : null;
  const status = typeof record.status === "string" && record.status.length > 0 ? record.status : null;

  if (commandDescription !== null && status !== null) {
    return `${status} · ${commandDescription}`;
  }
  if (commandDescription !== null) {
    return commandDescription;
  }
  if (status !== null) {
    return status;
  }
  return null;
}

function describeCommandPayload(command: JsonRecord): string | null {
  const commandType = typeof command.command_type === "string" ? command.command_type : null;
  if (commandType === null) {
    return null;
  }

  if (commandType === "assign_vehicle_destination") {
    return `assign_vehicle_destination · vehicle ${formatMaybeNumber(command.vehicle_id)} → node ${formatMaybeNumber(
      command.destination_node_id,
    )}`;
  }
  if (commandType === "reposition_vehicle") {
    return `reposition_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id)} → node ${formatMaybeNumber(command.node_id)}`;
  }
  if (commandType === "block_edge" || commandType === "unblock_edge") {
    return `${commandType} · edge ${formatMaybeNumber(command.edge_id)}`;
  }
  if (commandType === "spawn_vehicle") {
    return `spawn_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id)} at node ${formatMaybeNumber(command.node_id)}`;
  }
  if (commandType === "remove_vehicle") {
    return `remove_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id)}`;
  }
  if (commandType === "inject_job") {
    return `inject_job · vehicle ${formatMaybeNumber(command.vehicle_id)} job ${formatMaybeJobId(command.job)}`;
  }
  if (commandType === "declare_temporary_hazard" || commandType === "clear_temporary_hazard") {
    return `${commandType} · edge ${formatMaybeNumber(command.edge_id)}`;
  }
  return commandType;
}

function describeSessionControlResult(payload: JsonRecord | null): string | null {
  if (payload === null) {
    return null;
  }

  if (isRecord(payload.session_advance)) {
    const sequence = typeof payload.session_advance.sequence === "number" ? payload.session_advance.sequence : null;
    if (sequence !== null) {
      return `Session advance sequence ${sequence}.`;
    }
    return "Session advance acknowledged.";
  }

  return null;
}

function describeRoutePreviewResponse(payload: JsonRecord | null): string | null {
  if (payload === null) {
    return null;
  }

  const routePreviews = payload.route_previews;
  if (!Array.isArray(routePreviews) || routePreviews.length === 0) {
    return null;
  }

  const previewDescriptions = routePreviews.flatMap((entry) => {
    if (!isRecord(entry)) {
      return [];
    }
    const vehicleId = typeof entry.vehicle_id === "number" ? entry.vehicle_id : null;
    const destinationNodeId = typeof entry.destination_node_id === "number" ? entry.destination_node_id : null;
    if (vehicleId === null || destinationNodeId === null) {
      return [];
    }
    return [`vehicle ${vehicleId} → node ${destinationNodeId}`];
  });

  if (previewDescriptions.length === 0) {
    return null;
  }

  return `Preview targets: ${previewDescriptions.join(" · ")}`;
}

function countPreviewResults(payload: JsonRecord | null, fallback: number): number {
  if (payload === null) {
    return fallback;
  }

  const routePreviews = payload.route_previews;
  if (!Array.isArray(routePreviews)) {
    return fallback;
  }

  return routePreviews.length > 0 ? routePreviews.length : fallback;
}

function parseTypedInteger(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return null;
  }

  const parsed = Number(trimmed);
  if (!Number.isInteger(parsed) || parsed < 0) {
    return null;
  }

  return parsed;
}

function parseTypedFloat(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return null;
  }

  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }

  return parsed;
}

function summarizeVehicleIds(values: number[]): string {
  if (values.length === 0) {
    return "none";
  }

  const visibleValues = values.slice(0, 4).map((value) => String(value));
  const suffix = values.length > visibleValues.length ? "…" : "";
  return `${visibleValues.join(", ")}${suffix}`;
}

function formatMaybeNumber(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  return "?";
}

function formatMaybeJobId(value: unknown): string {
  if (isRecord(value) && typeof value.id === "string" && value.id.length > 0) {
    return value.id;
  }
  return "job";
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
