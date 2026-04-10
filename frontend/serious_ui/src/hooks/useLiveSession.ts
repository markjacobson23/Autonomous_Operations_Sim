import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

import { loadLiveBundle, sendLiveCommand, sendSessionControl } from "../api/liveClient";
import type {
  BootstrapSummary,
  BundlePayload,
  JsonRecord,
  SessionControlPayload,
} from "../types";

function buildBootstrapSummary(
  bundle: BundlePayload,
  message: string,
): BootstrapSummary {
  const snapshot = bundle.snapshot ?? {};
  const commandCenter = bundle.command_center ?? {};
  const recentCommands = commandCenter.recent_commands ?? [];
  const suggestions = commandCenter.ai_assist?.suggestions ?? [];
  const anomalies = commandCenter.ai_assist?.anomalies ?? [];
  const routePreviews = commandCenter.route_previews ?? [];
  const summary = bundle.summary ?? null;
  return {
    loadState: "loaded",
    surfaceName: bundle.metadata?.surface_name ?? "live_bundle",
    seed: bundle.seed ?? null,
    simulatedTimeS: bundle.simulated_time_s ?? snapshot.simulated_time_s ?? null,
    vehicleCount: (snapshot.vehicles ?? []).length,
    blockedEdgeCount: snapshot.blocked_edge_ids?.length ?? 0,
    traceEventCount: Array.isArray(bundle.trace_events) ? bundle.trace_events.length : null,
    selectedVehicleCount: (commandCenter.selected_vehicle_ids ?? []).length,
    recentCommandCount: recentCommands.length,
    suggestionCount: suggestions.length,
    anomalyCount: anomalies.length,
    routePreviewCount: routePreviews.length,
    message,
    commandCenter,
    summary,
    bundle,
  };
}

const initialBootstrap: BootstrapSummary = {
  loadState: "idle",
  surfaceName: "unbound",
  seed: null,
  simulatedTimeS: null,
  vehicleCount: null,
  blockedEdgeCount: null,
  traceEventCount: null,
  selectedVehicleCount: null,
  recentCommandCount: null,
  suggestionCount: null,
  anomalyCount: null,
  routePreviewCount: null,
  message: "No live bundle is connected yet.",
  commandCenter: {},
  summary: null,
  bundle: null,
};

export type UseLiveSessionResult = {
  bundlePath: string | null;
  bootstrap: BootstrapSummary;
  bundle: BundlePayload | null;
  liveCommandMessage: string;
  setLiveCommandMessage: Dispatch<SetStateAction<string>>;
  setBundlePath: Dispatch<SetStateAction<string | null>>;
  applyLoadedBundle: (bundlePayload: BundlePayload, message: string) => void;
  refreshBundle: () => Promise<void>;
  submitLiveCommand: (payload: JsonRecord) => Promise<void>;
  controlLiveSession: (
    action: "play" | "pause" | "step",
    options?: { selectedVehicleIds?: number[]; deltaSeconds?: number },
  ) => Promise<void>;
  sessionControl: SessionControlPayload | null;
};

