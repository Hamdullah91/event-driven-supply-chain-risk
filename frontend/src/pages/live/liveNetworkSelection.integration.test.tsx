import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useUiStore } from "../../state/uiStore";
import { LiveNetworkPage } from "./LiveNetworkPage";

const { useEventImpactMock } = vi.hoisted(() => ({
  useEventImpactMock: vi.fn(),
}));

vi.mock("../../query/hooks", () => ({
  useEntitySearch: () => ({ data: [], isPending: false, isError: false }),
  useCompanyNetwork: () => ({ data: undefined, isPending: false, isError: false }),
  useCompanyImpact: () => ({ data: undefined, isPending: false, isError: false }),
  useEventImpact: useEventImpactMock,
  useCompany: () => ({ data: undefined, isPending: false, isError: false }),
  useEvent: () => ({ data: { eventType: "FACILITY_OUTAGE" }, isPending: false, isError: false }),
}));

function eventImpact(maxHops: number, targetId: "nvidia" | "amd" = "nvidia") {
  const target = targetId === "nvidia"
    ? { id: "nvidia", name: "NVIDIA", hop: 1, risk: 0.6 }
    : { id: "amd", name: "AMD", hop: 2, risk: 0.378 };
  const pathId = `path-${target.id}`;
  const nodes = target.hop === 1
    ? [
        { id: "tsmc", type: "Company", name: "TSMC" },
        { id: target.id, type: "Company", name: target.name },
      ]
    : [
        { id: "tsmc", type: "Company", name: "TSMC" },
        { id: "nvidia", type: "Company", name: "NVIDIA" },
        { id: target.id, type: "Company", name: target.name },
      ];
  const included = target.hop <= maxHops;

  return {
    origin: { kind: "Event", id: "evt-1", name: "FACILITY_OUTAGE" },
    maxHops,
    metricType: "PROPAGATED_RISK",
    targets: included
      ? [{
          company: { id: target.id, type: "Company", name: target.name },
          hop: target.hop,
          riskLevel: target.hop === 1 ? "HIGH" : "MEDIUM",
          propagatedRisk: target.risk,
          pathId,
        }]
      : [],
    paths: included
      ? [{
          pathId,
          nodes,
          trace: {
            hop: target.hop,
            initialRisk: 0.75,
            combinedPathDependency: target.hop === 1 ? 0.8 : 0.72,
            distanceDecay: target.hop === 1 ? 1 : 0.7,
            propagatedRisk: target.risk,
          },
        }]
      : [],
  };
}

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

beforeEach(() => {
  useEventImpactMock.mockImplementation((_eventId: string | undefined, maxHops: number) => ({
    data: eventImpact(maxHops, "nvidia"),
    isPending: false,
    isError: false,
  }));
});

afterEach(() => {
  resetStore();
  vi.clearAllMocks();
});

describe("LIVE Impact URL selection", () => {
  it("restores target, path, and Inspector after a hard-load style mount", async () => {
    render(
      <MemoryRouter initialEntries={["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3&targetId=nvidia&pathId=path-nvidia"]}>
        <LiveNetworkPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(useUiStore.getState().inspectorRef?.id).toBe("nvidia"));
    expect(useUiStore.getState().selectedGraphObjectId).toBe("nvidia");
    expect(useUiStore.getState().highlightedPathId).toBe("path-nvidia");
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
    expect(screen.getByTestId("location-search")).toHaveTextContent("pathId=path-nvidia");
  });

  it("preserves a selected target and Inspector when it remains inside the new max-hop limit", async () => {
    render(
      <MemoryRouter initialEntries={["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3&targetId=nvidia&pathId=path-nvidia"]}>
        <LiveNetworkPage />
        <LocationProbe />
      </MemoryRouter>,
    );

    await waitFor(() => expect(useUiStore.getState().inspectorRef?.id).toBe("nvidia"));

    fireEvent.click(screen.getByRole("button", { name: "2" }));

    await waitFor(() => expect(screen.getByTestId("location-search")).toHaveTextContent("maxHops=2"));
    expect(screen.getByTestId("location-search")).toHaveTextContent("targetId=nvidia");
    expect(screen.getByTestId("location-search")).toHaveTextContent("pathId=path-nvidia");
    expect(useUiStore.getState().inspectorRef?.id).toBe("nvidia");
    expect(useUiStore.getState().selectedGraphObjectId).toBe("nvidia");
    expect(useUiStore.getState().highlightedPathId).toBe("path-nvidia");
  });

  it("clears the selected target and Inspector only when the new result no longer contains it", async () => {
    useEventImpactMock.mockImplementation((_eventId: string | undefined, maxHops: number) => ({
      data: eventImpact(maxHops, "amd"),
      isPending: false,
      isError: false,
    }));

    render(
      <MemoryRouter initialEntries={["/network?mode=impact&focusType=Event&focusId=evt-1&eventId=evt-1&maxHops=3&targetId=amd&pathId=path-amd"]}>
        <LiveNetworkPage />
        <LocationProbe />
      </MemoryRouter>,
    );

    await waitFor(() => expect(useUiStore.getState().inspectorRef?.id).toBe("amd"));

    fireEvent.click(screen.getByRole("button", { name: "1" }));

    await waitFor(() => expect(screen.getByTestId("location-search")).toHaveTextContent("maxHops=1"));
    await waitFor(() => expect(screen.getByTestId("location-search")).not.toHaveTextContent("targetId=amd"));
    expect(screen.getByTestId("location-search")).not.toHaveTextContent("pathId=path-amd");
    expect(useUiStore.getState().inspectorRef).toBeNull();
    expect(useUiStore.getState().selectedGraphObjectId).toBeNull();
    expect(useUiStore.getState().highlightedPathId).toBeNull();
  });
});
