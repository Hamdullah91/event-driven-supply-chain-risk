export type DemoGraphNodeType =
  | "Company"
  | "Facility"
  | "Material"
  | "Product"
  | "Technology"
  | "Country";

export type DemoGraphNode = {
  id: string;
  label: string;
  type: DemoGraphNodeType;
  x: number;
  y: number;
};

export type DemoGraphRelationship = {
  id: string;
  source: string;
  target: string;
  type:
    | "SUPPLIES"
    | "OPERATES"
    | "USES"
    | "PRODUCES"
    | "LOCATED_IN";
};

export type DemoStructureFixture = {
  focusId: string;
  nodes: DemoGraphNode[];
  relationships: DemoGraphRelationship[];
};

type EntityDefinition = Omit<DemoGraphNode, "x" | "y">;

const entityCatalog: Record<string, EntityDefinition> = {
  "demo-asml": { id: "demo-asml", label: "ASML", type: "Company" },
  "demo-tsmc": { id: "demo-tsmc", label: "TSMC", type: "Company" },
  "demo-nvidia": { id: "demo-nvidia", label: "NVIDIA", type: "Company" },
  "demo-samsung": { id: "demo-samsung", label: "Samsung Electronics", type: "Company" },
  "demo-facility-1": { id: "demo-facility-1", label: "Demo Fab", type: "Facility" },
  "demo-material-1": { id: "demo-material-1", label: "Silicon", type: "Material" },
  "demo-product-1": { id: "demo-product-1", label: "GPU", type: "Product" },
};

export const networkFocusEntities: EntityDefinition[] = [
  entityCatalog["demo-tsmc"],
  entityCatalog["demo-nvidia"],
  entityCatalog["demo-asml"],
  entityCatalog["demo-samsung"],
  entityCatalog["demo-facility-1"],
  entityCatalog["demo-material-1"],
  entityCatalog["demo-product-1"],
];

export const networkStructureDemoRelationships: DemoGraphRelationship[] = [
  { id: "demo-rel-1", source: "demo-asml", target: "demo-tsmc", type: "SUPPLIES" },
  { id: "demo-rel-2", source: "demo-tsmc", target: "demo-nvidia", type: "SUPPLIES" },
  { id: "demo-rel-3", source: "demo-tsmc", target: "demo-facility-1", type: "OPERATES" },
  { id: "demo-rel-4", source: "demo-nvidia", target: "demo-material-1", type: "USES" },
  { id: "demo-rel-5", source: "demo-nvidia", target: "demo-product-1", type: "PRODUCES" },
];

function nodesFromLayout(layout: Record<string, [number, number]>): DemoGraphNode[] {
  return Object.entries(layout).map(([id, [x, y]]) => ({ ...entityCatalog[id], x, y }));
}

const tsmcFixture: DemoStructureFixture = {
  focusId: "demo-tsmc",
  nodes: nodesFromLayout({
    "demo-asml": [23, 28],
    "demo-tsmc": [50, 26],
    "demo-nvidia": [50, 53],
    "demo-facility-1": [25, 66],
    "demo-material-1": [38, 82],
    "demo-product-1": [64, 82],
  }),
  relationships: networkStructureDemoRelationships,
};

const nvidiaFixture: DemoStructureFixture = {
  focusId: "demo-nvidia",
  nodes: nodesFromLayout({
    "demo-asml": [18, 20],
    "demo-tsmc": [50, 22],
    "demo-nvidia": [50, 49],
    "demo-facility-1": [24, 58],
    "demo-material-1": [35, 78],
    "demo-product-1": [65, 78],
  }),
  relationships: networkStructureDemoRelationships,
};

const asmlFixture: DemoStructureFixture = {
  focusId: "demo-asml",
  nodes: nodesFromLayout({
    "demo-asml": [50, 24],
    "demo-tsmc": [50, 50],
    "demo-nvidia": [70, 75],
    "demo-facility-1": [30, 75],
    "demo-material-1": [62, 90],
    "demo-product-1": [82, 88],
  }),
  relationships: networkStructureDemoRelationships,
};

const facilityFixture: DemoStructureFixture = {
  focusId: "demo-facility-1",
  nodes: nodesFromLayout({
    "demo-asml": [18, 20],
    "demo-tsmc": [50, 26],
    "demo-nvidia": [76, 24],
    "demo-facility-1": [50, 58],
    "demo-material-1": [68, 80],
    "demo-product-1": [86, 61],
  }),
  relationships: networkStructureDemoRelationships,
};

const materialFixture: DemoStructureFixture = {
  focusId: "demo-material-1",
  nodes: nodesFromLayout({
    "demo-asml": [16, 18],
    "demo-tsmc": [30, 30],
    "demo-nvidia": [50, 43],
    "demo-facility-1": [28, 67],
    "demo-material-1": [50, 72],
    "demo-product-1": [76, 72],
  }),
  relationships: networkStructureDemoRelationships,
};

const productFixture: DemoStructureFixture = {
  focusId: "demo-product-1",
  nodes: nodesFromLayout({
    "demo-asml": [15, 18],
    "demo-tsmc": [30, 30],
    "demo-nvidia": [50, 43],
    "demo-facility-1": [28, 67],
    "demo-material-1": [74, 72],
    "demo-product-1": [50, 72],
  }),
  relationships: networkStructureDemoRelationships,
};

export const structureFixturesByFocusId: Record<string, DemoStructureFixture> = {
  "demo-tsmc": tsmcFixture,
  "demo-nvidia": nvidiaFixture,
  "demo-asml": asmlFixture,
  "demo-facility-1": facilityFixture,
  "demo-material-1": materialFixture,
  "demo-product-1": productFixture,
};

export function getStructureFixture(focusId: string | null | undefined): DemoStructureFixture | undefined {
  if (!focusId) return undefined;
  return structureFixturesByFocusId[focusId];
}

export function getNetworkFocusEntity(focusId: string | null | undefined): EntityDefinition | undefined {
  if (!focusId) return undefined;
  return entityCatalog[focusId];
}

export const networkStructureDemoNodes: DemoGraphNode[] = networkFocusEntities
  .filter((entity) => entity.id !== "demo-samsung")
  .map((entity) => {
    const positioned = tsmcFixture.nodes.find((node) => node.id === entity.id);
    return positioned ?? { ...entity, x: 50, y: 50 };
  });
