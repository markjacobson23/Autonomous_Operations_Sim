import { PanelHeader } from "../shared/PanelHeader";
import { SectionCard } from "../shared/SectionCard";
import {
  describeSelectedTarget,
  findEdgeById,
  findNodePosition,
  formatMeters,
  formatMaybeNumber,
  sampleTrafficSnapshot,
  scaleX,
  scaleY,
  trafficRoadPressureScore,
} from "../../viewModel";
import type { BundlePayload, SelectedTarget } from "../../types";

type TrafficTabProps = {
  bundle: BundlePayload | null;
  motionClockS: number;
  selectedTarget: SelectedTarget | null;
};

export function TrafficTab({ bundle, motionClockS, selectedTarget }: TrafficTabProps): JSX.Element {
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const trafficRoadStatesRanked = [...trafficRoadStates].sort(
    (left, right) =>
      trafficRoadPressureScore(right) - trafficRoadPressureScore(left) ||
      (left.road_id ?? "").localeCompare(right.road_id ?? ""),
  );
  const trafficRoadById = new Map(
    trafficRoadStates
      .filter((state) => state.road_id)
      .map((state) => [state.road_id as string, state]),
  );
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + (roadState.queued_vehicle_ids?.length ?? 0),
    0,
  );
  const congestedRoadCount = trafficRoadStates.filter(
    (roadState) => (roadState.congestion_intensity ?? 0) > 0.2,
  ).length;
  const peakTrafficIntensity = trafficRoadStates.reduce(
    (peak, roadState) => Math.max(peak, roadState.congestion_intensity ?? 0),
    0,
  );
  const blockedEdgeIds = [...(bundle?.snapshot?.blocked_edge_ids ?? [])].sort((left, right) => left - right);
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find((road) => road.road_id === selectedTarget.roadId) ?? null
      : null;
  const selectedRoadTraffic =
    selectedRoad?.road_id !== undefined ? trafficRoadById.get(selectedRoad.road_id) ?? null : null;
  const selectedQueueRecord =
    selectedTarget?.kind === "queue"
      ? (bundle?.traffic_baseline?.queue_records ?? []).find((record) => record.road_id === selectedTarget.roadId) ?? null
      : null;
  const selectedQueueTraffic =
    typeof selectedQueueRecord?.road_id === "string"
      ? trafficRoadById.get(selectedQueueRecord.road_id) ?? null
      : null;
  const trafficQueueRecords = [...(bundle?.traffic_baseline?.queue_records ?? [])].sort((left, right) => {
    const leftRoadState =
      typeof left.road_id === "string" ? trafficRoadById.get(left.road_id) ?? null : null;
    const rightRoadState =
      typeof right.road_id === "string" ? trafficRoadById.get(right.road_id) ?? null : null;
    const leftVehicleCount = left.vehicle_ids?.length ?? (left.vehicle_id !== undefined ? 1 : 0);
    const rightVehicleCount = right.vehicle_ids?.length ?? (right.vehicle_id !== undefined ? 1 : 0);
    return (
      trafficRoadPressureScore(rightRoadState) +
      rightVehicleCount * 10 -
      (trafficRoadPressureScore(leftRoadState) + leftVehicleCount * 10) ||
      (left.road_id ?? "").localeCompare(right.road_id ?? "") ||
      (left.node_id ?? 0) - (right.node_id ?? 0)
    );
  });
  const trafficFocusRoadState = selectedRoadTraffic ?? trafficRoadStatesRanked[0] ?? null;
  const trafficFocusRoad =
    trafficFocusRoadState?.road_id !== undefined
      ? (bundle?.render_geometry?.roads ?? []).find((road) => road.road_id === trafficFocusRoadState.road_id) ?? selectedRoad
      : selectedRoad;
  const trafficMonitoringRoadStates = trafficRoadStatesRanked.slice(0, 5);

  return (
    <section className="panel info-panel traffic-pane" aria-labelledby="traffic-title">
      <PanelHeader
        eyebrow="Traffic Region"
        title="Traffic Control"
        titleId="traffic-title"
        lede="Congestion, blocked edges, queue reservations, and road-state cards are ranked by pressure."
        className="compact traffic-panel-header"
        meta={<span className="status-pill secondary traffic-panel-status">{formatMaybeNumber(blockedEdgeIds.length)} blocked edges</span>}
      />
      <div className="section-stack traffic-monitor-stack">
        <SectionCard
          eyebrow="Urgent traffic issues"
          title="Congestion Overview"
          titleId="traffic-congestion-title"
          lede="Roads with the highest pressure appear first, followed by the rest of the monitored road set."
          className="traffic-monitor-board"
          meta={<span className="traffic-alert-badge">{formatMaybeNumber(congestedRoadCount)} active</span>}
        >
          <div className="traffic-summary-row traffic-summary-row-monitor">
            <span className="traffic-summary-chip critical">{formatMaybeNumber(queuedVehicleCount)} queued</span>
            <span className="traffic-summary-chip">{formatMaybeNumber(congestedRoadCount)} congested roads</span>
            <span className="traffic-summary-chip accent">Peak {Math.round(peakTrafficIntensity * 100)}%</span>
            <span className="traffic-summary-chip critical">{formatMaybeNumber(blockedEdgeIds.length)} blocked edges</span>
          </div>
          <div className="traffic-alert-grid">
            <article className="traffic-alert-card traffic-alert-card-congestion">
              <div className="traffic-alert-card-header">
                <div>
                  <p className="traffic-alert-kicker">Urgent traffic issues</p>
                  <h3>Congestion Overview</h3>
                  <p className="traffic-card-lede">
                    Roads with the highest pressure appear first, followed by the rest of the monitored road set.
                  </p>
                </div>
                <span className="traffic-alert-badge">{formatMaybeNumber(congestedRoadCount)} active</span>
              </div>
              <ul className="traffic-alert-list">
                {trafficMonitoringRoadStates.filter((roadState) => trafficRoadPressureScore(roadState) > 0).length > 0 ? (
                  trafficMonitoringRoadStates
                    .filter((roadState) => trafficRoadPressureScore(roadState) > 0)
                    .slice(0, 3)
                    .map((roadState) => (
                      <li key={`traffic-urgent-${roadState.road_id ?? "road"}`} className="traffic-alert-row">
                        <div className="traffic-alert-row-header">
                          <div>
                            <strong>Road {roadState.road_id ?? "unknown"}</strong>
                            <span>{roadState.congestion_level ?? "active"} · {roadState.control_state ?? "free_flow"}</span>
                          </div>
                          <span className="traffic-alert-row-score">{Math.round((roadState.congestion_intensity ?? 0) * 100)}%</span>
                        </div>
                        <div className="traffic-alert-bar" aria-hidden="true">
                          <span style={{ width: `${Math.round((roadState.congestion_intensity ?? 0) * 100)}%` }} />
                        </div>
                        <div className="traffic-alert-row-meta">
                          <span>Queued {formatMaybeNumber(roadState.queued_vehicle_ids?.length ?? 0)}</span>
                          <span>Occupancy {formatMaybeNumber(roadState.occupancy_count ?? null)}</span>
                          <span>Min spacing {formatMeters(roadState.min_spacing_m ?? null)}</span>
                        </div>
                      </li>
                    ))
                ) : (
                  <li className="traffic-alert-row traffic-alert-row-calm">
                    <div className="traffic-alert-row-header">
                      <div>
                        <strong>All monitored roads</strong>
                        <span>No congestion at the current sample</span>
                      </div>
                      <span className="traffic-alert-row-score">0%</span>
                    </div>
                    <div className="traffic-alert-bar" aria-hidden="true">
                      <span style={{ width: "0%" }} />
                    </div>
                  </li>
                )}
              </ul>
            </article>

            <article className="traffic-alert-card traffic-alert-card-hazard">
              <div className="traffic-alert-card-header">
                <div>
                  <p className="traffic-alert-kicker">Hazard watch</p>
                  <h3>Blocked Edge Watch</h3>
                  <p className="traffic-card-lede">
                    Blocked edges are surfaced before neutral traffic data so closures and hazards stay obvious.
                  </p>
                </div>
                <span className="traffic-alert-badge traffic-alert-badge-critical">{formatMaybeNumber(blockedEdgeIds.length)} blocked</span>
              </div>
              {selectedTarget?.kind === "hazard" && selectedTarget ? (
                <div className="traffic-hazard-focus">
                  <div className="traffic-hazard-focus-header">
                    <strong>Selected blocked edge {selectedTarget.edgeId}</strong>
                    <span>distance pending</span>
                  </div>
                  <div className="traffic-hazard-focus-meta">
                    <span>Start node pending</span>
                    <span>End node pending</span>
                    <span>Speed limit pending</span>
                  </div>
                </div>
              ) : blockedEdgeIds.length > 0 ? (
                <ul className="traffic-hazard-list">
                  {blockedEdgeIds.slice(0, 5).map((edgeId) => (
                    <li key={`blocked-${edgeId}`} className="traffic-hazard-card">
                      <strong>Edge {edgeId}</strong>
                      <span>Blocked edge under active monitoring</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="traffic-hazard-empty">
                  <strong>No blocked edges</strong>
                  <span>Hazard watch is clear at the current sample. Reconnect the live bundle if you expect a newer closure set.</span>
                </div>
              )}
            </article>
          </div>
        </SectionCard>

        <div className="subsection traffic-road-state-pane">
          <div className="traffic-section-heading">
            <div>
              <h3>Active Road Conditions</h3>
              <p className="traffic-section-lede">
                Road-state cards surface congestion intensity, occupancy, queued vehicles, and control state in a scan-friendly order.
              </p>
            </div>
            <span className="traffic-section-badge">{formatMaybeNumber(trafficRoadStatesRanked.length)} roads sampled</span>
          </div>
          {trafficFocusRoadState ? (
            <article
              className={`traffic-road-card traffic-road-card-spotlight ${
                trafficFocusRoadState.road_id && selectedRoadTraffic?.road_id === trafficFocusRoadState.road_id ? "selected" : ""
              }`}
            >
              <div className="traffic-road-card-header">
                <div>
                  <p className="traffic-road-card-kicker">Road focus</p>
                  <h4>Road {trafficFocusRoadState.road_id ?? "unknown"}</h4>
                  <p className="traffic-road-card-summary">
                    {trafficFocusRoad?.road_class ?? "connector"} · {trafficFocusRoad?.directionality ?? "unknown"} · {formatMaybeNumber(trafficFocusRoad?.lane_count ?? null)} lanes · {trafficFocusRoad?.width_m ?? "pending"}m width
                  </p>
                </div>
                <span className="traffic-road-card-pill">{trafficFocusRoadState.congestion_level ?? "free"} · {trafficFocusRoadState.control_state ?? "free_flow"}</span>
              </div>
              <div className="traffic-road-card-metrics">
                <span>Intensity <strong>{Math.round((trafficFocusRoadState.congestion_intensity ?? 0) * 100)}%</strong></span>
                <span>Occupancy <strong>{formatMaybeNumber(trafficFocusRoadState.occupancy_count ?? null)}</strong></span>
                <span>Queued <strong>{formatMaybeNumber(trafficFocusRoadState.queued_vehicle_ids?.length ?? 0)}</strong></span>
                <span>Control <strong>{trafficFocusRoadState.control_state ?? "free_flow"}</strong></span>
                <span>Min spacing <strong>{formatMeters(trafficFocusRoadState.min_spacing_m ?? null)}</strong></span>
              </div>
              <div className="traffic-road-card-bar" aria-hidden="true">
                <span style={{ width: `${Math.round((trafficFocusRoadState.congestion_intensity ?? 0) * 100)}%` }} />
              </div>
              <div className="traffic-road-card-footnote">
                <span>Stop lines {trafficFocusRoadState.stop_line_ids?.join(", ") || "none"}</span>
                <span>Protected zones {trafficFocusRoadState.protected_conflict_zone_ids?.join(", ") || "none"}</span>
              </div>
            </article>
          ) : null}
          <div className="traffic-road-card-grid">
            {trafficMonitoringRoadStates.slice(trafficFocusRoadState ? 1 : 0).map((roadState) => (
              <article
                key={`road-state-${roadState.road_id ?? "road"}`}
                className={`traffic-road-card ${
                  (roadState.congestion_intensity ?? 0) > 0.65
                    ? "traffic-road-card-hot"
                    : (roadState.queued_vehicle_ids?.length ?? 0) > 0
                      ? "traffic-road-card-queued"
                      : "traffic-road-card-calm"
                }`}
              >
                <div className="traffic-road-card-header">
                  <div>
                    <p className="traffic-road-card-kicker">Road {roadState.road_id ?? "unknown"}</p>
                    <h4>{roadState.congestion_level ?? "free"} traffic</h4>
                  </div>
                  <span className="traffic-road-card-pill">{roadState.control_state ?? "free_flow"}</span>
                </div>
                <div className="traffic-road-card-metrics">
                  <span>Intensity <strong>{Math.round((roadState.congestion_intensity ?? 0) * 100)}%</strong></span>
                  <span>Occupancy <strong>{formatMaybeNumber(roadState.occupancy_count ?? null)}</strong></span>
                  <span>Queued <strong>{formatMaybeNumber(roadState.queued_vehicle_ids?.length ?? 0)}</strong></span>
                  <span>Control <strong>{roadState.control_state ?? "free_flow"}</strong></span>
                </div>
                <div className="traffic-road-card-bar" aria-hidden="true">
                  <span style={{ width: `${Math.round((roadState.congestion_intensity ?? 0) * 100)}%` }} />
                </div>
                <div className="traffic-road-card-footnote">
                  <span>Active {formatMaybeNumber(roadState.active_vehicle_ids?.length ?? 0)}</span>
                  <span>Min spacing {formatMeters(roadState.min_spacing_m ?? null)}</span>
                </div>
              </article>
            ))}
            {trafficMonitoringRoadStates.length === 0 ? (
              <div className="traffic-road-empty">
                No road-state samples are available yet. Connect or refresh the live bundle to populate road pressure data.
              </div>
            ) : null}
          </div>
        </div>

        <div className="subsection traffic-reservation-inspection">
          <div className="traffic-section-heading">
            <div>
              <h3>Queue and Reservation Detail</h3>
              <p className="traffic-section-lede">
                Queue records are linked to the road they affect so reservation pressure is easy to follow.
              </p>
            </div>
            <span className="traffic-section-badge">{formatMaybeNumber(trafficQueueRecords.length)} reservations</span>
          </div>
          {selectedQueueRecord ? (
            <article className="traffic-reservation-card traffic-reservation-card-spotlight">
              <div className="traffic-reservation-card-header">
                <div>
                  <p className="traffic-reservation-card-kicker">Selected queue</p>
                  <h4>Road {selectedQueueRecord.road_id ?? "unknown"}</h4>
                  <p className="traffic-reservation-card-summary">
                    Node {formatMaybeNumber(selectedQueueRecord.node_id ?? null)} · {selectedQueueRecord.reason ?? "queued"}
                  </p>
                </div>
                <span className="traffic-reservation-badge">{selectedQueueRecord.vehicle_ids?.length ?? (selectedQueueRecord.vehicle_id !== undefined ? 1 : 0)} vehicle(s)</span>
              </div>
              <div className="traffic-reservation-meta">
                <span>Control {selectedQueueTraffic?.control_state ?? "yield"}</span>
                <span>Congestion {selectedQueueTraffic?.congestion_level ?? "free"}</span>
                <span>Queued {selectedQueueTraffic?.queued_vehicle_ids?.length ?? 0}</span>
                <span>Occupancy {formatMaybeNumber(selectedQueueTraffic?.occupancy_count ?? null)}</span>
              </div>
            </article>
          ) : null}
          <div className="traffic-reservation-grid">
            {trafficQueueRecords.length > 0 ? (
              trafficQueueRecords
                .filter((record) => record !== selectedQueueRecord)
                .slice(0, 4)
                .map((record, index) => {
                  const roadTraffic =
                    typeof record.road_id === "string"
                      ? trafficRoadById.get(record.road_id) ?? null
                      : null;
                  const queuedVehicleCount =
                    record.vehicle_ids?.length ?? (record.vehicle_id !== undefined ? 1 : 0);
                  return (
                    <article key={`${record.road_id ?? "queue"}-${index}`} className="traffic-reservation-card">
                      <div className="traffic-reservation-card-header">
                        <div>
                          <p className="traffic-reservation-card-kicker">Road {record.road_id ?? "unknown"}</p>
                          <h4>{record.reason ?? "Queued reservation"}</h4>
                        </div>
                        <span className="traffic-reservation-badge">{queuedVehicleCount} vehicle(s)</span>
                      </div>
                      <div className="traffic-reservation-meta">
                        <span>Control {roadTraffic?.control_state ?? "yield"}</span>
                        <span>Congestion {roadTraffic?.congestion_level ?? "free"}</span>
                        <span>Occupancy {formatMaybeNumber(roadTraffic?.occupancy_count ?? null)}</span>
                        <span>Node {formatMaybeNumber(record.node_id ?? null)}</span>
                      </div>
                    </article>
                  );
                })
            ) : (
              <div className="traffic-reservation-empty">
                No queue reservations are active yet. Reservation pressure will appear here when a road is blocked, yielded, or back-pressured.
              </div>
            )}
          </div>
          <div className="traffic-context-strip">
            <span>Selected route conflicts {selectedTarget?.kind === "hazard" ? `blocked edge ${selectedTarget.edgeId}` : "no route conflict noted yet"}</span>
            <span>Route preview roads none</span>
            <span>Blocked edges {blockedEdgeIds.length > 0 ? blockedEdgeIds.join(", ") : "none"}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
