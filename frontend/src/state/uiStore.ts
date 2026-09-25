import { create } from "zustand";
import type { EntityType } from "../domain/types";

export type InspectorRef = {
  kind: "entity" | "relationship" | "event" | "risk";
  id: string;
  entityType?: EntityType;
  name?: string;
  context?: { relatedCompanyId?: string; graphFocusId?: string; relationshipId?: string };
};

type RiskNotification = { companyId: string; eventId?: string; timestamp: string };

type UiState = {
  inspectorRef: InspectorRef | null;
  highlightedPathId: string | null;
  selectedGraphObjectId: string | null;
  newRiskNotification: RiskNotification | null;
  setInspectorRef: (value: InspectorRef | null) => void;
  setHighlightedPathId: (value: string | null) => void;
  setSelectedGraphObjectId: (value: string | null) => void;
  setNewRiskNotification: (value: RiskNotification | null) => void;
  clearSelection: () => void;
};

export const useUiStore = create<UiState>((set) => ({
  inspectorRef: null,
  highlightedPathId: null,
  selectedGraphObjectId: null,
  newRiskNotification: null,
  setInspectorRef: (inspectorRef) => set({ inspectorRef }),
  setHighlightedPathId: (highlightedPathId) => set({ highlightedPathId }),
  setSelectedGraphObjectId: (selectedGraphObjectId) => set({ selectedGraphObjectId }),
  setNewRiskNotification: (newRiskNotification) => set({ newRiskNotification }),
  clearSelection: () => set({ inspectorRef: null, highlightedPathId: null, selectedGraphObjectId: null }),
}));
