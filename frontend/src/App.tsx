import { useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import type { NavigationSection } from "./components/layout/PrimaryNavigation";

import { OverviewPage } from "./pages/OverviewPage";
import { EventsPage } from "./pages/EventsPage";
import { NetworkPage } from "./pages/NetworkPage";
import { CompaniesPage } from "./pages/CompaniesPage";
import { RiskAnalysisPage } from "./pages/RiskAnalysisPage";
import { IntelligencePage } from "./pages/IntelligencePage";


function App() {
  const [activeSection, setActiveSection] =
    useState<NavigationSection>("overview");

  return (
    <AppShell
      activeSection={activeSection}
      onSectionChange={setActiveSection}
    >
      {activeSection === "overview" ? (
        <OverviewPage />
      ) : activeSection === "events" ? (
        <EventsPage />
      ) : activeSection === "network" ? (
        <NetworkPage />
      ) : activeSection === "companies" ? (
        <CompaniesPage />
      ) : activeSection === "risk" ? (
        <RiskAnalysisPage />
      ) : activeSection === "intelligence" ? (
        <IntelligencePage />
      ) : null}
    </AppShell>
  );
}

export default App;