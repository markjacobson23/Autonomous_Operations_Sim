import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

import {
  reloadAuthoringState,
  saveAuthoringEdits,
  validateAuthoringEdits,
} from "../api/liveClient";
import type {
  BundlePayload,
  EditTransaction,
  ValidationMessage,
} from "../types";

export const emptyTransaction: EditTransaction = {
  label: "live_geometry_edit",
  operations: [],
};

export type UseAuthoringResult = {
  editorEnabled: boolean;
  draftTransaction: EditTransaction;
  validationMessages: ValidationMessage[];
  editorMessage: string;
  isValidating: boolean;
  isSaving: boolean;
  isReloading: boolean;
  setEditorEnabled: Dispatch<SetStateAction<boolean>>;
  setDraftTransaction: Dispatch<SetStateAction<EditTransaction>>;
  setValidationMessages: Dispatch<SetStateAction<ValidationMessage[]>>;
  setEditorMessage: Dispatch<SetStateAction<string>>;
  toggleEditMode: () => void;
  saveScenario: () => Promise<void>;
  reloadScenario: () => Promise<void>;
};

export function useAuthoring({
  bundle,
  applyLoadedBundle,
}: {
  bundle: BundlePayload | null;
  applyLoadedBundle: (bundlePayload: BundlePayload, message: string) => void;
}): UseAuthoringResult {
  const [editorEnabled, setEditorEnabled] = useState(false);
  const [draftTransaction, setDraftTransaction] = useState<EditTransaction>(emptyTransaction);
  const [validationMessages, setValidationMessages] = useState<ValidationMessage[]>([]);
  const [editorMessage, setEditorMessage] = useState("Authoring surface is ready.");
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  const authoring = bundle?.authoring;

  useEffect(() => {
    if (!authoring?.validate_endpoint || draftTransaction.operations.length === 0) {
      setValidationMessages([]);
      return;
    }

    let cancelled = false;
    setIsValidating(true);
    void validateAuthoringEdits(authoring.validate_endpoint, draftTransaction)
      .then((payload) => {
        if (!cancelled) {
          setValidationMessages(payload.validation_messages ?? []);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Validation request failed";
          setValidationMessages([
            {
              severity: "error",
              code: "validation_request_failed",
              message,
            },
          ]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsValidating(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [authoring?.validate_endpoint, draftTransaction]);

  const toggleEditMode = useCallback(() => {
    setEditorEnabled((current) => {
      const next = !current;
      setEditorMessage(
        next
          ? "Edit mode enabled. The scene handles are visible now, so you can stage geometry changes directly on the map."
          : "Edit mode paused. Draft mutations are preserved until you save or reload.",
      );
      return next;
    });
  }, []);

  const saveScenario = useCallback(async () => {
    if (!authoring?.save_endpoint || draftTransaction.operations.length === 0) {
      return;
    }
    setIsSaving(true);
    setEditorMessage("Saving live geometry edits into the working scenario...");
    try {
      const payload = await saveAuthoringEdits(authoring.save_endpoint, draftTransaction);
      setValidationMessages(payload.validation_messages ?? []);
      if (!payload.ok || !payload.bundle) {
        setEditorMessage(
          "Save rejected. Review the validation panel, clear the blocking items, and try again.",
        );
        return;
      }
      applyLoadedBundle(payload.bundle, "Live authoring save completed.");
      setDraftTransaction(emptyTransaction);
      setEditorMessage("Scenario changes saved and live bundle reloaded.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Save request failed";
      setEditorMessage(`Save request failed. ${message}`);
    } finally {
      setIsSaving(false);
    }
  }, [applyLoadedBundle, authoring?.save_endpoint, draftTransaction]);

  const reloadScenario = useCallback(async () => {
    if (!authoring?.reload_endpoint) {
      return;
    }
    setIsReloading(true);
    setEditorMessage("Reloading working scenario from the Python authoring surface...");
    try {
      const payload = await reloadAuthoringState(authoring.reload_endpoint);
      if (!payload.ok || !payload.bundle) {
        throw new Error("Reload response did not include a bundle.");
      }
      applyLoadedBundle(payload.bundle, "Working scenario reloaded.");
      setDraftTransaction(emptyTransaction);
      setValidationMessages([]);
      setEditorMessage("Working scenario reloaded and draft edits cleared.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Reload request failed";
      setEditorMessage(`Reload request failed. ${message}`);
    } finally {
      setIsReloading(false);
    }
  }, [applyLoadedBundle, authoring?.reload_endpoint]);

  return {
    editorEnabled,
    draftTransaction,
    validationMessages,
    editorMessage,
    isValidating,
    isSaving,
    isReloading,
    setEditorEnabled,
    setDraftTransaction,
    setValidationMessages,
    setEditorMessage,
    toggleEditMode,
    saveScenario,
    reloadScenario,
  };
}
