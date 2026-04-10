import type { ReactNode } from "react";

import { StateCallout } from "./shared/StateCallout";
import type { BootstrapSummary } from "../types";
import type { WorkspaceTab } from "../types";
import { architecture } from "../viewModel";

type WorkspaceShellProps = {
  shellClassName: string;
  bootstrap: BootstrapSummary;
  selectedVehicleCount: number;
  minDisplayedSpacingLabel: string;
  queuedVehicleCount: number;
  congestedRoadCount: number;
  editCount: number;
  validationCount: number;
  activeTab: WorkspaceTab;
  tabs: Array<{
    id: WorkspaceTab;
    label: string;
    summary: string;
  }>;
  onTabChange: (tab: WorkspaceTab) => void;
  bundleStatusTitle: string;
  bundleStatusCopy: string;
  bundleStatusAction: string;
  bundleStatusTone: "muted" | "loading" | "warning" | "error" | "success";
  children: ReactNode;
};

export function WorkspaceShell({
  shellClassName,
  bootstrap,
  selectedVehicleCount,
  minDisplayedSpacingLabel,
  queuedVehicleCount,
  congestedRoadCount,
  editCount,
  validationCount,
  activeTab,
  tabs,
  onTabChange,
  bundleStatusTitle,
  bundleStatusCopy,
  bundleStatusAction,
  bundleStatusTone,
  children,
}: WorkspaceShellProps): JSX.Element {
  return (
    <div className={shellClassName}>
      <div className="shell-accent shell-accent-left" aria-hidden="true" />
      <div className="shell-accent shell-accent-right" aria-hidden="true" />
      <header className="masthead panel">
        <div className="masthead-copy">
          <p className="eyebrow">Final UI cleanup pass</p>
          <h1>Autonomous Ops Command Deck</h1>
          <p className="lede">
            Stop lines, yield controls, and protected conflict areas are now visible in the serious
            UI, so controlled junctions show why vehicles are pausing instead of flattening traffic
            into a single static line.
          </p>
        </div>
        <div className="masthead-meta">
          <div className="badge-row" aria-label="Architecture decisions">
            <span className="badge">Primary: {architecture.primaryStack}</span>
            <span className="badge">Authority: {architecture.authority}</span>
            <span className="badge accent-2">{architecture.launchMode}</span>
          </div>
          <div className="toolbar-strip" aria-label="Top toolbar">
            <button className="toolbar-button" type="button">
              Launch Live Run
            </button>
            <button className="toolbar-button" type="button">
              Reconnect Bundle
            </button>
          </div>
        </div>
      </header>

      <section className="session-bar panel" aria-label="Session metadata">
        <div className="metric-pill">
          <span className="metric-label">Bundle</span>
          <strong>{bootstrap.surfaceName}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Seed</span>
          <strong>{bootstrap.seed === null ? "pending" : String(bootstrap.seed)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Simulated Time</span>
          <strong>{bootstrap.simulatedTimeS === null ? "pending" : `${bootstrap.simulatedTimeS.toFixed(1)}s`}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Vehicles</span>
          <strong>{bootstrap.vehicleCount === null ? "pending" : String(bootstrap.vehicleCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Selected Fleet</span>
          <strong>{String(selectedVehicleCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Min Spacing</span>
          <strong>{minDisplayedSpacingLabel}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Queued Vehicles</span>
          <strong>{String(queuedVehicleCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Congested Roads</span>
          <strong>{String(congestedRoadCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Pending Edits</span>
          <strong>{String(editCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Validation</span>
          <strong>{validationCount === 0 ? "clean" : `${validationCount} issue(s)`}</strong>
        </div>
        <div className={`health-pill health-pill-${bootstrap.loadState}`}>
          {bootstrap.loadState === "loading"
            ? "CONNECTING"
            : bootstrap.loadState === "error"
              ? "RECONNECT"
              : bootstrap.loadState === "loaded"
                ? "READY"
                : "UNBOUND"}
        </div>
      </section>

      <section
        className={`bundle-status-strip panel bundle-status-${bootstrap.loadState}`}
        aria-label="Bundle connection status"
      >
        <StateCallout
          title={bundleStatusTitle}
          copy={bundleStatusCopy}
          action={bundleStatusAction}
          tone={bundleStatusTone}
        />
      </section>

      <nav className="workspace-tabs panel" aria-label="Workspace tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab workspace-tab-${tab.id} ${activeTab === tab.id ? "workspace-tab-active" : ""}`}
            type="button"
            onClick={() => onTabChange(tab.id)}
            aria-pressed={activeTab === tab.id}
          >
            <strong>{tab.label}</strong>
            <span>{tab.summary}</span>
          </button>
        ))}
      </nav>

      <main className="workspace">{children}</main>
    </div>
  );
}
