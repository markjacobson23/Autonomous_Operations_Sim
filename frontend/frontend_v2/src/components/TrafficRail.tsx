import type { LiveBundleViewModel, LiveTrafficRoadStateViewModel } from "../adapters/liveBundle";
import { buildSelectionPresentation, resolveActiveSelectionTarget } from "../adapters/selectionModel";
import type { FrontendUiState } from "../state/frontendUiState";

type TrafficRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
};

export function TrafficRail({ bundle, uiState }: TrafficRailProps): JSX.Element {
  const selectedTarget = resolveActiveSelectionTarget(bundle, uiState);
  const selectionPresentation = buildSelectionPresentation(bundle, uiState);
  const trafficRoadStates = [...bundle.traffic.roadStates].sort(
    (left, right) => trafficPressureScore(right) - trafficPressureScore(left) || left.roadId.localeCompare(right.roadId),
  );
  const trafficRoadById = new Map(trafficRoadStates.map((roadState) => [roadState.roadId, roadState]));
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? bundle.map.roads.find((road) => road.roadId === selectedTarget.roadId) ?? null
      : null;
  const selectedRoadState = selectedRoad !== null ? trafficRoadById.get(selectedRoad.roadId) ?? null : null;
  const selectedVehicleInspection =
    selectedTarget?.kind === "vehicle"
      ? bundle.commandCenter.vehicleInspections.find((inspection) => inspection.vehicleId === selectedTarget.vehicleId) ?? null
      : null;
  const queuedVehicleCount = trafficRoadStates.reduce((count, roadState) => count + roadState.queuedVehicleIds.length, 0);
  const congestedRoadCount = trafficRoadStates.filter((roadState) => roadState.congestionIntensity > 0.2).length;
  const blockedRoadCount = bundle.map.roads.filter((road) => road.blocked).length;
  const controlPointCount = bundle.traffic.controlPoints.length;
  const signalReadyCount = bundle.traffic.controlPoints.filter((controlPoint) => controlPoint.signalReady).length;
  const trafficDiagnostics = bundle.utility.renderDiagnostics.filter(
    (entry) => entry.includes("Control point") || entry.includes("Queue record"),
  );
  const queueRecords = [...bundle.traffic.queueRecords].sort(
    (left, right) =>
      (right.queueEndS - right.queueStartS) - (left.queueEndS - left.queueStartS) ||
      left.roadId?.localeCompare(right.roadId ?? "") ||
      left.nodeId - right.nodeId,
  );
  const activeQueueRoads = new Set(queueRecords.flatMap((record) => (record.roadId !== null ? [record.roadId] : [])));

  return (
    <section className="panel traffic-rail">
      <div className="panel-topline">
        <div>
          <p className="panel-kicker">Traffic</p>
          <h2>Traffic mode baseline</h2>
        </div>
        <div className="panel-metrics">
          <span>{congestedRoadCount} congested roads</span>
          <span>{queuedVehicleCount} queued vehicles</span>
          <span>{blockedRoadCount} blocked roads</span>
        </div>
      </div>
      <p className="stack-copy">
        Inspect queues, road pressure, and control points here. The map stays primary, but this mode makes flow issues easier to read.
      </p>

      <div className="traffic-summary-strip">
        <span className="selection-pill">{trafficRoadStates.length > 0 ? `${trafficRoadStates.length} road state sample(s)` : "No road states yet"}</span>
        <span className="selection-pill">{controlPointCount} control point(s)</span>
        <span className="selection-pill">{signalReadyCount} signal-ready</span>
        <span className="selection-pill">{bundle.traffic.queueRecords.length} queue record(s)</span>
      </div>

      {trafficDiagnostics.length > 0 ? (
        <section className="traffic-diagnostics-card">
          <div className="traffic-section-head">
            <div>
              <h3>Geometry diagnostics</h3>
              <p>Node-driven traffic overlays are using the canonical node map, and these are the items that could not resolve.</p>
            </div>
            <span className="selection-popup-badge">{trafficDiagnostics.length} issue(s)</span>
          </div>
          <ul className="list-copy">
            {trafficDiagnostics.slice(0, 3).map((diagnostic) => (
              <li key={diagnostic}>{diagnostic}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="traffic-focus-card">
        <div className="command-card-head">
          <div>
            <p className="panel-kicker">Selected traffic context</p>
            <h3>{selectionPresentation?.title ?? "No selection"}</h3>
          </div>
          <span className="selection-popup-badge">{selectedTarget === null ? "Select a road or vehicle" : selectedTarget.kind}</span>
        </div>
        <p className="stack-copy">
          {selectedRoadState !== null
            ? describeRoadState(selectedRoadState, selectedRoad)
            : selectedVehicleInspection !== null
              ? describeVehicleTraffic(selectedVehicleInspection)
              : selectionPresentation?.summary ?? "Select a traffic target to see queue and control detail."}
        </p>
        <div className="traffic-focus-meta">
          {selectedRoadState !== null ? (
            <>
              <span>Queued {selectedRoadState.queuedVehicleIds.length}</span>
              <span>Occupancy {selectedRoadState.occupancyCount}</span>
              <span>Control {selectedRoadState.controlState}</span>
              <span>Intensity {Math.round(selectedRoadState.congestionIntensity * 100)}%</span>
            </>
          ) : selectedVehicleInspection !== null ? (
            <>
              <span>Node {selectedVehicleInspection.currentNodeId ?? "unknown"}</span>
              <span>Wait {selectedVehicleInspection.waitReason ?? "none"}</span>
              <span>Control {selectedVehicleInspection.trafficControlState ?? "none"}</span>
              <span>ETA {selectedVehicleInspection.etaSeconds !== null ? `${selectedVehicleInspection.etaSeconds.toFixed(1)}s` : "unknown"}</span>
            </>
          ) : (
            <>
              <span>Roads and queues appear below</span>
              <span>Selection-aware detail stays compact</span>
            </>
          )}
        </div>
      </section>

      <section className="traffic-section">
        <div className="traffic-section-head">
          <div>
            <h3>Congestion scan</h3>
            <p>Roads are ranked by pressure, then by road id for a stable scan order.</p>
          </div>
          <span className="selection-popup-badge">{bundle.traffic.sampleTimeS !== null ? `${bundle.traffic.sampleTimeS.toFixed(1)}s sample` : "Live sample"}</span>
        </div>
        {trafficRoadStates.length > 0 ? (
          <div className="traffic-road-list">
            {trafficRoadStates.slice(0, 5).map((roadState) => {
              const road = bundle.map.roads.find((entry) => entry.roadId === roadState.roadId) ?? null;
              const selected = selectedRoadState?.roadId === roadState.roadId;
              return (
                <article
                  key={roadState.roadId}
                  className={`traffic-road-card traffic-road-card-compact ${selected ? "selected" : ""} ${
                    roadState.congestionIntensity > 0.65
                      ? "traffic-road-card-hot"
                      : roadState.queuedVehicleIds.length > 0
                        ? "traffic-road-card-queued"
                        : "traffic-road-card-calm"
                  }`}
                >
                  <div className="traffic-road-card-header">
                    <div>
                      <p className="traffic-road-card-kicker">Road {roadState.roadId}</p>
                      <h4>{roadState.congestionLevel}</h4>
                    </div>
                    <span className="traffic-road-card-pill">{roadState.controlState}</span>
                  </div>
                  <p className="traffic-road-card-summary">
                    {road?.roadClass ?? "road"} · {road?.directionality ?? "unknown"} · {road?.laneCount ?? 0} lane(s)
                  </p>
                  <div className="traffic-road-card-metrics">
                    <span>Intensity <strong>{Math.round(roadState.congestionIntensity * 100)}%</strong></span>
                    <span>Queued <strong>{roadState.queuedVehicleIds.length}</strong></span>
                    <span>Active <strong>{roadState.activeVehicleIds.length}</strong></span>
                    <span>Min spacing <strong>{roadState.minSpacingM !== null ? `${roadState.minSpacingM.toFixed(1)}m` : "n/a"}</strong></span>
                  </div>
                  <div className="traffic-road-card-bar" aria-hidden="true">
                    <span style={{ width: `${Math.round(roadState.congestionIntensity * 100)}%` }} />
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="traffic-empty-state">No live road-state sample is available yet.</div>
        )}
      </section>

      <section className="traffic-section">
        <div className="traffic-section-head">
          <div>
            <h3>Queue watch</h3>
            <p>Queue records show where waiting pressure is landing on the map.</p>
          </div>
          <span className="selection-popup-badge">{bundle.traffic.queueRecords.length} records</span>
        </div>
        {queueRecords.length > 0 ? (
          <div className="traffic-queue-list">
            {queueRecords.slice(0, 5).map((record, index) => {
              const roadState = record.roadId !== null ? trafficRoadById.get(record.roadId) ?? null : null;
              const queueDuration = Math.max(0, record.queueEndS - record.queueStartS);
              return (
                <article key={`${record.roadId ?? "queue"}-${record.nodeId}-${index}`} className="traffic-queue-card">
                  <div className="traffic-queue-card-head">
                    <strong>{record.roadId !== null ? `Road ${record.roadId}` : "Unassigned queue"}</strong>
                    <span>{queueDuration.toFixed(1)}s</span>
                  </div>
                  <p>{record.reason}</p>
                  <div className="traffic-queue-card-meta">
                    <span>Node {record.nodeId}</span>
                    <span>Vehicle {record.vehicleId}</span>
                    <span>{roadState?.controlState ?? "yield"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="traffic-empty-state">No queue records are active yet.</div>
        )}
      </section>

      <section className="traffic-section">
        <div className="traffic-section-head">
          <div>
            <h3>Control points</h3>
            <p>Control points anchor the baseline closure and intersection context.</p>
          </div>
          <span className="selection-popup-badge">{controlPointCount} total</span>
        </div>
        {bundle.traffic.controlPoints.length > 0 ? (
          <div className="traffic-control-list">
            {bundle.traffic.controlPoints.slice(0, 5).map((controlPoint) => (
              <article key={controlPoint.controlId} className="traffic-control-card">
                <div className="traffic-control-card-head">
                  <strong>{controlPoint.controlType}</strong>
                  <span>{controlPoint.signalReady ? "Signal ready" : "Waiting"}</span>
                </div>
                <p>Node {controlPoint.nodeId}</p>
                <div className="traffic-control-card-meta">
                  <span>{controlPoint.controlledRoadIds.length} road(s)</span>
                  <span>{controlPoint.stopLineIds.length} stop line(s)</span>
                  <span>{controlPoint.protectedConflictZoneIds.length} conflict zone(s)</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="traffic-empty-state">No control points are available in the current bundle.</div>
        )}
      </section>

      {activeQueueRoads.size > 0 ? (
        <p className="traffic-footnote">Queue pressure currently touches {activeQueueRoads.size} road(s).</p>
      ) : (
        <p className="traffic-footnote">Queue pressure is currently localized to the selected traffic sample.</p>
      )}
    </section>
  );
}

function trafficPressureScore(roadState: LiveTrafficRoadStateViewModel): number {
  return roadState.congestionIntensity * 100 + roadState.queuedVehicleIds.length * 8 + roadState.occupancyCount;
}

function describeRoadState(
  roadState: LiveTrafficRoadStateViewModel,
  road: LiveBundleViewModel["map"]["roads"][number] | null,
): string {
  const roadSummary =
    road !== null ? `${road.roadClass} · ${road.directionality} · ${road.laneCount} lane(s)` : "Road detail unavailable.";
  const queueSummary = roadState.queuedVehicleIds.length > 0 ? `${roadState.queuedVehicleIds.length} queued` : "No queue pressure";
  const spacingSummary = roadState.minSpacingM !== null ? ` · min spacing ${roadState.minSpacingM.toFixed(1)}m` : "";
  return `${roadSummary} · ${queueSummary}${spacingSummary}`;
}

function describeVehicleTraffic(
  inspection: LiveBundleViewModel["commandCenter"]["vehicleInspections"][number],
): string {
  const wait = inspection.waitReason !== null ? inspection.waitReason : "no wait reason";
  const control = inspection.trafficControlDetail !== null ? inspection.trafficControlDetail : "no control detail";
  const eta = inspection.etaSeconds !== null ? ` · ETA ${inspection.etaSeconds.toFixed(1)}s` : "";
  return `${wait} · ${control}${eta}`;
}