export function useLiveSession(): UseLiveSessionResult {
  const [bundlePath, setBundlePath] = useState<string | null>(() =>
    typeof window === "undefined"
      ? null
      : new URLSearchParams(window.location.search).get("bundle"),
  );
  const [bootstrap, setBootstrap] = useState<BootstrapSummary>(initialBootstrap);
  const [bundle, setBundle] = useState<BundlePayload | null>(null);
  const [liveCommandMessage, setLiveCommandMessage] = useState(
    "Live command controls are ready.",
  );

  const applyLoadedBundle = useCallback((bundlePayload: BundlePayload, message: string) => {
    setBundle(bundlePayload);
    setBootstrap(buildBootstrapSummary(bundlePayload, message));
  }, []);

  const loadAndApplyBundle = useCallback(
    async (path: string, message: string) => {
      setBootstrap((current) => ({
        ...current,
        loadState: "loading",
        message,
      }));
      try {
        const loadedBundle = await loadLiveBundle(path);
        applyLoadedBundle(loadedBundle, message);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown bootstrap error";
        setBootstrap({
          ...initialBootstrap,
          loadState: "error",
          surfaceName: "bootstrap_failed",
          message: `Live bundle bootstrap failed: ${errorMessage}`,
        });
      }
    },
    [applyLoadedBundle],
  );

  useEffect(() => {
    if (!bundlePath) {
      return;
    }
    void loadAndApplyBundle(bundlePath, `Loading live bundle from ${bundlePath}`);
  }, [bundlePath, loadAndApplyBundle]);

  useEffect(() => {
    const sessionControl = bundle?.session_control;
    if (sessionControl?.play_state !== "playing" || !bundlePath) {
      return;
    }

    let cancelled = false;
    const refresh = () => {
      void loadLiveBundle(bundlePath)
        .then((loadedBundle) => {
          if (!cancelled) {
            setBootstrap((current) => buildBootstrapSummary(loadedBundle, current.message));
            setBundle(loadedBundle);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setLiveCommandMessage(
              "Live bundle refresh failed. Use Reconnect Bundle to retry the live snapshot.",
            );
          }
        });
    };

    const intervalId = window.setInterval(refresh, 2000);
    refresh();
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [bundle, bundlePath]);

  const refreshBundle = useCallback(async () => {
    if (!bundlePath) {
      return;
    }
    await loadAndApplyBundle(bundlePath, bootstrap.message);
  }, [bootstrap.message, bundlePath, loadAndApplyBundle]);

  const submitLiveCommand = useCallback(
    async (payload: JsonRecord) => {
      const endpoint =
        bundle?.session_control?.command_endpoint ?? "/api/live/command";
      setLiveCommandMessage("Sending live command to the Python session...");
      try {
        const response = await sendLiveCommand(endpoint, payload);
        if (response.bundle) {
          applyLoadedBundle(
            response.bundle,
            response.ok ? "Live command applied." : "Live command response returned.",
          );
        }
        setLiveCommandMessage(
          (response.command_result as { message?: string | null } | undefined)?.message ??
            (response.ok ? "Command accepted." : "Command rejected."),
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : "Command request failed";
        setLiveCommandMessage(`Command request failed. ${message}`);
      }
    },
    [applyLoadedBundle, bundle],
  );

  const controlLiveSession = useCallback(
    async (
      action: "play" | "pause" | "step",
      options: { selectedVehicleIds?: number[]; deltaSeconds?: number } = {},
    ) => {
      const endpoint =
        bundle?.session_control?.session_control_endpoint ?? "/api/live/session/control";
      const deltaSeconds =
        options.deltaSeconds ?? bundle?.session_control?.step_seconds ?? 0.5;
      setLiveCommandMessage(
        action === "step"
          ? "Advancing the live session by one explicit step..."
          : action === "play"
            ? "Setting live session refresh to play mode..."
            : "Pausing live session refresh...",
      );
      try {
        const response = await sendSessionControl(endpoint, {
          action,
          delta_s: deltaSeconds,
          selected_vehicle_ids: options.selectedVehicleIds ?? [],
        } as SessionControlPayload & JsonRecord);
        if (response.bundle) {
          applyLoadedBundle(
            response.bundle,
            action === "step" ? "Live session advanced by one step." : "Session control updated.",
          );
        }
        setLiveCommandMessage(
          action === "step"
            ? "Single-step completed."
            : action === "play"
              ? "Session refresh set to play mode."
              : "Session refresh paused.",
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : "Session control failed";
        setLiveCommandMessage(`Session control failed. ${message}`);
      }
    },
    [applyLoadedBundle, bundle],
  );

  return {
    bundlePath,
    bootstrap,
    bundle,
    liveCommandMessage,
    setLiveCommandMessage,
    setBundlePath,
    applyLoadedBundle,
    refreshBundle,
    submitLiveCommand,
    controlLiveSession,
    sessionControl: bundle?.session_control ?? null,
  };
}
