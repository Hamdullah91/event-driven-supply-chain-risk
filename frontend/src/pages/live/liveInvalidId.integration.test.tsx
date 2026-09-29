import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useUiStore } from "../../state/uiStore";
import { LiveCompaniesPage } from "./LiveCompaniesPage";
import { LiveEventsPage } from "./LiveEventsPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderRoute(path: string, routePath: string, element: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={routePath} element={element} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  useUiStore.setState({
    inspectorRef: null,
    highlightedPathId: null,
    selectedGraphObjectId: null,
    newRiskNotification: null,
  });
});

describe("LIVE invalid-ID truthfulness", () => {
  it("shows an honest Company not-found state without substituting another company", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ detail: "Company 'missing-company' was not found." }, 404));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/companies/missing-company", "/companies/:companyId", <LiveCompaniesPage />);

    expect(await screen.findByText("Company profile not found")).toBeInTheDocument();
    expect(screen.getAllByText(/No other company is substituted for missing-company/).length).toBeGreaterThan(0);
    expect(screen.queryByText("TSMC")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it("shows an honest Event not-found state without substituting an unrelated Event", async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/events/missing-event")) {
        return Promise.resolve(jsonResponse({ detail: "Event 'missing-event' was not found." }, 404));
      }
      if (url.includes("/api/v1/events")) {
        return Promise.resolve(jsonResponse({ events: [], count: 0, limit: 100, offset: 0 }));
      }
      return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/events/missing-event", "/events/:eventId", <LiveEventsPage />);

    expect(await screen.findByText(/Event not found:/)).toHaveTextContent("No unrelated Event is substituted");
    expect(screen.queryByText("FACILITY_OUTAGE")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });
});
