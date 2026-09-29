import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useUiStore } from "../../state/uiStore";
import { LiveNetworkPage } from "./LiveNetworkPage";

vi.mock("../../query/hooks", () => ({
  useEntitySearch: () => ({ data: [], isPending: false, isError: false }),
  useCompanyNetwork: () => ({ data: undefined, isPending: false, isError: false }),
  useCompanyImpact: () => ({ data: undefined, isPending: false, isError: false }),
  useEventImpact: () => ({
    data: {
      origin: { kind: "Event", id: "evt-1", name: "FACILITY_OUTAGE" },
      maxHops: 3,
      metricType: "PROPAGATED_RISK",
      targets: [{
        company: { id: "nvidia", type: "Company", name: "NVIDIA" },
        hop: 1,
        riskLevel: "HIGH",
        propagatedRisk: 0.6,
        pathId: "path-1",
      }],
      paths: [{
        pathId: "path-1",
        nodes: [{ id: "tsmc", type: "Company", name: "TSMC" }, { id: "nvidia", type: "Company", name: "NVIDIA" }],
        trace: { hop: 1, initialRisk: 0.75, combinedPathDependency: 0.8, distanceDecay: 1, propagatedRisk: 0.6 },
      }],
    },
    isPending: false,
    isError: false,
  }),
  useCompany: () => ({ data: undefined, isPending: false, isError: false }),
  useEvent: () => ({ data: { eventType: "FACILITY_OUTAGE" }, isPending: false, isError: false }),
}));

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location-search">{location.search}</output>;
}

function resetStore() {
  useUiStore.setState({
    inspectorRef: null,
    highlightedPathId: null,
    selectedGraphObjectId: null,
    newRiskNotification: null,
  });
}

afterEach(resetStore);

describe("LIVE Impact URL selection", () => {
  it("restores target, path, and Inspector after a hard-load style mount", async () => {
    render(
      <MemoryRouter initialEntries={["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3&targetId=nvidia&pathId=path-1"]}>
        <LiveNetworkPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(useUiStore.getState().inspectorRef?.id).toBe("nvidia"));
    expect(useUiStore.getState().selectedGraphObjectId).toBe("nvidia");
    expect(useUiStore.getState().highlightedPathId).toBe("path-1");
    expect(screen.getByText("TSMC → NVIDIA")).toBeInTheDocument();
  });

  it("writes a selected target and path into navigable URL state", async () => {
    render(
      <MemoryRouter initialEntries={["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3"]}>
        <LiveNetworkPage />
        <LocationProbe />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /NVIDIA/ }));

    await waitFor(() => expect(screen.getByTestId("location-search")).toHaveTextContent("targetId=nvidia"));
    expect(screen.getByTestId("location-search")).toHaveTextContent("pathId=path-1");
  });
});
