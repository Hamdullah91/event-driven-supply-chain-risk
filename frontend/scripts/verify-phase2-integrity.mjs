import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(fileURLToPath(new URL(path, root)), "utf8");

const impactData = read("src/data/networkImpactDemo.ts");
const structureData = read("src/data/networkStructureDemo.ts");
const companyData = read("src/data/companiesDemo.ts");
const eventData = read("src/data/eventsDemo.ts");
const companiesPage = read("src/pages/CompaniesPage.tsx");
const eventsPage = read("src/pages/EventsPage.tsx");
const intelligencePage = read("src/pages/IntelligencePage.tsx");
const networkPage = read("src/pages/NetworkPage.tsx");
const networkCss = read("src/pages/NetworkPhase2.css");
const phase2State = read("src/phase2.ts");
const app = read("src/app/DemoApp.tsx");
const appShell = read("src/components/layout/AppShell.tsx");
const appShellCss = read("src/components/layout/AppShell.css");
const inspector = read("src/components/layout/EntityInspector.tsx");
const inspectorCss = read("src/components/layout/EntityInspector.css");

const checks = [
  ["unsupported Company Profile IDs render an explicit unavailable state", () => {
    assert.match(companyData, /companyProfilesById/);
    assert.match(companyData, /getCompanyProfile/);
    assert.match(companiesPage, /Profile unavailable for this development entity/);
    assert.match(companiesPage, /if \(props\.profileCompanyId\)[\s\S]*?getCompanyProfile\(props\.profileCompanyId\)[\s\S]*?CompanyProfileUnavailable/);
  }],
  ["unsupported Impact targets do not expose a false Open Profile action", () => {
    assert.match(inspector, /hasCompanyProfile\(context\.id\)/);
    assert.match(networkPage, /Profile unavailable for this development entity\./);
    assert.match(networkPage, /selectedProfileId && hasCompanyProfile\(selectedProfileId\)/);
  }],
  ["Samsung Structure focus cannot resolve to a TSMC fixture", () => {
    assert.match(structureData, /"demo-samsung"/);
    assert.match(structureData, /structureFixturesByFocusId/);
    assert.doesNotMatch(structureData, /"demo-samsung": tsmcFixture/);
    assert.match(networkPage, /No development network fixture is available for/);
    assert.match(networkPage, /No TSMC or other topology is substituted/);
  }],
  ["Structure fixture lookup has no unrelated default fallback", () => {
    assert.match(structureData, /return structureFixturesByFocusId\[focusId\]/);
    assert.doesNotMatch(structureData, /\?\?\s*tsmcFixture/);
    assert.doesNotMatch(structureData, /networkStructureDemoNodes/);
    assert.doesNotMatch(networkPage, /find\(\(node\) => node\.label === "TSMC"\)!/);
  }],
  ["Structure to Impact mode switching preserves full focus identity", () => {
    assert.match(networkPage, /const setMode = \(mode:[\s\S]*?\.\.\.investigation,[\s\S]*?mode,/);
    assert.doesNotMatch(networkPage, /const setMode[\s\S]*?focusId:\s*.*TSMC/);
  }],
  ["NVIDIA and ASML unsupported Impact origins cannot become TSMC", () => {
    assert.match(structureData, /"demo-nvidia": nvidiaFixture/);
    assert.match(structureData, /"demo-asml": asmlFixture/);
    assert.doesNotMatch(impactData, /"Company:demo-nvidia"/);
    assert.doesNotMatch(impactData, /"Company:demo-asml"/);
    assert.match(networkPage, /The current origin is preserved\. No TSMC path or other origin is substituted\./);
  }],
  ["returning from unavailable Impact keeps the original Structure focus", () => {
    assert.match(networkPage, /onReturnToStructure=\{\(\) => setMode\("structure"\)\}/);
    assert.match(networkPage, /onClick=\{onReturnToStructure\}>Return to Structure/);
    assert.doesNotMatch(networkPage, /normalize.*TSMC/i);
  }],
  ["supported TSMC Structure and Impact fixtures remain explicit", () => {
    assert.match(structureData, /"demo-tsmc": tsmcFixture/);
    assert.match(impactData, /"Company:demo-tsmc": companyTsmcFixture/);
    assert.doesNotMatch(impactData, /networkImpactDemo/);
  }],
  ["Network Focus Search remains interactive and uses stable IDs", () => {
    assert.match(networkPage, /aria-label="Focus Network"/);
    assert.match(networkPage, /selectFocus\(node\)/);
    assert.match(networkPage, /networkFocusEntities/);
    assert.match(structureData, /id: "demo-nvidia"/);
    assert.doesNotMatch(structureData, /id: "demo-company-nvidia"/);
  }],
  ["Reset preserves focus while resetting depth filters selection and path", () => {
    assert.match(networkPage, /const reset = \(\) => \{[\s\S]*?\.\.\.investigation,[\s\S]*?maxHops: 1,[\s\S]*?selectedObjectId: undefined,[\s\S]*?highlightedPath: undefined/);
    assert.doesNotMatch(networkPage, /const reset[\s\S]*?focusId:\s*"demo-tsmc"/);
  }],
  ["Intelligence Show Network still replaces stale focus identity", () => {
    assert.match(app, /const focusNode = networkFocusEntities\.find/);
    assert.match(app, /focusId: focusNode\?\.id/);
    assert.match(app, /focusName: path\[0\]/);
  }],
  ["unsupported and missing Impact origins remain distinct honest states", () => {
    assert.match(networkPage, /Select an event or origin company to analyze propagation\./);
    assert.match(networkPage, /Impact data is not available for/);
    assert.match(networkPage, /does not render risk rings or paths without a valid origin context/);
  }],
  ["company exposure fixtures remain isolated", () => {
    assert.match(companyData, /companyExposuresById/);
    assert.match(companyData, /"demo-nvidia": demoNvidiaExposures/);
    assert.doesNotMatch(companiesPage, /demoNvidiaExposures\.slice/);
    assert.match(companiesPage, /Detailed development exposure paths are unavailable for this company\./);
  }],
  ["Inspector primary actions remain near the identity and above scrollable analysis", () => {
    const identityIndex = inspector.indexOf("inspector-identity");
    const actionsIndex = inspector.indexOf("inspector-actions");
    const scrollIndex = inspector.indexOf("entity-inspector-scroll");
    assert.ok(identityIndex >= 0 && actionsIndex > identityIndex && scrollIndex > actionsIndex);
    assert.match(inspectorCss, /\.entity-inspector-scroll[\s\S]*?overflow-y: auto/);
    assert.doesNotMatch(inspectorCss, /\.inspector-actions[\s\S]*?margin-top: auto/);
  }],
  ["1024px Inspector reserves workspace instead of overlaying Network", () => {
    assert.match(appShellCss, /@media \(max-width: 1024px\)[\s\S]*?\.app-workspace \{[\s\S]*?display: grid;[\s\S]*?grid-template-columns: minmax\(0, 1fr\) clamp\(280px, 31vw, 320px\);/);
    assert.match(appShellCss, /@media \(max-width: 1024px\)[\s\S]*?\.entity-inspector \{[\s\S]*?position: sticky;[\s\S]*?height: calc\(100vh - var\(--topbar-height\)\);/);
    assert.match(appShellCss, /@media \(max-width: 760px\)[\s\S]*?\.entity-inspector \{[\s\S]*?position: fixed;/);
  }],
  ["Intelligence cannot submit a trimmed-empty question", () => {
    assert.match(intelligencePage, /const canSubmit = question\.trim\(\)\.length > 0 && !preparing;/);
    assert.match(intelligencePage, /const submit = \(\) => \{[\s\S]*?if \(!canSubmit\) return;/);
    assert.match(intelligencePage, /onSubmit=\{\(event\) => \{ event\.preventDefault\(\); if \(canSubmit\) submit\(\); \}\}/);
    assert.match(intelligencePage, /disabled=\{!canSubmit\}/);
    assert.match(intelligencePage, /aria-disabled=\{!canSubmit\}/);
  }],
  ["Impact NONE filter cannot behave like All", () => {
    assert.match(networkPage, /riskFilter === "NONE"[\s\S]*?\? false/);
    assert.match(networkPage, /visibleCompanies\.length === 0/);
    assert.match(networkPage, /No impact results match the current risk \/ exposure filter\./);
  }],
  ["focused graph prototype uses deterministic layout without the old canvas help card", () => {
    assert.match(structureData, /nodesFromLayout/);
    assert.match(networkPage, /source\.x \+ target\.x/);
    assert.match(networkCss, /\.graph-node\.is-focus/);
    assert.doesNotMatch(networkPage, /network-canvas-notice/);
  }],
  ["dead graph controls and incorrect listbox semantics are not reintroduced", () => {
    assert.doesNotMatch(networkPage, /aria-label="Center graph"/);
    assert.doesNotMatch(networkPage, /aria-label="Expand graph canvas"/);
    assert.doesNotMatch(appShell, /role="listbox"/);
    assert.match(phase2State, /mode: "structure"/);
  }],
  ["Impact to Structure preserves a valid selected Company as a Structure node", () => {
    assert.match(networkPage, /function selectedStructureNodeFromImpact/);
    assert.match(networkPage, /const canonicalCompanyId = companyIdByName\[selectedImpactCompany\.company\]/);
    assert.match(networkPage, /structureFixture\.nodes\.some\(\(node\) => node\.id === canonicalCompanyId\)/);
    assert.match(networkPage, /const preservedSelectionId = selectedStructureNodeFromImpact\(investigation\)/);
    assert.match(networkPage, /selectedObjectId: preservedSelectionId/);
    assert.match(companyData, /companyId: "demo-nvidia"/);
  }],
  ["Impact to Structure clears an invalid Impact-only selected entity", () => {
    assert.match(networkPage, /if \(!selectedImpactCompany \|\| !structureFixture\) return undefined/);
    assert.match(networkPage, /if \(!canonicalCompanyId\) return undefined/);
    assert.match(networkPage, /investigation\.selectedObjectId && !preservedSelectionId\) onClearInspector\(\)/);
  }],
  ["Clear Highlight cannot leave a stale Inspector selection", () => {
    assert.match(networkPage, /const clearHighlight = \(\) => \{[\s\S]*?selectedObjectId: undefined,[\s\S]*?if \(hadPrimarySelection\) onClearInspector\(\)/);
    assert.match(networkPage, /onClick=\{clearHighlight\}>Clear Highlight/);
  }],
  ["Impact visibility filtering clears hidden selected targets and Inspector", () => {
    assert.match(networkPage, /const selectedCompanyVisible = selectedCompany[\s\S]*?visibleCompanies\.some/);
    assert.match(networkPage, /if \(!selectedCompany \|\| selectedCompanyVisible\) return;/);
    assert.match(networkPage, /selectedObjectId: undefined, highlightedPath: undefined/);
    assert.match(networkPage, /onClearInspector\(\)/);
  }],
  ["Impact filtering preserves selection while the selected target remains visible", () => {
    assert.match(networkPage, /if \(!selectedCompany \|\| selectedCompanyVisible\) return;/);
    assert.doesNotMatch(networkPage, /if \(selectedCompanyVisible\)[\s\S]*?selectedObjectId: undefined/);
  }],
  ["Demo Facility resolves canonically as a Facility", () => {
    assert.match(eventData, /name: "Demo Facility", type: "Facility"/);
    assert.match(eventData, /id: "demo-facility-1"/);
    assert.match(eventsPage, /type: entity\.type/);
  }],
  ["Events no longer use a generic non-company to Industry fallback", () => {
    assert.doesNotMatch(eventsPage, /type:\s*company\s*\?\s*"Company"\s*:\s*"Industry"/);
    assert.match(eventData, /type: "Industry"/);
  }],
  ["Event filters clear a selected event that is no longer visible", () => {
    assert.match(eventsPage, /const selectedEventVisible = selectedEvent \? filteredEvents\.some/);
    assert.match(eventsPage, /if \(!selectedEventId \|\| !selectedEvent \|\| selectedEventVisible\) return;/);
    assert.match(eventsPage, /onSelectEvent\(null\)/);
    assert.match(eventsPage, /Select an event to inspect\./);
  }],
  ["Event filters preserve a selected event that remains visible", () => {
    assert.match(eventsPage, /const activeEvent = selectedEventVisible \? selectedEvent : undefined/);
    assert.match(eventsPage, /event\.id === activeEvent\?\.id/);
  }],
  ["Company exposure records carry canonical Event IDs", () => {
    assert.match(companyData, /eventId: string/);
    assert.match(companyData, /id: "demo-exposure-001",[\s\S]*?eventId: "demo-event-001"/);
    assert.match(companyData, /id: "demo-exposure-002",[\s\S]*?eventId: "demo-event-002"/);
  }],
  ["FACILITY_OUTAGE exposure resolves the canonical FACILITY_OUTAGE Event", () => {
    assert.match(companyData, /eventId: "demo-event-001",[\s\S]*?eventType: "FACILITY_OUTAGE"/);
    assert.match(eventData, /id: "demo-event-001",[\s\S]*?type: "FACILITY_OUTAGE"/);
  }],
  ["SUPPLY_DISRUPTION exposure resolves the canonical SUPPLY_DISRUPTION Event", () => {
    assert.match(companyData, /eventId: "demo-event-002",[\s\S]*?eventType: "SUPPLY_DISRUPTION"/);
    assert.match(eventData, /id: "demo-event-002",[\s\S]*?type: "SUPPLY_DISRUPTION"/);
  }],
  ["Exposure record IDs are never passed to Event navigation from Company Profile", () => {
    assert.match(companiesPage, /id: exposure\.eventId,[\s\S]*?type: "Event"/);
    assert.doesNotMatch(companiesPage, /id: exposure\.id,[\s\S]*?type: "Event"/);
    assert.match(companiesPage, /Exposure record/);
  }],
  ["Invalid explicit Event IDs never silently fall back to another Event", () => {
    assert.match(eventsPage, /Event data is not available for this development event\./);
    assert.match(eventsPage, /No unrelated Event is substituted\./);
    assert.doesNotMatch(eventsPage, /eventsDemo\.find\([\s\S]*?\?\?\s*filteredEvents\[0\]/);
    assert.doesNotMatch(eventsPage, /filteredEvents\[0\]\s*\?\?\s*eventsDemo\[0\]/);
  }],
];

for (const [name, check] of checks) {
  check();
  console.log(`PASS: ${name}`);
}

console.log(`\n${checks.length} Phase 2 integrity checks passed.`);
