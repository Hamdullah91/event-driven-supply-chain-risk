export type IntelligenceEvidence = {
  id: string;
  source: string;
  document: string;
  confidence: string;
  extractedContext: string;
};

export type IntelligenceEntity = {
  id: string;
  name: string;
  type: string;
};

export const intelligenceDemo = {
  question: "Why is NVIDIA exposed to a disruption affecting TSMC?",

  answer:
    "The development graph indicates that NVIDIA is exposed because its supply-chain path includes a direct downstream dependency from TSMC. A disruption affecting TSMC can therefore propagate to NVIDIA through the SUPPLIES relationship. The example exposure is one hop from the affected company and is associated with the demonstrated risk path.",

  path: ["TSMC", "NVIDIA"],

  relationship: "SUPPLIES",

  entities: [
    {
      id: "demo-tsmc",
      name: "TSMC",
      type: "Company",
    },
    {
      id: "demo-nvidia",
      name: "NVIDIA",
      type: "Company",
    },
  ] satisfies IntelligenceEntity[],

  risk: {
    hopDistance: 1,
    initialRisk: "0.75",
    pathDependency: "1.00",
    distanceDecay: "1.00",
    propagatedRisk: "0.75",
  },

  evidence: [
    {
      id: "evidence-demo-001",
      source: "Development source",
      document: "Demo supply-chain disclosure",
      confidence: "0.91",
      extractedContext: "Not available",
    },
  ] satisfies IntelligenceEvidence[],
};