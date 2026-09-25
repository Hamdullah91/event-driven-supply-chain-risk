import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import type { NavigationSection } from "../components/layout/PrimaryNavigation";
import { LiveAppShell, type LiveInspectorAction } from "../components/live/LiveAppShell";
import { LiveCompaniesPage } from "../pages/live/LiveCompaniesPage";
import { LiveEventsPage } from "../pages/live/LiveEventsPage";
import { LiveNetworkPage } from "../pages/live/LiveNetworkPage";
import { LiveUnavailablePage } from "../pages/live/LiveUnavailablePage";
import { useUiStore, type InspectorRef } from "../state/uiStore";

function sectionFromPath(pathname: string): NavigationSection {
  if (pathname.startsWith("/events")) return "events";
  if (pathname.startsWith("/network")) return "network";
  if (pathname.startsWith("/companies")) return "companies";
  if (pathname.startsWith("/risk-analysis")) return "risk";
  if (pathname.startsWith("/intelligence")) return "intelligence";
  return "overview";
}

const sectionRoutes: Record<NavigationSection, string> = { overview: "/overview", events: "/events", network: "/network", companies: "/companies", risk: "/risk-analysis", intelligence: "/intelligence" };

export function LiveApp() {
  const navigate = useNavigate();
  const location = useLocation();
  const inspectorRef = useUiStore((state) => state.inspectorRef);
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);

  const onSectionChange = (section: NavigationSection) => { if (section !== sectionFromPath(location.pathname)) navigate(sectionRoutes[section]); };
  const inspectorAction = (action: LiveInspectorAction, ref: InspectorRef) => {
    if (action === "Open Profile" && ref.entityType === "Company") navigate(`/companies/${encodeURIComponent(ref.id)}`);
    else if (action === "Open Event" && ref.entityType === "Event") navigate(`/events/${encodeURIComponent(ref.id)}`);
    else if (action === "Open Company" && ref.context?.relatedCompanyId) navigate(`/companies/${encodeURIComponent(ref.context.relatedCompanyId)}`);
    else if (action === "Explore Network" && ref.entityType === "Company") navigate(`/network?mode=structure&focusType=Company&focusId=${encodeURIComponent(ref.id)}&depth=1`);
    else if (action === "Open Impact" && ref.entityType === "Company") navigate(`/network?mode=impact&focusType=Company&focusId=${encodeURIComponent(ref.id)}&maxHops=3`);
    else if (action === "Open Impact" && ref.entityType === "Event") navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(ref.id)}&eventId=${encodeURIComponent(ref.id)}&maxHops=3`);
  };

  return <LiveAppShell activeSection={sectionFromPath(location.pathname)} onSectionChange={onSectionChange} inspectorRef={inspectorRef} onInspect={setInspectorRef} onCloseInspector={() => setInspectorRef(null)} onInspectorAction={inspectorAction}><Routes>
    <Route path="/overview" element={<LiveUnavailablePage title="Overview" description="Live Overview aggregation is being integrated from verified backend contracts; unsupported system-wide metrics are not replaced with demo values." />} />
    <Route path="/events" element={<LiveEventsPage />} /><Route path="/events/:eventId" element={<LiveEventsPage />} />
    <Route path="/network" element={<LiveNetworkPage />} />
    <Route path="/companies" element={<LiveCompaniesPage />} /><Route path="/companies/:companyId" element={<LiveCompaniesPage />} />
    <Route path="/risk-analysis" element={<LiveUnavailablePage title="Risk Analysis" description="No system-wide risk ranking is fabricated while the backend lacks a dedicated aggregate contract." />} />
    <Route path="/intelligence" element={<LiveUnavailablePage title="Intelligence" description="The public Agent API will be integrated without exposing hidden reasoning." />} />
    <Route path="/" element={<Navigate to="/overview" replace />} /><Route path="*" element={<Navigate to="/overview" replace />} />
  </Routes></LiveAppShell>;
}
