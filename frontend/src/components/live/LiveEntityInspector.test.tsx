import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ExposureContribution } from "../../domain/types";
import type { InspectorRef } from "../../state/uiStore";
import { LiveEntityInspector } from "./LiveEntityInspector";

const exposure: ExposureContribution = {
  exposureId: "exposure:evt-1:nvidia:1:tsmc>nvidia",
  eventId: "evt-1",
  eventType: "SUPPLY_DISRUPTION",
  severity: "high",
  sourceEntity: { id: "tsmc", type: "Company", name: "TSMC" },
  targetCompany: { id: "nvidia", type: "Company", name: "NVIDIA" },
  hop: 1,
  initialRisk: 0.75,
  combinedPathDependency: 0.8,
  distanceDecay: 1,
  propagatedRisk: 0.6,
  path: [{ id: "tsmc", type: "Company", name: "TSMC" }, { id: "nvidia", type: "Company", name: "NVIDIA" }],
  confidence: 0.91,
  source: "wire",
  evidence: { availability: "PARTIAL", source: "wire", eventId: "evt-1" },
};

vi.mock("../../query/hooks", () => ({
  useCompany: () => ({ data: undefined, isPending: false, isError: false }),
  useCompanyRisk: () => ({ data: undefined, isPending: false, isError: false }),
  useEvent: () => ({ data: undefined, isPending: false, isError: false }),
  useCompanyExposure: () => ({ data: [exposure], isPending: false, isError: false }),
  useCompanyNetwork: () => ({ data: undefined, isPending: false, isError: false }),
}));

describe("LiveEntityInspector exposure semantics", () => {
  it("keeps Exposure ID primary and linked Event ID separate", () => {
    const onAction = vi.fn();
    const reference: InspectorRef = {
      kind: "exposure",
      id: exposure.exposureId,
      name: "SUPPLY_DISRUPTION exposure",
      context: { relatedCompanyId: "nvidia", eventId: "evt-1" },
    };

    render(<LiveEntityInspector reference={reference} onClose={vi.fn()} onAction={onAction} />);

    expect(screen.getByText("Exposure")).toBeInTheDocument();
    expect(screen.getByText(exposure.exposureId)).toBeInTheDocument();
    expect(screen.getByText("Linked Event ID")).toBeInTheDocument();
    expect(screen.getByText("evt-1")).toBeInTheDocument();
    expect(screen.getByText("Propagated Risk")).toBeInTheDocument();
    expect(screen.getByText("0.600")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open Event" }));
    expect(onAction).toHaveBeenCalledWith("Open Event", reference);
  });
});
