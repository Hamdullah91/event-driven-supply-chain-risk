import { afterEach, describe, expect, it } from "vitest";
import { useUiStore } from "./uiStore";

function resetStore() {
  useUiStore.setState({
    inspectorRef: null,
    highlightedPathId: null,
    selectedGraphObjectId: null,
    newRiskNotification: null,
  });
}

afterEach(resetStore);

describe("Phase 3 ephemeral UI state", () => {
  it("does not let a real-time notification hijack active investigation selection", () => {
    useUiStore.getState().setInspectorRef({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    useUiStore.getState().setSelectedGraphObjectId("company:nvidia");
    useUiStore.getState().setHighlightedPathId("path:nvidia");

    useUiStore.getState().setNewRiskNotification({ companyId: "amd", eventId: "evt-2", timestamp: "2026-09-25T01:00:00Z" });

    expect(useUiStore.getState().inspectorRef?.id).toBe("nvidia");
    expect(useUiStore.getState().selectedGraphObjectId).toBe("company:nvidia");
    expect(useUiStore.getState().highlightedPathId).toBe("path:nvidia");
    expect(useUiStore.getState().newRiskNotification?.companyId).toBe("amd");
  });

  it("clearSelection clears the visible selection, Inspector, and path together without discarding update state", () => {
    useUiStore.getState().setInspectorRef({ kind: "event", id: "evt-1", entityType: "Event" });
    useUiStore.getState().setSelectedGraphObjectId("evt-1");
    useUiStore.getState().setHighlightedPathId("path-1");
    useUiStore.getState().setNewRiskNotification({ companyId: "nvidia", timestamp: "2026-09-25T01:00:00Z" });

    useUiStore.getState().clearSelection();

    expect(useUiStore.getState().inspectorRef).toBeNull();
    expect(useUiStore.getState().selectedGraphObjectId).toBeNull();
    expect(useUiStore.getState().highlightedPathId).toBeNull();
    expect(useUiStore.getState().newRiskNotification?.companyId).toBe("nvidia");
  });
});
