import { useMemo, useState, type ReactNode } from "react";
import { Search, X } from "lucide-react";

import { EntityInspector, type InspectorAction } from "./EntityInspector";
import { PrimaryNavigation, type NavigationSection } from "./PrimaryNavigation";
import type { InspectorContext } from "../../data/inspectorDemo";
import { searchDemoResults } from "../../data/searchDemo";

import "./AppShell.css";

type ConnectionState = "CONNECTING" | "CONNECTED" | "RECONNECTING" | "DISCONNECTED" | "ERROR";

type AppShellProps = {
  children: ReactNode;
  activeSection: NavigationSection;
  onSectionChange: (section: NavigationSection) => void;
  inspectorContext: InspectorContext | null;
  onInspect: (context: InspectorContext) => void;
  onCloseInspector: () => void;
  onInspectorAction: (action: InspectorAction, context: InspectorContext) => void;
  connectionState: ConnectionState;
};

const sectionTitles: Record<NavigationSection, string> = {
  overview: "Overview",
  events: "Events",
  network: "Network",
  companies: "Companies",
  risk: "Risk Analysis",
  intelligence: "Intelligence",
};

export function AppShell({
  children,
  activeSection,
  onSectionChange,
  inspectorContext,
  onInspect,
  onCloseInspector,
  onInspectorAction,
  connectionState,
}: AppShellProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);

  const filteredResults = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return searchDemoResults;
    return searchDemoResults.filter((result) =>
      `${result.label} ${result.type} ${result.secondary}`.toLowerCase().includes(query),
    );
  }, [searchQuery]);

  const selectSearchResult = (context: InspectorContext) => {
    onInspect(context);
    setSearchOpen(false);
  };

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">SC</div>
          <div className="brand-copy">
            <span className="brand-title">Supply Chain</span>
            <span className="brand-subtitle">Risk Intelligence</span>
          </div>
        </div>

        <PrimaryNavigation activeSection={activeSection} onSectionChange={onSectionChange} />

        <div className="sidebar-system">
          <span className="system-indicator" aria-hidden="true" />
          <div>
            <div className="system-label">Application</div>
            <div className="system-value">Frontend active</div>
          </div>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <div className="topbar-page-context">
            <span className="topbar-eyebrow">Command Center</span>
            <span className="topbar-title">{sectionTitles[activeSection]}</span>
          </div>

          <div className="topbar-actions">
            <div className="global-search">
              <Search size={15} aria-hidden="true" />
              <input
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setSearchOpen(true);
                }}
                onFocus={() => setSearchOpen(true)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") setSearchOpen(false);
                }}
                placeholder="Search companies, facilities, materials, events..."
                aria-label="Global entity search development fixture"
                aria-expanded={searchOpen}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="global-search-clear"
                  aria-label="Clear global search"
                  onClick={() => setSearchQuery("")}
                >
                  <X size={14} />
                </button>
              )}

              {searchOpen && (
                <div className="global-search-results" role="listbox" aria-label="Global search results">
                  <div className="global-search-fixture-label">DEVELOPMENT SEARCH FIXTURE</div>
                  {filteredResults.length > 0 ? (
                    filteredResults.map((result) => (
                      <button
                        type="button"
                        key={result.id}
                        className="global-search-result"
                        onClick={() => selectSearchResult(result.context)}
                      >
                        <span>
                          <strong>{result.label}</strong>
                          <small>{result.secondary}</small>
                        </span>
                        <em>{result.type}</em>
                      </button>
                    ))
                  ) : (
                    <div className="global-search-empty">No development results match this search.</div>
                  )}
                </div>
              )}
            </div>

            <div className="topbar-status" title="WebSocket adapter is not connected in the Phase 2 fixture">
              <span className="status-label">WS</span>
              <span className="status-value">{connectionState}</span>
            </div>
          </div>
        </header>

        <main className={`app-workspace${inspectorContext ? "" : " app-workspace--no-inspector"}`}>
          <div className="workspace-content">{children}</div>
          {inspectorContext && (
            <EntityInspector
              context={inspectorContext}
              onClose={onCloseInspector}
              onAction={onInspectorAction}
            />
          )}
        </main>
      </div>
    </div>
  );
}
