import {
  BrainCircuit,
  Building2,
  ChartNoAxesCombined,
  LayoutDashboard,
  Network,
  RadioTower,
} from "lucide-react";

import "./PrimaryNavigation.css";

export type NavigationSection =
  | "overview"
  | "events"
  | "network"
  | "companies"
  | "risk"
  | "intelligence";

type PrimaryNavigationProps = {
  activeSection: NavigationSection;
  onSectionChange: (section: NavigationSection) => void;
};

const navigationItems = [
  {
    id: "overview",
    label: "Overview",
    icon: LayoutDashboard,
  },
  {
    id: "events",
    label: "Events",
    icon: RadioTower,
  },
  {
    id: "network",
    label: "Network",
    icon: Network,
  },
  {
    id: "companies",
    label: "Companies",
    icon: Building2,
  },
  {
    id: "risk",
    label: "Risk Analysis",
    icon: ChartNoAxesCombined,
  },
  {
    id: "intelligence",
    label: "Intelligence",
    icon: BrainCircuit,
  },
] satisfies Array<{
  id: NavigationSection;
  label: string;
  icon: typeof LayoutDashboard;
}>;

export function PrimaryNavigation({
  activeSection,
  onSectionChange,
}: PrimaryNavigationProps) {
  return (
    <nav className="primary-navigation" aria-label="Primary navigation">
      <div className="navigation-section-label">Workspace</div>

      <ul className="navigation-list">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <li key={item.id}>
              <button
                type="button"
                className={`navigation-item${isActive ? " is-active" : ""}`}
                aria-current={isActive ? "page" : undefined}
                onClick={() => onSectionChange(item.id)}
              >
                <span className="navigation-accent" aria-hidden="true" />

                <Icon
                  className="navigation-icon"
                  size={18}
                  strokeWidth={1.8}
                  aria-hidden="true"
                />

                <span className="navigation-label">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}