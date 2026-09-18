import { useCallback, useEffect, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import type { InspectorAction } from "./components/layout/EntityInspector";
import type { NavigationSection } from "./components/layout/PrimaryNavigation";
import type { InspectorContext } from "./data/inspectorDemo";
import { eventsDemo } from "./data/eventsDemo";
import { networkStructureDemoNodes } from "./data/networkStructureDemo";
import {
  DEFAULT_NETWORK_INVESTIGATION,
  type NetworkInvestigation,
  type Phase2HistoryState,
} from "./phase2";

import { OverviewPage } from "./pages/OverviewPage";
import { EventsPage } from "./pages/EventsPage";
import { NetworkPage } from "./pages/NetworkPage";
import { CompaniesPage } from "./pages/CompaniesPage";
import { RiskAnalysisPage } from "./pages/RiskAnalysisPage";
import { IntelligencePage } from "./pages/IntelligencePage";

import "./phase2.css";

function App() {
  const [activeSection, setActiveSection] = useState<NavigationSection>("overview");
  const [inspectorContext, setInspectorContext] = useState<InspectorContext | null>(null);
  const [selectedEventId, setSelectedEventId] = useState(eventsDemo[0].id);
  const [companyProfileId, setCompanyProfileId] = useState<string | null>(null);
  const [network, setNetwork] = useState<NetworkInvestigation>(DEFAULT_NETWORK_INVESTIGATION);

  const snapshot = useCallback(
    (): Phase2HistoryState => ({
      phase2: true,
      section: activeSection,
      companyProfileId,
      selectedEventId,
      network,
      inspector: inspectorContext,
    }),
    [activeSection, companyProfileId, inspectorContext, network, selectedEventId],
  );

  const applyHistoryState = useCallback((state: Phase2HistoryState) => {
    setActiveSection(state.section);
    setCompanyProfileId(state.companyProfileId);
    setSelectedEventId(state.selectedEventId);
    setNetwork(state.network);
    setInspectorContext(state.inspector);
  }, []);

  const routeFor = (state: Phase2HistoryState) => {
    if (state.section === "companies" && state.companyProfileId) {
      return `#/companies/${encodeURIComponent(state.companyProfileId)}`;
    }
    return `#/${state.section}`;
  };

  const pushNavigation = useCallback(
    (next: Phase2HistoryState) => {
      window.history.replaceState(snapshot(), "", window.location.hash || `#/${activeSection}`);
      window.history.pushState(next, "", routeFor(next));
      applyHistoryState(next);
    },
    [activeSection, applyHistoryState, snapshot],
  );

  useEffect(() => {
    const current = window.history.state as Phase2HistoryState | null;
    if (!current?.phase2) {
      window.history.replaceState(snapshot(), "", window.location.hash || "#/overview");
    }

    const onPopState = (event: PopStateEvent) => {
      const state = event.state as Phase2HistoryState | null;
      if (state?.phase2) applyHistoryState(state);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [applyHistoryState, snapshot]);

  const changeSection = (section: NavigationSection) => {
    if (section === activeSection) return;
    pushNavigation({ ...snapshot(), section });
  };

  const openEvent = (eventId: string) => {
    pushNavigation({ ...snapshot(), section: "events", selectedEventId: eventId });
  };

  const openCompanyProfile = (companyId: string) => {
    pushNavigation({ ...snapshot(), section: "companies", companyProfileId: companyId });
  };

  const openNetwork = (changes: Partial<NetworkInvestigation>) => {
    const nextNetwork: NetworkInvestigation = {
      ...network,
      ...changes,
      highlightedPath: changes.highlightedPath,
      selectedObjectId: changes.selectedObjectId,
    };
    pushNavigation({ ...snapshot(), section: "network", companyProfileId: null, network: nextNetwork });
  };

  const backFromCompanyProfile = () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    setCompanyProfileId(null);
  };

  const handleInspectorAction = (action: InspectorAction, context: InspectorContext) => {
    const focusType = context.type === "Relationship" ? undefined : context.type;

    if (action === "Open Profile" && context.type === "Company") {
      openCompanyProfile(context.id);
    } else if (action === "Open Event" && context.type === "Event") {
      openEvent(context.id);
    } else if (action === "Open Company" && context.relatedCompanyId) {
      openCompanyProfile(context.relatedCompanyId);
    } else if (action === "Explore Network" && focusType) {
      openNetwork({
        mode: "structure",
        focusId: context.id,
        focusName: context.name,
        focusType,
        eventId: undefined,
        selectedObjectId: undefined,
        highlightedPath: undefined,
      });
    } else if (action === "Open Impact" && focusType) {
      openNetwork({
        mode: "impact",
        focusId: context.id,
        focusName: context.name,
        focusType,
        eventId: context.type === "Event" ? context.id : undefined,
        selectedObjectId: undefined,
        highlightedPath: undefined,
      });
    } else if (action === "Highlight Path" && context.path) {
      openNetwork({ highlightedPath: context.path, selectedObjectId: context.id });
    }
  };

  const openImpact = (focus: { id: string; name: string; type: "Company" | "Event"; eventId?: string }) => {
    openNetwork({
      mode: "impact",
      focusId: focus.id,
      focusName: focus.name,
      focusType: focus.type,
      eventId: focus.eventId,
      selectedObjectId: undefined,
      highlightedPath: undefined,
    });
  };

  const showStructurePath = (path: string[]) => {
    const focusNode = networkStructureDemoNodes.find((node) => node.label === path[0]);
    openNetwork({
      mode: "structure",
      focusId: focusNode?.id,
      focusName: path[0],
      focusType: focusNode?.type ?? "Company",
      eventId: undefined,
      highlightedPath: path,
      selectedObjectId: undefined,
    });
  };

  return (
    <AppShell
      activeSection={activeSection}
      onSectionChange={changeSection}
      inspectorContext={inspectorContext}
      onInspect={setInspectorContext}
      onCloseInspector={() => setInspectorContext(null)}
      onInspectorAction={handleInspectorAction}
      connectionState="DISCONNECTED"
    >
      {activeSection === "overview" ? (
        <OverviewPage
          selectedInspectorId={inspectorContext?.id}
          onInspect={setInspectorContext}
          onOpenEvent={openEvent}
          onOpenCompanyProfile={openCompanyProfile}
          onOpenImpact={openImpact}
        />
      ) : activeSection === "events" ? (
        <EventsPage
          selectedEventId={selectedEventId}
          onSelectEvent={setSelectedEventId}
          onInspect={setInspectorContext}
          onOpenImpact={openImpact}
          onOpenCompanyProfile={openCompanyProfile}
        />
      ) : activeSection === "network" ? (
        <NetworkPage
          investigation={network}
          onInvestigationChange={setNetwork}
          onInspect={setInspectorContext}
          onClearInspector={() => setInspectorContext(null)}
          onOpenCompanyProfile={openCompanyProfile}
        />
      ) : activeSection === "companies" ? (
        <CompaniesPage
          profileCompanyId={companyProfileId}
          selectedInspectorId={inspectorContext?.id}
          onOpenProfile={openCompanyProfile}
          onBackFromProfile={backFromCompanyProfile}
          onInspect={setInspectorContext}
          onExploreNetwork={(company) =>
            openNetwork({
              mode: "structure",
              focusId: company.companyId,
              focusName: company.name,
              focusType: "Company",
              selectedObjectId: undefined,
              highlightedPath: undefined,
            })
          }
          onOpenImpact={(company) =>
            openImpact({ id: company.companyId, name: company.name, type: "Company" })
          }
        />
      ) : activeSection === "risk" ? (
        <RiskAnalysisPage
          selectedInspectorId={inspectorContext?.id}
          onInspect={setInspectorContext}
          onOpenProfile={openCompanyProfile}
          onOpenImpact={openImpact}
        />
      ) : activeSection === "intelligence" ? (
        <IntelligencePage
          onInspect={setInspectorContext}
          onShowNetwork={showStructurePath}
          onOpenImpact={openImpact}
        />
      ) : null}
    </AppShell>
  );
}

export default App;
