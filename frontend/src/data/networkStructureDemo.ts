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

export const networkStructureDemoNodes: DemoGraphNode[] = [
  {
    id: "demo-company-asml",
    label: "ASML",
    type: "Company",
    x: 17,
    y: 24,
  },
  {
    id: "demo-company-tsmc",
    label: "TSMC",
    type: "Company",
    x: 46,
    y: 40,
  },
  {
    id: "demo-company-nvidia",
    label: "NVIDIA",
    type: "Company",
    x: 76,
    y: 28,
  },
  {
    id: "demo-facility-1",
    label: "Demo Fab",
    type: "Facility",
    x: 36,
    y: 72,
  },
  {
    id: "demo-material-1",
    label: "Silicon",
    type: "Material",
    x: 67,
    y: 72,
  },
  {
    id: "demo-product-1",
    label: "GPU",
    type: "Product",
    x: 86,
    y: 57,
  },
];

export const networkStructureDemoRelationships: DemoGraphRelationship[] = [
  {
    id: "demo-rel-1",
    source: "demo-company-asml",
    target: "demo-company-tsmc",
    type: "SUPPLIES",
  },
  {
    id: "demo-rel-2",
    source: "demo-company-tsmc",
    target: "demo-company-nvidia",
    type: "SUPPLIES",
  },
  {
    id: "demo-rel-3",
    source: "demo-company-tsmc",
    target: "demo-facility-1",
    type: "OPERATES",
  },
  {
    id: "demo-rel-4",
    source: "demo-company-nvidia",
    target: "demo-material-1",
    type: "USES",
  },
  {
    id: "demo-rel-5",
    source: "demo-company-nvidia",
    target: "demo-product-1",
    type: "PRODUCES",
  },
];