import { useEffect, useState, type ReactNode } from "react";
import { Search, X } from "lucide-react";

import { useEntitySearch, useDetailedHealth } from "../../query/hooks";
import type { SearchResult } from "../../domain/types";
import type { InspectorRef } from "../../state/uiStore";
import { PrimaryNavigation, type NavigationSection } from "../layout/PrimaryNavigation";
import { LiveEntityInspector } from "./LiveEntityInspector";

import "../layout/AppShell.css";

export type LiveInspectorAction = "Open Profile" | "Explore Network" | "Open Impact" | "Open Event" | "Open Company";

type Props = {
  children: ReactNode;
  activeSection: NavigationSection;
  onSectionChange: (section: NavigationSection) => void;
  inspectorRef: InspectorRef | null;
  onInspect: (ref: InspectorRef) => void;
  onCloseInspector: () => void;
  onInspectorAction: (action: LiveInspectorAction, ref: InspectorRef) => void;
};

const sectionTitles: Record<NavigationSection, string> = {
  overview: "Overview",
  events: "Events",
  network: "Network",
  companies: "Companies",
  risk: "Risk Analysis",
  intelligence: "Intelligence",
};

function toInspectorRef(result: SearchResult): InspectorRef {
  return {
    kind: result.entity.type === "Event" ? "event" : "entity",
    id: result.entity.id,
    entityType: result.entity.type,
    name: result.entity.name,
  };
}

export function LiveAppShell({ children, activeSection, onSectionChange, inspectorRef, onInspect, onCloseInspector, onInspectorAction }: Props) {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const search = useEntitySearch(debouncedQuery, 25);
  const health = useDetailedHealth();

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(searchQuery.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  const selectSearchResult = (result: SearchResult) => {
    onInspect(toInspectorRef(result));
    setSearchOpen(false);
  };

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand"><div className="brand-mark" aria-hidden="true">SC</div><div className="brand-copy"><span className="brand-title">Supply Chain</span><span className="brand-subtitle">Risk Intelligence</span></div></div>
        <PrimaryNavigation activeSection={activeSection} onSectionChange={onSectionChange} />
        <div className="sidebar-system">
          <span className="system-indicator" aria-hidden="true" />
          <div><div className="system-label">Backend</div><div className="system-value">{health.isPending ? "Checking" : health.isError ? "Unavailable" : health.data?.status ?? "Unknown"}</div></div>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <div className="topbar-page-context"><span className="topbar-eyebrow">Command Center</span><span className="topbar-title">{sectionTitles[activeSection]}</span></div>
          <div className="topbar-actions">
            <div className="global-search">
              <Search size={15} aria-hidden="true" />
              <input
                value={searchQuery}
                onChange={(event) => { setSearchQuery(event.target.value); setSearchOpen(true); }}
                onFocus={() => setSearchOpen(true)}
                onKeyDown={(event) => { if (event.key === "Escape") setSearchOpen(false); }}
                placeholder="Search companies, facilities, materials, events..."
                aria-label="Global entity search"
                aria-expanded={searchOpen}
              />
              {searchQuery && <button type="button" className="global-search-clear" aria-label="Clear global search" onClick={() => { setSearchQuery(""); setDebouncedQuery(""); }}><X size={14} /></button>}
              {searchOpen && searchQuery.trim().length >= 2 && (
                <div className="global-search-results" aria-label="Global search results">
                  <div className="global-search-fixture-label">LIVE GRAPH SEARCH</div>
                  {search.isPending ? <div className="global-search-empty">Searching…</div>
                    : search.isError ? <div className="global-search-empty">Search unavailable. No demo results substituted.</div>
                    : (search.data?.length ?? 0) > 0 ? search.data!.map((result) => (
                      <button type="button" key={`${result.entity.type}:${result.entity.id}`} className="global-search-result" onClick={() => selectSearchResult(result)}>
                        <span><strong>{result.entity.name}</strong><small>{result.entity.id}</small></span><em>{result.entity.type}</em>
                      </button>
                    )) : <div className="global-search-empty">No matching live entities.</div>}
                </div>
              )}
            </div>
            <div className="topbar-status" title="WebSocket integration is isolated from HTTP server state"><span className="status-label">DATA</span><span className="status-value">LIVE</span></div>
          </div>
        </header>

        <main className={`app-workspace${inspectorRef ? "" : " app-workspace--no-inspector"}`}>
          <div className="workspace-content">{children}</div>
          {inspectorRef && <LiveEntityInspector reference={inspectorRef} onClose={onCloseInspector} onAction={onInspectorAction} />}
        </main>
      </div>
    </div>
  );
}
