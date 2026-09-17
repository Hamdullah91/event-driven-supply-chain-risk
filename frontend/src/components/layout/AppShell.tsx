import type { ReactNode } from "react";
import { EntityInspector } from "./EntityInspector";
import { defaultInspectorContext } from "../../data/inspectorDemo";

import {
  PrimaryNavigation,
  type NavigationSection,
} from "./PrimaryNavigation";

import "./AppShell.css";

type AppShellProps = {
  children: ReactNode;
  activeSection: NavigationSection;
  onSectionChange: (section: NavigationSection) => void;
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
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">
            SC
          </div>

          <div className="brand-copy">
            <span className="brand-title">Supply Chain</span>
            <span className="brand-subtitle">Risk Intelligence</span>
          </div>
        </div>

        <PrimaryNavigation
          activeSection={activeSection}
          onSectionChange={onSectionChange}
        />

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
            <span className="topbar-title">
              {sectionTitles[activeSection]}
            </span>
          </div>

          <div className="topbar-actions">
            <div
              className="search-reserved"
              aria-label="Global search reserved"
            >
              Global search
              <span>Reserved</span>
            </div>

            <div className="topbar-status">
              <span className="status-label">UI</span>
              <span className="status-value">Ready</span>
            </div>
          </div>
        </header>

        <main className="app-workspace">
          <div className="workspace-content">{children}</div>

          <EntityInspector context={defaultInspectorContext} />
        </main>
      </div>
    </div>
  );
}