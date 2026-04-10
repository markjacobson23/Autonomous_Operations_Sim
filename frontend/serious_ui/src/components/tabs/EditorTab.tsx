import { PanelHeader } from "../shared/PanelHeader";
import { formatMaybeNumber } from "../../viewModel";
import type { BundlePayload, EditTransaction, ValidationMessage } from "../../types";

type EditorTabProps = {
  bundle: BundlePayload | null;
  editorEnabled: boolean;
  draftTransaction: EditTransaction;
  validationMessages: ValidationMessage[];
  editorMessage: string;
  onToggleEditMode: () => void;
  onSaveScenario: () => void;
  onReloadScenario: () => void;
};

export function EditorTab({
  bundle,
  editorEnabled,
  draftTransaction,
  validationMessages,
  editorMessage,
  onToggleEditMode,
  onSaveScenario,
  onReloadScenario,
}: EditorTabProps): JSX.Element {
  const authoringBundle = bundle?.authoring;
  const editCount = draftTransaction.operations.length;
  const hasDraftEdits = editCount > 0;
  const validationBlocked = validationMessages.length > 0;
  const editorModeLabel = editorEnabled ? "Edit mode on" : "Edit mode off";
  const draftStatusLabel = hasDraftEdits
    ? `${editCount} staged edit${editCount === 1 ? "" : "s"}`
    : "No draft edits";
  const validationStatusLabel = validationBlocked ? "Validation blocked" : "Validation clean";
  const workingScenarioPath = authoringBundle?.working_scenario_path ?? "unavailable";
  const sourceScenarioPath = authoringBundle?.source_scenario_path ?? "unavailable";
  const authoringModeLabel = authoringBundle?.mode ?? "authoring";
  const editableNodeCount = formatMaybeNumber(authoringBundle?.editable_node_count ?? null);
  const editableRoadCount = formatMaybeNumber(authoringBundle?.editable_road_count ?? null);
  const editableAreaCount = formatMaybeNumber(authoringBundle?.editable_area_count ?? null);
  const editorSceneContextLabel = editorEnabled ? "Scene handles visible" : "Scene handles hidden";
  const editorSceneContextCopy = editorEnabled
    ? "The scene is now the authoring surface. Drag the visible node, road, and zone handles in place to stage geometry changes."
    : "The scene remains read-only until edit mode is enabled. Turn it on to reveal the authoring handles directly in the map.";
  const editorPrimaryActionLabel = validationBlocked
    ? "Resolve the validation issues before saving"
    : hasDraftEdits
      ? authoringBundle?.save_endpoint
        ? "Save the staged geometry into the working scenario"
        : "Saving is unavailable in this bundle"
      : editorEnabled
        ? "Start staging geometry changes in the scene"
        : "Enable edit mode to begin authoring";
  const editorPrimaryActionCopy = validationBlocked
    ? "Clear the messages below first, then use Save Scenario to persist the draft."
    : hasDraftEdits
      ? authoringBundle?.save_endpoint
        ? "Save will persist the staged edits and reload the live bundle."
        : "The draft is ready, but the current bundle cannot save it yet."
      : editorEnabled
        ? "Use the scene handles to build a draft directly on the map."
        : "Press Edit Scene to switch the scene into authoring mode.";

  return (
    <section className="panel info-panel editor-pane" aria-labelledby="editor-title">
      <PanelHeader
        eyebrow="Editor Region"
        title="Scenario Authoring"
        titleId="editor-title"
        lede="Working scenario controls, staged geometry, and validation live together here."
        className="compact editor-panel-header"
        meta={
          <div className="editor-header-stack" aria-label="Editor mode summary">
            <span className={`status-pill ${editorEnabled ? "accent" : "secondary"}`}>{editorModeLabel}</span>
            <span className={`status-pill ${hasDraftEdits ? "accent" : "secondary"}`}>{draftStatusLabel}</span>
            <span className={`status-pill ${validationBlocked ? "secondary" : "accent"}`}>{validationStatusLabel}</span>
          </div>
        }
      />
      <div className="section-stack">
        <div className="editor-mode-banner">
          <div className="editor-mode-copy">
            <p className="eyebrow">Working Scenario</p>
            <strong>{workingScenarioPath}</strong>
            <p>
              Source: {sourceScenarioPath} · Mode: {authoringModeLabel} · Save endpoint {authoringBundle?.save_endpoint ? "ready" : "unavailable"}
            </p>
            <div className="editor-next-action">
              <span className="editor-next-action-label">Primary next action</span>
              <strong>{editorPrimaryActionLabel}</strong>
              <p>{editorPrimaryActionCopy}</p>
            </div>
          </div>
          <div className="editor-status-grid">
            <div className="editor-status-card">
              <span>Edit mode</span>
              <strong>{editorModeLabel}</strong>
              <p>{editorEnabled ? "Handles are active and geometry moves will stage into the draft." : "Turn edit mode on to stage geometry changes and reveal the authoring handles."}</p>
            </div>
            <div className="editor-status-card">
              <span>Draft edits</span>
              <strong>{draftStatusLabel}</strong>
              <p>{hasDraftEdits ? "Save to persist the staged geometry or reload to discard it." : "No staged geometry edits are present yet. Enable edit mode and move a handle to start a draft."}</p>
            </div>
            <div className="editor-status-card">
              <span>Validation</span>
              <strong>{validationStatusLabel}</strong>
              <p>{validationBlocked ? "Resolve the messages below before saving." : "Validation is clean and the working scenario is ready."}</p>
            </div>
            <div className="editor-status-card editor-status-card-context">
              <span>Editable scene</span>
              <strong>
                {editableNodeCount} nodes · {editableRoadCount} roads · {editableAreaCount} zones
              </strong>
              <p>{editorEnabled ? "The scene is open for authoring, with node, road, and zone handles active in place." : "Enable edit mode to reveal the editable handles directly in the scene."}</p>
            </div>
          </div>
        </div>

        <div className="subsection editor-controls">
          <div className="subsection-header">
            <h3>Authoring Controls</h3>
            <span className={`status-pill ${editorEnabled ? "accent" : "secondary"}`}>{editorEnabled ? "Ready to author" : "Edit mode paused"}</span>
          </div>
          <div className="action-row editor-action-row">
            <button className="scene-button scene-button-primary editor-primary-action" type="button" onClick={onToggleEditMode}>
              {editorEnabled ? "Pause Edit Mode" : "Edit Scene"}
            </button>
            <button className="scene-button scene-button-primary" type="button" onClick={onSaveScenario} disabled={!authoringBundle?.save_endpoint || !hasDraftEdits}>
              Save Scenario
            </button>
            <button className="scene-button" type="button" onClick={onReloadScenario} disabled={!authoringBundle?.reload_endpoint}>
              Reload Scenario
            </button>
          </div>
          <p className="status-copy">{editorMessage}</p>
        </div>

        <div className="editor-detail-grid">
          <div className="overview-card editor-state-card">
            <div className="subsection-header">
              <p className="eyebrow">Scene Editing Context</p>
              <span className={`status-pill ${editorEnabled ? "accent" : "secondary"}`}>{editorSceneContextLabel}</span>
            </div>
            <p className="editor-scene-context-copy">{editorSceneContextCopy}</p>
            <ul className="mini-list editor-state-list">
              <li>Working copy: {workingScenarioPath}</li>
              <li>Source scenario: {sourceScenarioPath}</li>
              <li>Save endpoint: {authoringBundle?.save_endpoint ? "ready" : "unavailable"}</li>
              <li>
                Geometry: {formatMaybeNumber(authoringBundle?.editable_node_count ?? null)} nodes · {formatMaybeNumber(authoringBundle?.editable_road_count ?? null)} roads · {formatMaybeNumber(authoringBundle?.editable_area_count ?? null)} zones
              </li>
            </ul>
          </div>
          <div className="subsection editor-validation-card">
            <div className="subsection-header">
              <h3>Validation Messages</h3>
              <span className={`status-pill ${validationBlocked ? "secondary" : "accent"}`}>{validationStatusLabel}</span>
            </div>
            <ul className="editor-message-list">
              {validationMessages.length > 0 ? (
                validationMessages.map((message, index) => {
                  const severity = (message.severity ?? "info").toLowerCase();
                  return (
                    <li key={`${message.code ?? "validation"}-${index}`} className={`editor-validation-item editor-validation-item-${severity}`}>
                      <div className="editor-item-heading">
                        <strong>{message.code ?? severity.toUpperCase()}</strong>
                        <span className="editor-item-chip">
                          {message.target_kind ?? "global"}
                          {message.target_id !== undefined && message.target_id !== null ? ` · ${message.target_id}` : ""}
                        </span>
                      </div>
                      <p>{message.message ?? "No validation message"}</p>
                    </li>
                  );
                })
              ) : (
                <li className="editor-empty-state">
                  No validation issues are blocking the draft yet. If Save Scenario is disabled, the
                  draft may still be empty or the save endpoint may be unavailable.
                </li>
              )}
            </ul>
          </div>
          <div className="subsection editor-draft-card">
            <div className="subsection-header">
              <h3>Draft Operations</h3>
              <span className={`status-pill ${hasDraftEdits ? "accent" : "secondary"}`}>{draftStatusLabel}</span>
            </div>
            <ul className="editor-operation-list">
              {draftTransaction.operations.length > 0 ? (
                draftTransaction.operations.map((operation, index) => (
                  <li key={`${operation.kind}-${operation.target_id}-${index}`} className="editor-draft-item">
                    <div className="editor-item-heading">
                      <strong>{operation.kind.split("_").join(" ")}</strong>
                      <span className="editor-item-chip">
                        {operation.kind === "move_node"
                          ? `node ${operation.target_id}`
                          : operation.kind === "set_road_centerline"
                            ? `road ${operation.target_id}`
                            : `zone ${operation.target_id}`}
                      </span>
                    </div>
                    <p>
                      {operation.kind === "move_node"
                        ? `move node ${operation.target_id} to ${operation.position.join(", ")}`
                        : operation.kind === "set_road_centerline"
                          ? `edit road ${operation.target_id} with ${operation.points.length} centerline point(s)`
                          : `edit zone ${operation.target_id} with ${operation.points.length} polygon vertex/vertices`}
                    </p>
                  </li>
                ))
              ) : (
                <li className="editor-empty-state">
                  No geometry edits are staged yet. Turn on edit mode and move a node, road, or zone
                  to create the first draft change.
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
