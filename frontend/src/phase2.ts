import type { NavigationSection } from "./components/layout/PrimaryNavigation";
import type { InspectorContext } from "./data/inspectorDemo";

/**
 * Temporary Phase 2 interaction state used to demonstrate the frozen UX behavior.
 * Phase 3 owns the canonical frontend data/state architecture and may replace this.
 */
export type NetworkMode = "structure" | "impact";
export type NetworkFocusType = "Company" | "Event" | "Facility" | "Material" | "Product" | "Technology" | "Industry" | "Location" | "Country";
export type HopDepth = 1 | 2 | 3;

export type NetworkInvestigation = {
  mode: NetworkMode;
  maxHops: HopDepth;
  focusId?: string;
  focusName?: string;
  focusType?: NetworkFocusType;
  eventId?: string;
  selectedObjectId?: string;
  highlightedPath?: string[];
  hopOnly?: HopDepth | null;
};

export type Phase2HistoryState = {
  phase2: true;
  section: NavigationSection;
  companyProfileId: string | null;
  selectedEventId: string;
  network: NetworkInvestigation;
  inspector: InspectorContext | null;
};

export const DEFAULT_NETWORK_INVESTIGATION: NetworkInvestigation = {
  mode: "structure",
  maxHops: 1,
  hopOnly: null,
};
