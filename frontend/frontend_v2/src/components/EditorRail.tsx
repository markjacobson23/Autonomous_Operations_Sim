import { useMemo, useState } from "react";

import type { LiveBundleViewModel } from "../adapters/liveBundle";
import type { FrontendUiState } from "../state/frontendUiState";

type EditorRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  refreshBundle: () => void;
};

type ValidationMessage = {
  tone: "info" | "warn" | "error";
  title: string;
  message: string;
};

type EditorFeedback = {
  tone: "idle" | "pending" | "success" | "warn";
  title: string;
  message: string;
};

const initialEditorFeedback: EditorFeedback = {
  tone: "idle",
  title: "Editor baseline ready",
  message: "This surface is intentionally read-only for now and acts as the home for later authoring work.",
};

export function EditorRail({ bundle, uiState, refreshBundle }: EditorRailProps): JSX.Element {
  const [draftName, setDraftName] = useState("Untitled scene draft");
  const [feedback, setFeedback] = useState<EditorFeedback>(initialEditorFeedback);

  const validationMessages = useMemo(() => buildValidationMessages(bundle, uiState), [bundle, uiState]);
  const validationCount = validationMessages.filter((message) => message.tone !== "info").length;

  function handleSaveDraft() {
    setFeedback({
      tone: "warn",
      title: "Save transport not bound",
      message: "The Editor baseline is wired for the future save flow, but no authoring endpoint is available yet.",
    });
  }

  function handleReloadBundle() {
    setFeedback({
      tone: "pending",
      title: "Reloading bundle",
      message: "Requesting a fresh authoritative bundle from the Python simulator.",
    });
    refreshBundle();
  }

  return (
    <section className="panel editor-rail">
      <div className="panel-topline">
        <div>
          <p className="panel-kicker">Editor</p>
          <h2>Editor mode baseline</h2>
        </div>
        <div className="panel-metrics">
          <span>{validationCount} non-info validation item(s)</span>
          <span>{bundle.loadState}</span>
          <span>{uiState.modePanel.activeMode}</span>
        </div>
      </div>

      <p className="stack-copy">
        Editor mode is the authoring home for later work. It stays visibly different from Operate, keeps the map primary, and surfaces validation
        and save/reload affordances without pretending deep editing exists yet.
      </p>

      <section className="editor-summary-card">
        <div className="editor-summary-head">
          <div>
            <p className="panel-kicker">Authoring surface</p>
            <h3>Draft workspace</h3>
          </div>
          <span className="selection-popup-badge">Read-only baseline</span>
        </div>
        <p className="stack-copy">
          Source scenario: <strong>{bundle.sessionIdentity.scenarioPath}</strong>
        </p>
        <p className="stack-copy">
          Environment: <strong>{bundle.map.environment.displayName}</strong> · Play state: <strong>{bundle.sessionIdentity.playState}</strong>
        </p>
        <label className="operate-field">
          <span>Draft name</span>
          <input
            type="text"
            value={draftName}
            onChange={(event) => setDraftName(event.currentTarget.value)}
            placeholder="Untitled scene draft"
          />
        </label>
      </section>

      <section className="editor-section">
        <div className="editor-section-head">
          <div>
            <h3>Validation messages</h3>
            <p>These checks stay grounded in bundle truth and highlight what still needs a real editor transport later.</p>
          </div>
          <span className="selection-popup-badge">{validationMessages.length} item(s)</span>
        </div>
        <div className="editor-validation-list">
          {validationMessages.map((message) => (
            <article key={`${message.tone}-${message.title}-${message.message}`} className={`editor-validation-card editor-validation-${message.tone}`}>
              <div className="editor-validation-card-head">
                <strong>{message.title}</strong>
                <span>{message.tone}</span>
              </div>
              <p>{message.message}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="editor-section">
        <div className="editor-section-head">
          <div>
            <h3>Save / reload flow</h3>
            <p>A real UI home for future authoring transport, with reload already wired to the authoritative bundle refresh.</p>
          </div>
        </div>
        <div className="editor-flow-card">
          <div className="editor-flow-card-copy">
            <strong>{draftName}</strong>
            <p>{feedback.message}</p>
          </div>
          <div className="editor-flow-actions">
            <button type="button" className="scene-button-primary" onClick={handleSaveDraft}>
              Save draft
            </button>
            <button type="button" className="scene-button-primary" onClick={handleReloadBundle}>
              Reload bundle
            </button>
          </div>
        </div>
        <p className="editor-flow-note">
          Save is a deliberate future hook. Reload stays live and authoritative by pulling a fresh Python-simulated bundle.
        </p>
      </section>

      <section className="editor-section editor-roadmap-card">
        <div className="editor-section-head">
          <div>
            <h3>Authoring home</h3>
            <p>The real editing tools can land here later without changing the surrounding mode architecture.</p>
          </div>
        </div>
        <ul className="list-copy">
          <li>Scene graph editing and placement tools.</li>
          <li>Topology-aware validation and warnings.</li>
          <li>Draft save transport and reload reconciliation.</li>
          <li>Selection-aware editing affordances on the map.</li>
        </ul>
      </section>

      <section className="editor-section">
        <div className="editor-feedback" aria-live="polite">
          <div className="editor-feedback-head">
            <p className="panel-kicker">Feedback</p>
            <span className={`selection-popup-badge editor-feedback-badge-${feedback.tone}`}>{feedback.tone}</span>
          </div>
          <strong>{feedback.title}</strong>
          <p>{feedback.message}</p>
        </div>
      </section>
    </section>
  );
}

function buildValidationMessages(bundle: LiveBundleViewModel, uiState: FrontendUiState): ValidationMessage[] {
  return [
    {
      tone: bundle.loadState === "error" ? "error" : "info",
      title: "Bundle connection",
      message:
        bundle.loadState === "error"
          ? bundle.loadMessage
          : bundle.loadState === "ready"
            ? "Authoritative bundle is connected and ready for read-only editor inspection."
            : "Waiting for the authoritative bundle to load.",
    },
    {
      tone: "info",
      title: "Source scenario",
      message: `${bundle.sessionIdentity.scenarioPath} · surface ${bundle.sessionIdentity.surfaceName}`,
    },
    {
      tone: bundle.map.environment.displayName === "unknown environment" ? "warn" : "info",
      title: "Environment context",
      message:
        bundle.map.environment.displayName === "unknown environment"
          ? "Environment metadata is not fully populated yet."
          : `Editing home is anchored to ${bundle.map.environment.displayName}.`,
    },
    {
      tone: bundle.commandSurface.commandEndpoint === "unknown" ? "warn" : "info",
      title: "Authoring transport",
      message:
        bundle.commandSurface.commandEndpoint === "unknown"
          ? "No editor mutation endpoint is exposed in the current live bundle."
          : "Mutation transport is available through the current bundle.",
    },
    {
      tone: uiState.selection.vehicleIds.length > 0 ? "warn" : "info",
      title: "Selection state",
      message:
        uiState.selection.vehicleIds.length > 0
          ? `${uiState.selection.vehicleIds.length} selected vehicle(s) will remain editable only after later authoring wiring.`
          : "No active selection is blocking editor setup.",
    },
  ];
}
