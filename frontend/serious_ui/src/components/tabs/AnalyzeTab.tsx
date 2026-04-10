import { PanelHeader } from "../shared/PanelHeader";
import {
  describeEdgeTargetLabel,
  describeSelectedBadge,
  describeRecentCommand,
  findDisplayedVehicleById,
  formatMaybeNumber,
  formatMeters,
  formatSeconds,
  normalizeReviewLevel,
  reviewPriorityRank,
  reviewSeverityRank,
  sampleDisplayedVehicles,
} from "../../viewModel";
import type { BundlePayload, SelectedTarget } from "../../types";

type AnalyzeTabProps = {
  bundle: BundlePayload | null;
  motionClockS: number;
  selectedTarget: SelectedTarget | null;
  selectedVehicleIds: number[];
};

export function AnalyzeTab({ bundle, motionClockS, selectedTarget, selectedVehicleIds }: AnalyzeTabProps): JSX.Element {
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const inspections = bundle?.command_center?.vehicle_inspections ?? [];
  const suggestions = bundle?.command_center?.ai_assist?.suggestions ?? [];
  const anomalies = bundle?.command_center?.ai_assist?.anomalies ?? [];
  const explanations = bundle?.command_center?.ai_assist?.explanations ?? [];
  const recentCommands = bundle?.command_center?.recent_commands ?? [];
  const reviewAnomalies = [...anomalies].sort(
    (left, right) =>
      reviewSeverityRank(left.severity) - reviewSeverityRank(right.severity) ||
      (left.summary ?? "").localeCompare(right.summary ?? "") ||
      (left.anomaly_id ?? "").localeCompare(right.anomaly_id ?? ""),
  );
  const reviewSuggestions = [...suggestions].sort(
    (left, right) =>
      reviewPriorityRank(left.priority) - reviewPriorityRank(right.priority) ||
      (left.kind ?? "").localeCompare(right.kind ?? "") ||
      (left.summary ?? "").localeCompare(right.summary ?? "") ||
      (left.suggestion_id ?? "").localeCompare(right.suggestion_id ?? ""),
  );
  const reviewExplanations = [...explanations].sort(
    (left, right) =>
      Number((left.vehicle_id ?? Number.MAX_SAFE_INTEGER) === selectedVehicleIds[0]) -
        Number((right.vehicle_id ?? Number.MAX_SAFE_INTEGER) === selectedVehicleIds[0]) ||
      (left.vehicle_id ?? Number.MAX_SAFE_INTEGER) - (right.vehicle_id ?? Number.MAX_SAFE_INTEGER) ||
      (left.summary ?? "").localeCompare(right.summary ?? ""),
  );
  const reviewRecentCommands = recentCommands.slice(0, 4);
  const selectedVehicleId = selectedVehicleIds[0] ?? null;
  const selectedInspection = selectedVehicleId
    ? inspections.find((inspection) => inspection.vehicle_id === selectedVehicleId) ?? null
    : null;
  const selectedVehicle = findDisplayedVehicleById(displayedVehicles, selectedVehicleId);

  return (
    <section className="panel info-panel analyze-pane" aria-labelledby="inspector-title">
      <PanelHeader
        eyebrow="Analyze Region"
        title="Diagnostics and AI Review"
        titleId="inspector-title"
        lede="Urgent issues first, recommended actions second, and supporting context last."
        className="compact analyze-panel-header"
        meta={
          <div className="analyze-panel-meta">
            <span className="status-pill secondary">{selectedTarget ? describeSelectedBadge(selectedTarget) : `${inspections.length} records`}</span>
            <div className="analyze-summary-strip" aria-label="Analyze summary">
              <span className="analysis-chip analysis-chip-alert">{reviewAnomalies.length} urgent issue{reviewAnomalies.length === 1 ? "" : "s"}</span>
              <span className="analysis-chip analysis-chip-action">{reviewSuggestions.length} action{reviewSuggestions.length === 1 ? "" : "s"}</span>
              <span className="analysis-chip analysis-chip-context">{reviewExplanations.length} explanation{reviewExplanations.length === 1 ? "" : "s"}</span>
            </div>
          </div>
        }
      />

      <div className="analyze-review-stack">
        <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-urgent">
          <div className="analyze-section-header">
            <div>
              <h3>Urgent issues</h3>
              <p>Escalations and anomalies are surfaced first for immediate review.</p>
            </div>
            <span className="analysis-section-chip">
              {reviewAnomalies.length > 0 ? "highest severity first" : "no active anomalies"}
            </span>
          </div>
          <div className="analyze-card-stack">
            {reviewAnomalies.length > 0 ? (
              reviewAnomalies.map((anomaly) => {
                const anomalyVehicle = findDisplayedVehicleById(displayedVehicles, anomaly.vehicle_id ?? null);
                const anomalyTargetLabel =
                  anomaly.vehicle_id !== undefined
                    ? `Vehicle ${formatMaybeNumber(anomaly.vehicle_id)}${
                        anomalyVehicle?.display_name ? ` · ${anomalyVehicle.display_name}` : ""
                      }`
                    : null;
                const severityLabel = normalizeReviewLevel(anomaly.severity, "info");
                return (
                  <article key={anomaly.anomaly_id ?? anomaly.summary ?? "anomaly"} className={`review-card review-card-urgent review-card-${severityLabel}`}>
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>{anomaly.summary ?? "No anomaly summary"}</strong>
                        <span>Anomaly review item</span>
                      </div>
                      <div className="review-card-meta">
                        <span className={`review-level-chip review-level-chip-${severityLabel}`}>{severityLabel.toUpperCase()}</span>
                        {anomalyTargetLabel ? <span className="review-target-chip">{anomalyTargetLabel}</span> : null}
                      </div>
                    </div>
                    <div className="review-card-body">
                      {anomaly.vehicle_id !== undefined
                        ? "This anomaly is tied to a specific vehicle and should be reviewed before the next action."
                        : "This anomaly is not tied to a vehicle target."}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="review-empty-state">No anomalies are available yet. The review feed is clear and waiting for the next escalation.</div>
            )}
          </div>
        </section>

        <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-actions">
          <div className="analyze-section-header">
            <div>
              <h3>Suggestions</h3>
              <p>Recommended actions are ordered by priority and linked to their target when possible.</p>
            </div>
            <span className="analysis-section-chip">{reviewSuggestions.length > 0 ? "actionable review" : "no recommendations"}</span>
          </div>
          <div className="analyze-card-stack">
            {reviewSuggestions.length > 0 ? (
              reviewSuggestions.map((suggestion) => {
                const suggestionVehicle = findDisplayedVehicleById(displayedVehicles, suggestion.target_vehicle_id ?? null);
                const suggestionTargetLabel =
                  suggestion.target_vehicle_id !== undefined && suggestion.target_vehicle_id !== null
                    ? `Vehicle ${formatMaybeNumber(suggestion.target_vehicle_id)}${
                        suggestionVehicle?.display_name ? ` · ${suggestionVehicle.display_name}` : ""
                      }`
                    : suggestion.target_edge_id !== undefined
                      ? describeEdgeTargetLabel(
                          suggestion.target_edge_id ?? undefined,
                          bundle?.render_geometry?.roads ?? [],
                        )
                      : null;
                const priorityLabel = normalizeReviewLevel(suggestion.priority, "medium");
                return (
                  <article key={suggestion.suggestion_id ?? suggestion.summary ?? "suggestion"} className={`review-card review-card-action review-card-${priorityLabel}`}>
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>{suggestion.summary ?? "No summary"}</strong>
                        <span>{suggestion.kind ?? "suggestion"}</span>
                      </div>
                      <div className="review-card-meta">
                        <span className={`review-level-chip review-level-chip-${priorityLabel}`}>{priorityLabel.toUpperCase()}</span>
                        {suggestionTargetLabel ? <span className="review-target-chip">{suggestionTargetLabel}</span> : null}
                      </div>
                    </div>
                    <div className="review-card-body">
                      {suggestion.target_vehicle_id !== undefined || suggestion.target_edge_id !== undefined
                        ? "This action is tied to a concrete target and can be executed or inspected directly."
                        : "This action is general guidance without a specific target."}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="review-empty-state">No actionable suggestions are available yet. The assistant has not returned a direct recommendation yet.</div>
            )}
          </div>
        </section>

        <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-context">
          <div className="analyze-section-header">
            <div>
              <h3>Supporting Context</h3>
              <p>Supporting context stays compact so the key review items remain easy to scan.</p>
            </div>
            <span className="analysis-section-chip">{reviewRecentCommands.length > 0 ? `${reviewRecentCommands.length} recent commands` : "context only"}</span>
          </div>

          {selectedInspection ? (
            <article className="review-card review-card-context analyze-context-card">
              <div className="review-card-header">
                <div className="review-card-title">
                  <strong>{selectedVehicle?.display_name ?? "Vehicle"} {formatMaybeNumber(selectedInspection.vehicle_id ?? null)}</strong>
                  <span>{selectedVehicle?.role_label ?? selectedInspection.operational_state ?? "unknown_state"}</span>
                </div>
                <span className="review-level-chip review-level-chip-info">Current target</span>
              </div>
              <div className="review-metric-grid" aria-label="Inspection metrics">
                <div className="review-metric"><span>Node</span><strong>{formatMaybeNumber(selectedInspection.current_node_id ?? null)}</strong></div>
                <div className="review-metric"><span>ETA</span><strong>{formatSeconds(selectedInspection.eta_s ?? null)}</strong></div>
                <div className="review-metric"><span>Job</span><strong>{selectedInspection.current_job_id ?? "none"}</strong></div>
                <div className="review-metric"><span>Wait</span><strong>{selectedInspection.wait_reason ?? "none"}</strong></div>
                <div className="review-metric"><span>Type</span><strong>{selectedVehicle?.vehicle_type ?? "GENERIC"}</strong></div>
                <div className="review-metric"><span>Control</span><strong>{selectedInspection.traffic_control_state ?? "none"}</strong></div>
              </div>
              <ul className="review-context-list">
                <li>Lane: {selectedVehicle?.lane_id ? `${selectedVehicle.lane_id} · ${selectedVehicle.lane_role ?? "travel"}` : "unassigned"}</li>
                <li>Lane direction: {selectedVehicle?.lane_directionality ?? "unknown"}</li>
                <li>Lane note: {selectedVehicle?.lane_selection_reason ?? "none"}</li>
                <li>Spacing: {formatMeters(selectedVehicle?.spacing_envelope_m ?? null)}</li>
                <li>Heading: {selectedVehicle ? `${Math.round((selectedVehicle.heading_rad ?? 0) * 180 / Math.PI)} deg` : "unknown"}</li>
                <li>{selectedInspection.traffic_control_detail ?? "No control detail"}</li>
              </ul>
            </article>
          ) : (
            <div className="review-empty-state">
              No vehicle is selected for analysis yet. Choose a vehicle in Operate or Fleet to populate inspection context, supporting context, and diagnostics.
            </div>
          )}

          {selectedVehicleIds.length > 1 ? (
            <article className="review-card review-card-context">
              <div className="review-card-header">
                <div className="review-card-title">
                  <strong>Fleet Selection</strong>
                  <span>multi-select</span>
                </div>
                <span className="review-level-chip review-level-chip-info">{selectedVehicleIds.length} vehicles</span>
              </div>
              <ul className="review-context-list">
                <li>Vehicles: {selectedVehicleIds.join(", ")}</li>
                <li>Selected records: {selectedVehicleIds.length}</li>
                <li>Route previews: {bundle?.command_center?.route_previews?.filter((preview) => selectedVehicleIds.includes(preview.vehicle_id ?? -1)).length ?? 0}</li>
                <li>Batch commands: assign and reposition apply to every selected vehicle.</li>
              </ul>
            </article>
          ) : null}

          <article className="review-card review-card-context analyze-command-card">
            <div className="review-card-header">
              <div className="review-card-title">
                <strong>Recent Commands</strong>
                <span>Latest operator actions</span>
              </div>
              <span className="review-level-chip review-level-chip-info">{reviewRecentCommands.length} shown</span>
            </div>
                  <div className="review-command-list">
              {reviewRecentCommands.length > 0 ? (
                reviewRecentCommands.map((command, commandIndex) => (
                  <div key={`${command.command_type ?? "command"}-${commandIndex}`} className="review-command-item">
                    <span className="review-command-kind">{command.command_type ?? "command"}</span>
                    <span className="review-command-summary">{describeRecentCommand(command)}</span>
                  </div>
                ))
              ) : (
                <div className="review-empty-state">No recent commands are available yet. The trace will appear here after the next operator action.</div>
              )}
            </div>
          </article>

          <div className="analyze-explanation-grid">
            {reviewExplanations.length > 0 ? (
              reviewExplanations.slice(0, 3).map((explanation, index) => {
                const explanationVehicle = findDisplayedVehicleById(displayedVehicles, explanation.vehicle_id ?? null);
                return (
                  <article key={`${explanation.vehicle_id ?? "explanation"}-${index}`} className="review-card review-card-context review-explanation-card">
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>Vehicle {formatMaybeNumber(explanation.vehicle_id ?? null)}</strong>
                        <span>{explanationVehicle?.display_name ?? explanationVehicle?.role_label ?? "explanation"}</span>
                      </div>
                      <span className="review-level-chip review-level-chip-info">Explanation</span>
                    </div>
                    <div className="review-card-body review-explanation-body">
                      {explanation.summary ?? "No explanation summary"}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="review-empty-state">No AI explanations are available yet. The assistant has not produced a vehicle-level note yet.</div>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
