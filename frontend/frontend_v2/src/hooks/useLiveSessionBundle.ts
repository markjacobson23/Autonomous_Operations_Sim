import { useCallback, useEffect, useRef, useState } from "react";

import type { LiveBundleResource, LoadState, JsonRecord } from "../adapters/liveBundle";

export function useLiveSessionBundle(): LiveBundleResource {
  const [bundle, setBundle] = useState<JsonRecord | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadMessage, setLoadMessage] = useState("Connecting to live session bundle...");
  const [refreshNonce, setRefreshNonce] = useState(0);
  const hasLoadedRef = useRef(false);
  const [bundleUrl] = useState(() => {
    return new URLSearchParams(window.location.search).get("bundle") ?? "/live_session_bundle.json";
  });

  const refresh = useCallback(() => {
    setRefreshNonce((currentNonce) => currentNonce + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const resolvedBundleUrl = new URL(bundleUrl, window.location.href).toString();

    async function loadBundle() {
      if (!hasLoadedRef.current) {
        setLoadState("loading");
        setLoadMessage(refreshNonce === 0 ? `Connecting to ${bundleUrl}...` : `Refreshing ${bundleUrl}...`);
      } else {
        setLoadState("ready");
        setLoadMessage(`Refreshing ${bundleUrl}...`);
      }
      try {
        const response = await fetch(resolvedBundleUrl, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }

        const payload: unknown = await response.json();
        if (!isRecord(payload)) {
          throw new Error("Live bundle did not decode to an object");
        }

        setBundle(payload);
        hasLoadedRef.current = true;
        setLoadState("ready");
        setLoadMessage("Live session connected");
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        if (!hasLoadedRef.current) {
          setBundle(null);
          setLoadState("error");
        } else {
          setLoadState("error");
        }
        setLoadMessage(error instanceof Error ? error.message : "Unable to load live bundle");
      }
    }

    void loadBundle();
    return () => controller.abort();
  }, [bundleUrl, refreshNonce]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      refresh();
    }, 2500);
    return () => window.clearInterval(intervalId);
  }, [refresh]);

  return {
    bundleUrl,
    loadState,
    loadMessage,
    bundle,
    refresh,
  };
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
