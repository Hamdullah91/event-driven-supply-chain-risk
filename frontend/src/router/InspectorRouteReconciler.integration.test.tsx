import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";

import { useUiStore, type InspectorRef } from "../state/uiStore";
import { InspectorRouteReconciler } from "./InspectorRouteReconciler";

function Harness() {
  const navigate = useNavigate();
  const location = useLocation();
  const clearSelection = useUiStore((state) => state.clearSelection);

  return <>
    <InspectorRouteReconciler />
    <output data-testid="location">{`${location.pathname}${location.search}`}</output>
    <button type="button" onClick={() => navigate("/events")}>Go Events</button>
    <button type="button" onClick={() => navigate("/events/evt-1")}>Go Event One</button>
    <button type="button" onClick={() => navigate("/companies/tsmc")}>Go TSMC</button>
    <button type="button" onClick={() => navigate("/companies/nvidia")}>Go NVIDIA</button>
    <button type="button" onClick={() => navigate("/network?mode=structure&focusType=Company&focusId=tsmc&depth=2")}>TSMC Depth Two</button>
    <button type="button" onClick={() => navigate("/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=2")}>Event Impact Hop Two</button>
    <button type="button" onClick={() => navigate("/network?mode=structure&focusType=Company&focusId=samsung&depth=1")}>Samsung Focus</button>
    <button type="button" onClick={() => navigate(-1)}>Back</button>
    <button type="button" onClick={() => navigate(1)}>Forward</button>
    <button type="button" onClick={() => navigate("/events")}>Inspector Action Events</button>
    <button type="button" onClick={() => { clearSelection(); navigate("/events"); }}>Sidebar Events</button>
  </>;
}

function renderHarness(initialEntries: string[], initialIndex = 0) {
  return render(
    <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
      <Harness />
    </MemoryRouter>,
  );
}

function setInspector(inspectorRef: InspectorRef) {
  useUiStore.setState({ inspectorRef });
}

function expectInspectorId(id: string | null) {
  expect(useUiStore.getState().inspectorRef?.id ?? null).toBe(id);
}

afterEach(() => {
  useUiStore.setState({
    inspectorRef: null,
    highlightedPathId: null,
    selectedGraphObjectId: null,
    newRiskNotification: null,
  });
});

describe("Inspector route lifecycle", () => {
  it("B1 clears a Company Inspector when navigating to Events", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/companies/nvidia"]);
    expectInspectorId("nvidia");

    await userEvent.click(screen.getByRole("button", { name: "Go Events" }));
    await waitFor(() => expectInspectorId(null));
  });

  it("B2 clears an Event Inspector when navigating to an unrelated Company profile", async () => {
    setInspector({ kind: "event", id: "evt-1", entityType: "Event", name: "FACILITY_OUTAGE" });
    renderHarness(["/events/evt-1"]);

    await userEvent.click(screen.getByRole("button", { name: "Go TSMC" }));
    await waitFor(() => expectInspectorId(null));
  });

  it("B3 clears a Network Relationship Inspector when leaving Network", async () => {
    setInspector({
      kind: "relationship",
      id: "rel-1",
      name: "SUPPLIES",
      context: { graphFocusId: "tsmc", graphDepth: 1, relationshipId: "rel-1" },
    });
    renderHarness(["/network?mode=structure&focusType=Company&focusId=tsmc&depth=1"]);

    await userEvent.click(screen.getByRole("button", { name: "Go Events" }));
    await waitFor(() => expectInspectorId(null));
  });

  it("B4 preserves a Network Company Inspector across a compatible Structure depth change", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/network?mode=structure&focusType=Company&focusId=tsmc&depth=1"]);

    await userEvent.click(screen.getByRole("button", { name: "TSMC Depth Two" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("depth=2"));
    expectInspectorId("nvidia");
  });

  it("B5 preserves an Impact target Inspector across a compatible max-hop change", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3"]);

    await userEvent.click(screen.getByRole("button", { name: "Event Impact Hop Two" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("maxHops=2"));
    expectInspectorId("nvidia");
  });

  it("B6 clears an incompatible Inspector when Network focus changes", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/network?mode=structure&focusType=Company&focusId=tsmc&depth=1"]);

    await userEvent.click(screen.getByRole("button", { name: "Samsung Focus" }));
    await waitFor(() => expectInspectorId(null));
  });

  it("B7 Browser Back clears a Company-profile Inspector that is invalid in the restored Network", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(
      ["/network?mode=structure&focusType=Company&focusId=tsmc&depth=1", "/companies/nvidia"],
      1,
    );

    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/network"));
    expectInspectorId(null);
  });

  it("B8 Browser Forward clears a restored Network Relationship Inspector in Company context", async () => {
    renderHarness(
      ["/network?mode=structure&focusType=Company&focusId=tsmc&depth=1", "/companies/nvidia"],
      1,
    );

    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/network"));
    setInspector({
      kind: "relationship",
      id: "rel-1",
      name: "SUPPLIES",
      context: { graphFocusId: "tsmc", graphDepth: 1, relationshipId: "rel-1" },
    });

    await userEvent.click(screen.getByRole("button", { name: "Forward" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/companies/nvidia"));
    expectInspectorId(null);
  });

  it("B9 direct Inspector-driven navigation is reconciled by the same route boundary", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/companies/nvidia"]);

    await userEvent.click(screen.getByRole("button", { name: "Inspector Action Events" }));
    await waitFor(() => expectInspectorId(null));
  });

  it("B10 existing explicit sidebar clear behavior remains functional", async () => {
    setInspector({ kind: "entity", id: "nvidia", entityType: "Company", name: "NVIDIA" });
    renderHarness(["/companies/nvidia"]);

    await userEvent.click(screen.getByRole("button", { name: "Sidebar Events" }));
    await waitFor(() => expectInspectorId(null));
  });
});
