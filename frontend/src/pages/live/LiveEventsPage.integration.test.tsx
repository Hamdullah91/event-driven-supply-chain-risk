import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SupplyChainEvent } from "../../domain/types";
import { LiveEventsPage } from "./LiveEventsPage";

const { useEventsMock, useEventMock } = vi.hoisted(() => ({
  useEventsMock: vi.fn(),
  useEventMock: vi.fn(),
}));

vi.mock("../../query/hooks", () => ({
  useEvents: useEventsMock,
  useEvent: useEventMock,
}));

const event: SupplyChainEvent = {
  eventId: "event-visual-1",
  eventType: "FACILITY_OUTAGE",
  timestamp: "2026-09-08T16:27:40Z",
  severity: "unknown",
  confidence: 0.95,
  description: "TSMC temporarily shut down semiconductor production after earthquake disruption",
  source: "day37-integration-test",
  affectedEntities: [],
  evidence: {
    availability: "PARTIAL",
    source: "day37-integration-test",
  },
};

function renderEventsPage(path = "/events") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/events" element={<LiveEventsPage />} />
        <Route path="/events/:eventId" element={<LiveEventsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useEventsMock.mockReturnValue({
    data: { events: [event], count: 1, limit: 100, offset: 0 },
    isPending: false,
    isError: false,
    error: null,
  });
  useEventMock.mockReturnValue({
    data: event,
    isPending: false,
    isError: false,
    error: null,
  });
});

describe("Live Events page presentation contract", () => {
  it("renders both filters with explicit labels and the themed select hook", () => {
    renderEventsPage();

    expect(screen.getByLabelText("Type")).toHaveClass("events-filter-select");
    expect(screen.getByLabelText("Severity")).toHaveClass("events-filter-select");
    expect(screen.getByRole("region", { name: "Event controls" })).toBeInTheDocument();
    expect(document.querySelector(".events-page--live")).toBeInTheDocument();
  });

  it("renders the feed row with separate description and severity badge elements", () => {
    renderEventsPage();

    const row = screen.getByRole("button", { name: /FACILITY_OUTAGE/ });
    expect(row).toHaveClass("event-row");
    expect(within(row).getByText("UNKNOWN")).toHaveClass("event-severity-badge");
    expect(within(row).getByText(event.description!)).toBeInTheDocument();
  });

  it("renders event metadata in a four-cell detail grid", () => {
    renderEventsPage("/events/event-visual-1");

    const metadata = screen.getByRole("region", { name: "Event classification metadata" });
    expect(within(metadata).getByText("Severity")).toBeInTheDocument();
    expect(within(metadata).getByText("Classifier Confidence")).toBeInTheDocument();
    expect(within(metadata).getByText("95.0%")).toBeInTheDocument();
    expect(within(metadata).getByText("UNKNOWN")).toHaveClass("event-severity-badge");
    expect(metadata.querySelectorAll(":scope > div")).toHaveLength(4);
  });
});
