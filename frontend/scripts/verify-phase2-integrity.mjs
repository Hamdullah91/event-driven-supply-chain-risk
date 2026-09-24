import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(fileURLToPath(new URL(path, root)), "utf8");

const impactData = read("src/data/networkImpactDemo.ts");
const structureData = read("src/data/networkStructureDemo.ts");
const companyData = read("src/data/companiesDemo.ts");
const companiesPage = read("src/pages/CompaniesPage.tsx");
const intelligencePage = read("src/pages/IntelligencePage.tsx");
const networkPage = read("src/pages/NetworkPage.tsx");
const networkCss = read("src/pages/NetworkPhase2.css");
const phase2State = read("src/phase2.ts");
const app = read("src/App.tsx");
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
    assert.match(networkPage, /const setMode = \(mode:[\s\S]*?onInvestigationChange\(\{[\s\S]*?\.\.\.investigation,[\s\S]*?mode,/);
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
];

for (const [name, check] of checks) {
  check();
  console.log(`PASS: ${name}`);
}

console.log(`\n${checks.length} Phase 2 integrity checks passed.`);
