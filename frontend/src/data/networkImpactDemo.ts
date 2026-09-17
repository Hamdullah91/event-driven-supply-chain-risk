export type ImpactNode = {
  id: string;
  label: string;
  hop: 0 | 1 | 2 | 3;
  transmissionFactor: number;
  x: number;
  y: number;
};

export const impactOrigin = {
  companyId: "demo-company-tsmc",
  companyName: "TSMC",
};

export const networkImpactDemoNodes: ImpactNode[] = [
  {
    id: "demo-company-tsmc",
    label: "TSMC",
    hop: 0,
    transmissionFactor: 1,
    x: 50,
    y: 50,
  },
  {
    id: "demo-company-nvidia",
    label: "NVIDIA",
    hop: 1,
    transmissionFactor: 1,
    x: 33,
    y: 31,
  },
  {
    id: "demo-company-amd",
    label: "AMD",
    hop: 1,
    transmissionFactor: 0.92,
    x: 67,
    y: 31,
  },
  {
    id: "demo-company-a",
    label: "Demo Supplier A",
    hop: 2,
    transmissionFactor: 0.7,
    x: 22,
    y: 72,
  },
  {
    id: "demo-company-b",
    label: "Demo Supplier B",
    hop: 2,
    transmissionFactor: 0.63,
    x: 78,
    y: 72,
  },
  {
    id: "demo-company-c",
    label: "Demo Company C",
    hop: 3,
    transmissionFactor: 0.49,
    x: 50,
    y: 88,
  },
];