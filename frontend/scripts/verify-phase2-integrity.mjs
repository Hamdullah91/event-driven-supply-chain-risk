import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(fileURLToPath(new URL(path, root)), "utf8");

const impactData = read("src/data/networkImpactDemo.ts");
const companyData = read("src/data/companiesDemo.ts");
const companiesPage = read("src/pages/CompaniesPage.tsx");
const networkPage = read("src/pages/NetworkPage.tsx");
const app = read("src/App.tsx");
const appShell = read("src/components/layout/AppShell.tsx");
const appShellCss = read("src/components/layout/AppShell.css");

const checks = [
  ["impact fixtures are keyed to explicit supported origins", () => {
    assert.match(impactData, /"Company:demo-tsmc"/);
    assert.match(impactData, /"Event:demo-event-001"/);
    assert.doesNotMatch(networkPage, /pathForCompany/);
  }],
  ["unsupported impact origins render an honest unavailable state", () => {
    assert.match(networkPage, /Impact data is not available for this development origin\./);
    assert.match(networkPage, /No TSMC path or other origin is substituted\./);
  }],
  ["impact without a valid origin renders no-context guidance", () => {
    assert.match(networkPage, /Select an event or origin company to analyze propagation\./);
    assert.match(networkPage, /does not render risk rings or paths without a valid origin context/);
  }],
  ["company exposure fixtures do not leak NVIDIA paths to other companies", () => {
    assert.match(companyData, /companyExposureFixtures/);
    assert.match(companyData, /"demo-nvidia": demoNvidiaExposures/);
    assert.doesNotMatch(companiesPage, /demoNvidiaExposures\.slice/);
    assert.match(companiesPage, /No development exposure fixture is available for this company\./);
  }],
  ["Network Focus\/Search is interactive", () => {
    assert.match(networkPage, /aria-label="Focus Network"/);
    assert.match(networkPage, /selectFocus\(node\)/);
    assert.match(networkPage, /network-focus-results/);
  }],
  ["Intelligence Show Network replaces stale focus identity", () => {
    assert.match(app, /const focusNode = networkStructureDemoNodes\.find/);
    assert.match(app, /focusId: focusNode\?\.id/);
    assert.match(app, /focusName: path\[0\]/);
  }],
  ["~1024px keeps Search and Inspector accessible", () => {
    assert.match(appShellCss, /@media \(max-width: 1024px\)/);
    assert.match(appShellCss, /\.global-search \{ display: flex;/);
    assert.match(appShellCss, /\.entity-inspector \{[\s\S]*?position: fixed;/);
    assert.doesNotMatch(appShellCss, /\.entity-inspector \{ display: none;/);
  }],
  ["dead graph canvas controls and incorrect listbox semantics are absent", () => {
    assert.doesNotMatch(networkPage, /aria-label="Center graph"/);
    assert.doesNotMatch(networkPage, /aria-label="Expand graph canvas"/);
    assert.doesNotMatch(appShell, /role="listbox"/);
  }],
];

for (const [name, check] of checks) {
  check();
  console.log(`PASS: ${name}`);
}

console.log(`\n${checks.length} Phase 2 integrity checks passed.`);
